"""
社区服务模块 - Flask-SQLAlchemy版本
处理社区相关的核心业务逻辑
"""

import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from typing import Dict
from sqlalchemy import select, func, delete, and_, or_, not_
from database.flask_models import db, User, Community, CommunityApplication, UserAuditLog
from wxcloudrun.utils.validators import generate_phone_hash
from const_default import DEFAULT_COMMUNITY_NAME,DEFAULT_COMMUNITY_ID,DEFAULT_BLACK_ROOM_NAME,DEFAULT_BLACK_ROOM_ID
from app.shared.utils.transaction import transactional

logger = logging.getLogger('CommunityService')


class CommunityService:
    """社区服务类"""

    @staticmethod
    @transactional
    def assign_user_to_community(user, community_name):
        """将用户分配到社区"""
        if not community_name:
            raise ValueError("社区名称不能为空")

        stmt = select(Community).where(Community.name == community_name)
        community = db.session.execute(stmt).scalar_one_or_none()
        if not community:
            raise ValueError(f"社区不存在: {community_name}")

        # 更新用户的社区ID
        user.community_id = community.community_id
        db.session.merge(user)

        logger.info(f"用户 {user.user_id} 已分配到社区 {community.community_id}")
        return community

    @staticmethod
    def query_community_by_id(comm_id):
        """根据ID查询社区"""
        stmt = select(Community).where(Community.community_id == comm_id)
        existing = db.session.execute(stmt).scalar_one_or_none()
        return existing

    @staticmethod
    def query_community_by_name(comm_name):
        """根据名称查询社区"""
        stmt = select(Community).where(Community.name == comm_name)
        existing = db.session.execute(stmt).scalar_one_or_none()
        return existing

    @staticmethod
    @transactional
    def create_community(name, description, creator_id, location=None, settings=None, manager_id=None, location_lat=None, location_lon=None):
        """创建新社区"""
        # 检查社区名称是否已存在
        stmt = select(Community).where(Community.name == name)
        existing = db.session.execute(stmt).scalar_one_or_none()
        if existing:
            raise ValueError(f"社区名称已存在: {name}")

        # 处理 settings 字段：如果是字典，转换为 JSON 字符串
        settings_json = None
        if settings is not None:
            if isinstance(settings, dict):
                settings_json = json.dumps(settings)
            else:
                settings_json = settings

        # 创建社区
        community = Community(
            name=name,
            description=description,
            creator_id=creator_id,
            location=location,
            settings=settings_json,
            manager_id=manager_id,
            location_lat=location_lat,
            location_lon=location_lon,
            status=1,
            created_at=datetime.now()
        )

        db.session.add(community)
        db.session.flush()  # 刷新以获取数据库生成的ID

        logger.info(f"创建社区成功: {community.community_id}")
        return community

    @staticmethod
    def create_community_application(user_id, community_id, reason=None):
        """
        创建社区申请

        Args:
            user_id: 用户ID
            community_id: 社区ID
            reason: 申请理由

        Returns:
            CommunityApplication: 创建的申请对象

        Raises:
            ValueError: 当用户或社区不存在，或用户已在社区时
        """
        # 检查用户是否存在
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        # 检查用户是否已在社区
        if user.community_id == community_id:
            raise ValueError("用户已在社区")

        # 检查是否已有待审核的申请
        stmt_app = select(CommunityApplication).where(
            CommunityApplication.user_id == user_id,
            CommunityApplication.target_community_id == community_id,
            CommunityApplication.status == 1  # 待审核状态
        )
        existing_application = db.session.execute(stmt_app).scalar_one_or_none()

        if existing_application:
            raise ValueError("已有待审核的申请")

        # 创建申请
        application = CommunityApplication(
            user_id=user_id,
            target_community_id=community_id,
            status=1,  # 待审核
            reason=reason
        )

        db.session.add(application)
        db.session.commit()
        db.session.refresh(application)

        logger.info(f"创建社区申请成功: application_id={application.application_id}, user_id={user_id}, community_id={community_id}")
        return application

    @staticmethod
    def get_community_applications(user_id, page=1, per_page=20, status_filter=None):
        """
        获取社区申请列表

        Args:
            user_id: 用户ID
            page: 页码
            per_page: 每页数量
            status_filter: 状态过滤（可选）

        Returns:
            dict: 包含申请列表和分页信息的字典
        """
        from sqlalchemy.orm import joinedload

        # 检查用户是否存在
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 构建查询
        stmt = select(CommunityApplication).options(
            joinedload(CommunityApplication.target_community),
            joinedload(CommunityApplication.user)
        )

        # 如果用户不是超级管理员，只显示其社区的申请
        if user.role != 4:
            # 获取用户管理的社区
            from database.flask_models import CommunityStaff
            stmt_staff = select(CommunityStaff.community_id).where(CommunityStaff.user_id == user_id)
            managed_community_ids = db.session.execute(stmt_staff).scalars().all()

            if not managed_community_ids:
                return {
                    'applications': [],
                    'total': 0,
                    'page': page,
                    'per_page': per_page
                }

            stmt = stmt.where(CommunityApplication.target_community_id.in_(managed_community_ids))

        # 应用状态过滤
        if status_filter is not None:
            try:
                status = int(status_filter)
                stmt = stmt.where(CommunityApplication.status == status)
            except ValueError:
                pass

        # 分页
        # 计算总数
        stmt_count = select(func.count()).select_from(CommunityApplication)
        if user.role != 4:
            stmt_count = stmt_count.where(CommunityApplication.target_community_id.in_(managed_community_ids))
        if status_filter is not None:
            stmt_count = stmt_count.where(CommunityApplication.status == status)
        total = db.session.execute(stmt_count).scalar()

        # 分页查询
        stmt = stmt.order_by(CommunityApplication.created_at.desc()).offset((page - 1) * per_page).limit(per_page)
        applications = db.session.execute(stmt).scalars().all()

        logger.info(f"获取社区申请列表成功: user_id={user_id}, total={total}")
        return {
            'applications': applications,
            'total': total,
            'page': page,
            'per_page': per_page
        }

    @staticmethod
    def process_application(application_id, approve, processor_id, rejection_reason=None):
        """处理社区申请"""
        application = db.session.get(CommunityApplication, application_id)
        if not application:
            raise ValueError("申请不存在")

        if application.status != 1:  # 不是待审核状态
            raise ValueError("申请已被处理")

        if approve:
            # 批准申请
            application.status = 2  # 已批准
            application.processed_by = processor_id
            application.updated_at = datetime.now()

            # 将用户加入社区
            user = db.session.get(User, application.user_id)
            user.community_id = application.target_community_id

            # 同步社区打卡规则到用户
            from wxcloudrun.community_staff_service import CommunityStaffService
            CommunityStaffService._activate_new_community_rules(application.user_id, application.target_community_id)

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=processor_id,
                action="approve_community_application",
                detail=f"批准社区申请: 申请ID={application_id}, 用户ID={application.user_id}"
            )
            db.session.add(audit_log)

            logger.info(f"社区申请批准: 申请ID={application_id}")
        else:
            # 拒绝申请
            if not rejection_reason:
                raise ValueError("拒绝申请必须提供理由")

            application.status = 3  # 已拒绝
            application.rejection_reason = rejection_reason
            application.processed_by = processor_id
            application.updated_at = datetime.now()

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=processor_id,
                action="reject_community_application",
                detail=f"拒绝社区申请: 申请ID={application_id}, 理由={rejection_reason}"
            )
            db.session.add(audit_log)

            logger.info(f"社区申请拒绝: 申请ID={application_id}, 理由={rejection_reason}")

        db.session.commit()
        return application

    @staticmethod
    def search_community_users(community_id, keyword=None, page=1, per_page=20):
        """搜索社区用户（非管理员）"""
        stmt = select(User).where(User.community_id == community_id)

        # 排除社区工作人员
        from database.flask_models import CommunityStaff
        stmt_staff = select(CommunityStaff.user_id).where(CommunityStaff.community_id == community_id)
        staff_user_ids = [s[0] for s in db.session.execute(stmt_staff).scalars().all()]
        if staff_user_ids:
            from sqlalchemy import not_
            stmt = stmt.where(not_(User.user_id.in_(staff_user_ids)))

        if keyword:
            # 判断是电话号码还是昵称
            if keyword.isdigit() and len(keyword) >= 7:
                # 电话号码精确搜索
                phone_hash = generate_phone_hash(keyword)
                stmt = stmt.where(User.phone_hash == phone_hash)
            else:
                # 昵称模糊搜索
                stmt = stmt.where(User.nickname.like(f"%{keyword}%"))

        # 分页 - 使用offset和limit实现
        # 计算总数
        stmt_count = select(func.count()).select_from(User).where(User.community_id == community_id)
        if staff_user_ids:
            stmt_count = stmt_count.where(not_(User.user_id.in_(staff_user_ids)))
        if keyword:
            if keyword.isdigit() and len(keyword) >= 7:
                stmt_count = stmt_count.where(User.phone_hash == phone_hash)
            else:
                stmt_count = stmt_count.where(User.nickname.like(f"%{keyword}%"))
        total = db.session.execute(stmt_count).scalar()

        offset = (page - 1) * per_page
        stmt = stmt.offset(offset).limit(per_page)
        users = db.session.execute(stmt).scalars().all()

        # 在会话关闭前将User对象转换为字典，避免会话分离问题
        user_dicts = [CommunityService._user_to_dict(user) for user in users]

        # 创建类似paginate对象的数据结构
        class Pagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0

        return Pagination(user_dicts, page, per_page, total)

    @staticmethod
    def get_available_communities():
        """获取可申请的社区列表（排除默认社区）"""
        stmt = select(Community).where(
            Community.status == 1,  # 启用状态
            Community.is_default == False  # 非默认社区
        )
        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def get_community_by_id(community_id):
        """根据ID获取社区"""
        return db.session.get(Community, community_id)

    @staticmethod
    def _community_to_dict(community):
        """将Community对象转换为字典，避免会话分离问题"""
        return {
            'community_id': community.community_id,
            'name': community.name,
            'description': community.description or '',
            'status': community.status,
            'location': community.location or '',
            'is_default': community.is_default,
            'is_blackhouse': community.is_blackhouse,
            'creator_id': community.creator_id,
            'created_at': community.created_at,
            'updated_at': community.updated_at
        }

    @staticmethod
    def _user_to_dict(user):
        """将User对象转换为字典，避免会话分离问题"""
        return {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'avatar_url': user.avatar_url,
            'phone_number': user.phone_number,
            'role': user.role,
            'role_name': user.role_name,
            'verification_status': user.verification_status,
            'created_at': user.created_at
        }

    @staticmethod
    def update_community_info(community_id, name=None, description=None, location=None, status=None, manager_id=None, location_lat=None, location_lon=None):
        """更新社区信息"""
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        # 更新字段
        if name is not None:
            # 检查名称是否与其他社区重复
            stmt = select(Community).where(
                Community.name == name,
                Community.community_id != community_id
            )
            existing = db.session.execute(stmt).scalar_one_or_none()
            if existing:
                raise ValueError("社区名称已存在")
            community.name = name

        if description is not None:
            community.description = description

        if location is not None:
            community.location = location

        if location_lat is not None:
            community.location_lat = location_lat

        if location_lon is not None:
            community.location_lon = location_lon

        if status is not None:
            community.status = status

        if manager_id is not None:
            # 更新社区主管
            community.manager_id = manager_id

        # 更新时间
        community.updated_at = datetime.now()

        db.session.commit()
        return community

    @staticmethod
    def update_community(community_id, params, user_id):
        """
        更新社区信息（适配器方法，用于路由调用）

        Args:
            community_id: 社区ID
            params: 更新参数字典
            user_id: 操作用户ID（用于审计）

        Returns:
            bool: 更新是否成功
        """
        try:
            # 从params中提取字段
            name = params.get('name')
            description = params.get('description')
            location = params.get('location')
            status = params.get('status')
            manager_id = params.get('manager_id')
            location_lat = params.get('location_lat')
            location_lon = params.get('location_lon')

            # 调用现有的update_community_info方法
            community = CommunityService.update_community_info(
                community_id=community_id,
                name=name,
                description=description,
                location=location,
                status=status,
                manager_id=manager_id,
                location_lat=location_lat,
                location_lon=location_lon
            )

            return community is not None

        except Exception as e:
            logger.error(f"更新社区失败: {str(e)}")
            return False

    @staticmethod
    def get_community_members(community_id, page=1, page_size=20):
        """获取社区成员列表（只返回普通成员，不包括工作人员）"""
        from database.flask_models import CheckinRecord, CommunityStaff
        from datetime import date

        # 获取该社区所有工作人员的用户ID列表
        stmt_staff = select(CommunityStaff).where(CommunityStaff.community_id == community_id)
        staff_user_ids = [s.user_id for s in db.session.execute(stmt_staff).scalars().all()]

        # 分页查询社区成员 - 使用User表查询，排除工作人员
        offset = (page - 1) * page_size
        stmt = select(User).where(User.community_id == community_id)

        # 排除工作人员
        if staff_user_ids:
            from sqlalchemy import not_
            stmt = stmt.where(not_(User.user_id.in_(staff_user_ids)))

        # 计算总数
        stmt_count = select(func.count()).select_from(User).where(User.community_id == community_id)
        if staff_user_ids:
            stmt_count = stmt_count.where(not_(User.user_id.in_(staff_user_ids)))
        total = db.session.execute(stmt_count).scalar()

        # 分页查询
        stmt = stmt.order_by(User.community_joined_at.desc()).offset(offset).limit(page_size)
        members = db.session.execute(stmt).scalars().all()

        # 格式化响应数据
        members_data = []
        today = date.today()

        for member_user in members:
            if not member_user:
                continue

            # 获取今日未完成打卡数和详情
            from sqlalchemy import and_, func
            stmt_records = select(CheckinRecord).where(
                and_(
                    CheckinRecord.user_id == member_user.user_id,
                    func.date(CheckinRecord.planned_time) == today,
                    CheckinRecord.status == 0  # 0-missed(未打卡)
                )
            )
            unchecked_records = db.session.execute(stmt_records).scalars().all()

            unchecked_items = []
            for record in unchecked_records:
                if record.rule:
                    unchecked_items.append({
                        'rule_id': str(record.rule_id),
                        'rule_name': record.rule.rule_name,
                        'planned_time': record.rule.planned_time.strftime('%H:%M:%S') if record.rule.planned_time else None
                    })

            user_data = {
                'user_id': str(member_user.user_id),
                'nickname': member_user.nickname,
                'avatar_url': member_user.avatar_url,
                'phone_number': member_user.phone_number,
                'join_time': member_user.community_joined_at.isoformat() if member_user.community_joined_at else None,
                'unchecked_count': len(unchecked_items),
                'unchecked_items': unchecked_items
            }

            members_data.append(user_data)

        return members_data, total

    @staticmethod
    def add_users_to_community(community_id, user_ids, operator_id=None):
        """批量添加用户到社区"""
        from datetime import datetime

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        added_count = 0
        failed = []

        for user_id in user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.get(User, user_id)
                if not target_user:
                    failed.append({'user_id': user_id, 'reason': '用户不存在'})
                    continue

                # 检查是否已在社区
                if target_user.community_id == community_id:
                    failed.append({'user_id': user_id, 'reason': '用户已在社区'})
                    continue

                # 更新用户社区信息
                target_user.community_id = community_id
                target_user.community_joined_at = datetime.now()

                # 同步社区打卡规则到用户
                from wxcloudrun.community_staff_service import CommunityStaffService
                CommunityStaffService._activate_new_community_rules(user_id, community_id)

                added_count += 1

            except Exception as e:
                logger.error(f'添加用户失败 user_id={user_id}: {str(e)}')
                failed.append({'user_id': user_id, 'reason': str(e)})

        db.session.commit()

        if added_count == 0:
            raise ValueError({'added_count': added_count, 'failed': failed}, '添加失败')

        return {
            'added_count': added_count,
            'failed': failed
        }

    @staticmethod
    def remove_user_from_community(community_id, user_id):
        """从社区移除用户"""
        from database.flask_models import CommunityStaff

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        # 查找用户
        target_user = db.session.get(User, user_id)
        if not target_user:
            raise ValueError("用户不存在")

        # 特殊社区逻辑处理
        moved_to = None

        # 获取特殊社区ID
        stmt_anka = select(Community).where(Community.name == DEFAULT_COMMUNITY_NAME)
        anka_family = db.session.execute(stmt_anka).scalar_one_or_none()
        stmt_black = select(Community).where(Community.name == DEFAULT_BLACK_ROOM_NAME)
        blackhouse = db.session.execute(stmt_black).scalar_one_or_none()

        # 如果从"黑屋"社区移除，不能删除用户
        if community.name == DEFAULT_BLACK_ROOM_NAME:
            raise ValueError("不能从黑屋社区删除用户")

        # 如果从"安卡大家庭"移除,移入"黑屋"
        elif community.name == DEFAULT_COMMUNITY_NAME and blackhouse:
            # 对于安卡大家庭，不检查用户是否在该社区，直接移入黑屋
            # 检查是否已在黑屋
            if target_user.community_id != blackhouse.community_id:
                target_user.community_id = blackhouse.community_id
                target_user.community_joined_at = datetime.now()
                moved_to = DEFAULT_BLACK_ROOM_NAME

        # 如果从普通社区移除
        elif community.name not in [DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
            # 检查用户是否在该社区（普通社区需要这个检查）
            if target_user.community_id != community_id:
                raise ValueError("用户不在该社区")

            # 检查用户是否还属于其他普通社区
            from sqlalchemy import and_, not_
            stmt_count = select(func.count()).select_from(User).join(
                Community, User.community_id == Community.community_id
            ).where(
                and_(
                    User.user_id == user_id,
                    User.community_id != community_id,
                    User.community_id.isnot(None)
                )
            )
            stmt_count = stmt_count.where(not_(Community.name.in_([DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME])))
            other_communities_count = db.session.execute(stmt_count).scalar()

            # 如果不属于任何其他普通社区,移入"安卡大家庭"
            if other_communities_count == 0 and anka_family:
                # 检查是否已在安卡大家庭
                if target_user.community_id != anka_family.community_id:
                    target_user.community_id = anka_family.community_id
                    target_user.community_joined_at = datetime.now()
                    moved_to = DEFAULT_COMMUNITY_NAME
            else:
                # 如果用户属于其他普通社区，则清空社区信息
                target_user.community_id = None
                target_user.community_joined_at = None

        db.session.commit()

        return {'moved_to': moved_to}

    @staticmethod
    def delete_community(community_id):
        """删除社区"""
        from database.flask_models import CommunityStaff

        # 查找社区
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        # 特殊社区不能删除
        if community.name in [DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
            raise ValueError("特殊社区不能删除")

        # 检查社区状态
        if community.status == 1:
            raise ValueError("请先停用社区")

        # 检查社区内是否还有用户
        stmt_count = select(func.count()).select_from(User).where(User.community_id == community_id)
        member_count = db.session.execute(stmt_count).scalar()
        if member_count > 0:
            raise ValueError({
                'user_count': member_count
            }, '社区内还有用户，无法删除')

        # 删除相关数据
        stmt_staff = delete(CommunityStaff).where(CommunityStaff.community_id == community_id)
        db.session.execute(stmt_staff)
        stmt_app = delete(CommunityApplication).where(CommunityApplication.target_community_id == community_id)
        db.session.execute(stmt_app)

        # 删除社区
        db.session.delete(community)
        db.session.commit()

    @staticmethod
    def get_community_daily_stats(community_id):
        """获取社区每日打卡统计"""
        from database.flask_models import CheckinRecord, CommunityStaff, CommunityCheckinRule
        from datetime import date
        from sqlalchemy import and_, func

        # 获取该社区所有工作人员的用户ID列表
        stmt_staff = select(CommunityStaff).where(CommunityStaff.community_id == community_id)
        staff_user_ids = [s.user_id for s in db.session.execute(stmt_staff).scalars().all()]

        # 获取社区所有用户（排除工作人员）
        stmt_users = select(User).where(User.community_id == community_id)
        if staff_user_ids:
            from sqlalchemy import not_
            stmt_users = stmt_users.where(not_(User.user_id.in_(staff_user_ids)))
        all_users = db.session.execute(stmt_users).scalars().all()

        # 获取今日所有启用的社区打卡规则
        today = date.today()
        stmt_rules = select(CommunityCheckinRule).where(
            CommunityCheckinRule.community_id == community_id,
            CommunityCheckinRule.status == 1  # 启用状态
        )
        enabled_rules = db.session.execute(stmt_rules).scalars().all()

        if not enabled_rules or not all_users:
            # 如果没有规则或没有用户，返回默认值
            return {
                'user_count': len(all_users),
                'total_rules': len(enabled_rules),
                'total_checkins': 0,
                'completed_checkins': 0,
                'missed_checkins': 0,
                'checkin_rate': 0.0,
                'unchecked_user_count': 0
            }

        # 获取今日所有打卡记录
        rule_ids = [rule.community_rule_id for rule in enabled_rules]
        user_ids = [user.user_id for user in all_users]

        stmt_records = select(CheckinRecord).where(
            and_(
                CheckinRecord.user_id.in_(user_ids),
                CheckinRecord.community_rule_id.in_(rule_ids),
                func.date(CheckinRecord.planned_time) == today
            )
        )
        today_records = db.session.execute(stmt_records).scalars().all()

        # 统计数据
        total_checkins = len(today_records)
        completed_checkins = sum(1 for r in today_records if r.status == 1)  # 1-completed
        missed_checkins = sum(1 for r in today_records if r.status == 0)  # 0-missed

        # 计算打卡率（已打卡数 / 总打卡数）
        checkin_rate = (completed_checkins / total_checkins * 100) if total_checkins > 0 else 0.0

        # 计算未打卡人数（去重）
        unchecked_user_ids = set(r.user_id for r in today_records if r.status == 0)
        unchecked_user_count = len(unchecked_user_ids)

        return {
            'user_count': len(all_users),
            'total_rules': len(enabled_rules),
            'total_checkins': total_checkins,
            'completed_checkins': completed_checkins,
            'missed_checkins': missed_checkins,
            'checkin_rate': round(checkin_rate, 1),
            'unchecked_user_count': unchecked_user_count
        }

    @staticmethod
    def get_community_checkin_stats(community_id: int, days: int = 7) -> Dict:
        """
        获取社区打卡统计信息

        Args:
            community_id: 社区ID
            days: 统计天数，默认7天

        Returns:
            Dict: 包含每个规则的打卡统计数据
        """
        from database.flask_models import CheckinRecord, CommunityCheckinRule, User, CommunityStaff
        from datetime import date, timedelta
        from sqlalchemy import and_, func, case

        # Layer 1: 入口点验证 - 确保社区ID有效
        if not community_id or community_id <= 0:
            raise ValueError('社区ID必须为正整数')

        # Layer 4: 调试仪表 - 记录统计上下文
        logger.debug(f"获取社区打卡统计: community_id={community_id}, days={days}")

        # 计算日期范围
        end_date = date.today()
        start_date = end_date - timedelta(days=days - 1)
        date_range = [start_date + timedelta(days=i) for i in range(days)]

        # 获取该社区所有工作人员的用户ID列表（排除）
        stmt_staff = select(CommunityStaff).where(CommunityStaff.community_id == community_id)
        staff_user_ids = [s.user_id for s in db.session.execute(stmt_staff).scalars().all()]

        # Layer 2: 业务逻辑验证 - 获取启用的规则
        stmt_rules = select(CommunityCheckinRule).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1  # 启用状态
            )
        )
        enabled_rules = db.session.execute(stmt_rules).scalars().all()

        # Layer 4: 调试仪表 - 记录规则和用户数量
        logger.debug(f"社区 {community_id} 启用规则数: {len(enabled_rules)}")

        # 获取该社区所有普通用户（排除工作人员）
        stmt_users = select(User).where(User.community_id == community_id)
        if staff_user_ids:
            from sqlalchemy import not_
            stmt_users = stmt_users.where(not_(User.user_id.in_(staff_user_ids)))
        all_users = db.session.execute(stmt_users).scalars().all()

        logger.debug(f"社区 {community_id} 普通用户数: {len(all_users)}")

        # Layer 2: 业务逻辑验证 - 即使没有用户，也要返回正确的规则数
        # 修复：不再因为无用户而返回 total_rules=0
        if not all_users:
            # Layer 4: 调试仪表 - 记录无用户情况
            logger.info(f"社区 {community_id} 没有普通用户，返回空统计但保留规则数")
            return {
                'stats': [],
                'total_rules': len(enabled_rules)  # ✅ 修复：返回实际规则数
            }

        user_ids = [user.user_id for user in all_users]
        rule_ids = [rule.community_rule_id for rule in enabled_rules]

        # 获取指定日期范围内的所有打卡记录
        stmt_records = select(CheckinRecord).where(
            and_(
                CheckinRecord.user_id.in_(user_ids),
                CheckinRecord.community_rule_id.in_(rule_ids),
                func.date(CheckinRecord.planned_time) >= start_date,
                func.date(CheckinRecord.planned_time) <= end_date
            )
        )
        all_records = db.session.execute(stmt_records).scalars().all()

        # 构建统计数据
        stats = []
        rule_dict = {rule.community_rule_id: rule for rule in enabled_rules}

        for rule in enabled_rules:
            rule_id = rule.community_rule_id

            # 统计该规则每日未打卡人数
            daily_missed = []
            for check_date in date_range:
                # 查询该日期该规则的未打卡记录
                day_records = [r for r in all_records
                             if r.community_rule_id == rule_id
                             and r.planned_time.date() == check_date
                             and r.status == 0]  # 0-missed

                # 计算该日期应该打卡但未打卡的人数
                # 理论上每个用户每天应该打卡一次
                missed_count = len(day_records)
                daily_missed.append(missed_count)

            # 计算7天未打卡人次总和
            total_missed = sum(daily_missed)

            stats.append({
                'rule_id': rule_id,
                'rule_name': rule.rule_name,
                'rule_icon': rule.icon_url or '📝',
                'total_missed': total_missed,
                'daily_missed': daily_missed,
                'dates': [d.isoformat() for d in date_range]
            })

        # 按未打卡人次总和降序排序
        stats.sort(key=lambda x: x['total_missed'], reverse=True)

        return {
            'stats': stats,
            'total_rules': len(enabled_rules)
        }

    @staticmethod
    def toggle_community_status(community_id, status):
        """切换社区状态"""
        # 查找社区
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError("社区不存在")

        # 特殊社区不能停用
        if community.name in [DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
            raise ValueError("特殊社区不能停用")

        # 更新状态
        community.status = 1 if status == 'active' else 2
        db.session.commit()

        return {
            'community_id': community_id,
            'status': status
        }

    @staticmethod
    def search_users(keyword, community_id=None):
        """搜索用户"""
        from database.flask_models import CommunityStaff
        from sqlalchemy import or_

        # 搜索用户 (按昵称或手机号)
        stmt_users = select(User).where(
            or_(
                User.nickname.like(f'%{keyword}%'),
                User.phone_number.like(f'%{keyword}%')
            )
        ).limit(20)

        users = db.session.execute(stmt_users).scalars().all()

        # 格式化响应
        result = []
        for u in users:
            # 检查是否已是任何社区的工作人员
            stmt_staff = select(CommunityStaff).where(CommunityStaff.user_id == u.user_id)
            is_staff = db.session.execute(stmt_staff).scalar_one_or_none() is not None

            user_data = {
                'user_id': str(u.user_id),
                'nickname': u.nickname,
                'avatar_url': u.avatar_url,
                'phone_number': u.phone_number,
                'is_staff': is_staff
            }

            # 如果指定了community_id,检查是否已在该社区
            if community_id:
                already_in = u.community_id == community_id
                user_data['already_in_community'] = already_in

            result.append(user_data)

        return result

    @staticmethod
    def search_users_excluding_blackroom(keyword, page=1, per_page=20):
        """搜索用户（排除黑名单房间）"""
        from database.flask_models import CommunityStaff
        from sqlalchemy import or_

        # 获取黑名单房间ID
        stmt_black = select(Community).where(Community.name == DEFAULT_BLACK_ROOM_NAME)
        blackroom_community = db.session.execute(stmt_black).scalar_one_or_none()
        blackroom_community_id = blackroom_community.community_id if blackroom_community else None

        # 搜索用户 (按昵称或手机号)
        stmt_users = select(User).where(
            or_(
                User.nickname.like(f'%{keyword}%'),
                User.phone_number.like(f'%{keyword}%')
            )
        )

        # 排除黑名单房间的用户
        if blackroom_community_id:
            stmt_users = stmt_users.where(User.community_id != blackroom_community_id)

        # 分页
        stmt_count = select(func.count()).select_from(User)
        if blackroom_community_id:
            stmt_count = stmt_count.where(User.community_id != blackroom_community_id)
        stmt_count = stmt_count.where(or_(
            User.nickname.like(f'%{keyword}%'),
            User.phone_number.like(f'%{keyword}%')
        ))
        total = db.session.execute(stmt_count).scalar()

        offset = (page - 1) * per_page
        stmt_users = stmt_users.offset(offset).limit(per_page)
        users = db.session.execute(stmt_users).scalars().all()

        return {
            'users': users,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page if per_page > 0 else 0
        }

    @staticmethod
    def get_manageable_communities(user, page=1, per_page=7):
        """获取用户可管理的社区列表"""
        from database.flask_models import CommunityStaff
        from const_default import DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_ID

        if user.role == 4:  # 超级管理员
            stmt = select(Community).where(Community.status == 1)  # 只显示启用状态

            # 确保特殊社区（安卡大家庭和黑屋）包含在结果中
            # 获取特殊社区
            stmt_special = select(Community).where(
                Community.community_id.in_([DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_ID]),
                Community.status == 1
            )
            special_communities = db.session.execute(stmt_special).scalars().all()

            # 获取特殊社区ID列表
            special_community_ids = [c.community_id for c in special_communities]

            # 如果特殊社区没有被包含在正常查询中，需要确保它们出现在结果中
            all_communities = db.session.execute(stmt).scalars().all()
            existing_ids = [c.community_id for c in all_communities]

            # 添加缺失的特殊社区
            for special_community in special_communities:
                if special_community.community_id not in existing_ids:
                    all_communities.append(special_community)

            # 按创建时间排序
            all_communities.sort(key=lambda x: x.created_at, reverse=True)

            # 手动分页
            total = len(all_communities)
            offset = (page - 1) * per_page
            communities = all_communities[offset:offset + per_page]

            return communities, total
        else:
            # 获取用户作为工作人员的社区
            stmt_staff = select(CommunityStaff).where(CommunityStaff.user_id == user.user_id)
            staff_communities = db.session.execute(stmt_staff).scalars().all()
            community_ids = [sc.community_id for sc in staff_communities]

            if not community_ids:
                return [], 0

            stmt = select(Community).where(
                Community.community_id.in_(community_ids),
                Community.status == 1  # 启用状态
            )

            # 分页查询
            stmt_count = select(func.count()).select_from(Community).where(
                Community.community_id.in_(community_ids),
                Community.status == 1
            )
            total = db.session.execute(stmt_count).scalar()

            offset = (page - 1) * per_page
            stmt = stmt.order_by(Community.created_at.desc()).offset(offset).limit(per_page)
            communities = db.session.execute(stmt).scalars().all()

            return communities, total

    @staticmethod
    def search_communities_with_permission(user, keyword):
        """搜索社区（根据权限过滤）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            stmt = select(Community).where(
                Community.name.like(f'%{keyword}%'),
                Community.status == 1
            )
        else:
            # 获取用户有权限的社区
            stmt_staff = select(CommunityStaff).where(CommunityStaff.user_id == user.user_id)
            staff_communities = db.session.execute(stmt_staff).scalars().all()
            community_ids = [sc.community_id for sc in staff_communities]

            if not community_ids:
                return []

            stmt = select(Community).where(
                Community.community_id.in_(community_ids),
                Community.name.like(f'%{keyword}%'),
                Community.status == 1
            )

        stmt = stmt.limit(20)
        communities = db.session.execute(stmt).scalars().all()  # 限制搜索结果数量
        return communities

    @staticmethod
    def can_access_community(user, community_id):
        """检查用户是否可以访问社区（查看详情）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 检查是否是社区工作人员
        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user.user_id
        )
        staff = db.session.execute(stmt).scalar_one_or_none()

        return staff is not None

    @staticmethod
    def can_manage_users(user, community_id):
        """检查用户是否可以管理社区用户（增删普通用户）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 检查是否是社区工作人员（主管或专员都可以管理用户）
        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user.user_id
        )
        staff = db.session.execute(stmt).scalar_one_or_none()

        return staff is not None

    @staticmethod
    def can_manage_staff(user, community_id):
        """检查用户是否可以管理社区工作人员（增删专员）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 只有社区主管可以管理工作人员
        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user.user_id,
            CommunityStaff.role == 'manager'
        )
        staff = db.session.execute(stmt).scalar_one_or_none()

        return staff is not None

    @staticmethod
    def is_community_manager(user, community_id):
        """检查用户是否是社区主管"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        stmt = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user.user_id,
            CommunityStaff.role == 'manager'  # 主管角色
        )
        staff = db.session.execute(stmt).scalar_one_or_none()

        return staff is not None

    @staticmethod
    def validate_ankafamily_rule(user_id, target_community_id, operator):
        """验证安卡大家庭规则"""
        # 获取安卡大家庭社区
        stmt = select(Community).where(Community.is_default == True)
        ankafamily = db.session.execute(stmt).scalar_one_or_none()
        if not ankafamily:
            raise ValueError("安卡大家庭社区不存在")

        # 检查用户当前社区
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        # 用户必须在安卡大家庭才能被添加到其他社区
        if user.community_id != ankafamily.community_id:
            raise ValueError("用户不在安卡大家庭，无法添加到其他社区")

        # 检查目标社区不是安卡大家庭
        if target_community_id == ankafamily.community_id:
            raise ValueError("不能将用户添加到安卡大家庭")

        return True

    @staticmethod
    def has_community_permission(user_id, community_id):
        """
        检查用户是否有社区管理权限

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            bool: 是否有权限
        """
        from database.flask_models import CommunityStaff

        # 检查用户是否存在
        user = db.session.get(User, user_id)
        if not user:
            logger.warning(f"用户不存在: user_id={user_id}")
            return False

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            logger.warning(f"社区不存在: community_id={community_id}")
            return False

        # 超级管理员有所有社区权限
        if user.role == 4:  # 超级管理员
            logger.info(f"超级管理员 {user_id} 有所有社区权限")
            return True

        # 检查用户是否是该社区的工作人员
        stmt = select(CommunityStaff).where(
            CommunityStaff.user_id == user_id,
            CommunityStaff.community_id == community_id
        )
        staff = db.session.execute(stmt).scalar_one_or_none()

        if staff:
            logger.info(f"用户 {user_id} 是社区 {community_id} 的工作人员，角色: {staff.role}")
            return True

        # 检查用户是否属于该社区（普通社区成员）
        if user.community_id == community_id:
            logger.info(f"用户 {user_id} 属于社区 {community_id}，但无工作人员权限")
            # 普通社区成员没有管理权限
            return False

        logger.warning(f"用户 {user_id} 无社区 {community_id} 的管理权限")
        return False

    @staticmethod
    def verify_user_community_access(user_id, community_id):
        """
        验证用户是否属于指定社区

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            bool: 是否属于该社区
        """
        try:
            user = db.session.get(User, user_id)
            if not user:
                logger.warning(f"用户不存在: user_id={user_id}")
                return False

            return user.community_id == community_id

        except Exception as e:
            logger.error(f"验证用户社区访问失败: {str(e)}")
            return False