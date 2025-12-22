"""
社区服务模块 - Flask-SQLAlchemy版本
处理社区相关的核心业务逻辑
"""

import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from database.flask_models import db, User, Community, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID,DEFAULT_BLACK_ROOM_NAME,DEFAULT_BLACK_ROOM_ID
logger = logging.getLogger('CommunityService')


class CommunityService:
    """社区服务类"""

    @staticmethod
    def assign_user_to_community(user, community_name):
        """将用户分配到社区"""
        if not community_name:
            raise ValueError("社区名称不能为空")

        community = db.session.query(Community).filter_by(name=community_name).first()
        if not community:
            raise ValueError(f"社区不存在: {community_name}")

        # 更新用户的社区ID
        user.community_id = community.community_id
        db.session.merge(user)
        db.session.commit()

        logger.info(f"用户 {user.user_id} 已分配到社区 {community.community_id}")
        return community

    @staticmethod
    def query_community_by_id(comm_id):
        """根据ID查询社区"""
        existing = db.session.query(Community).filter_by(community_id=comm_id).first()
        return existing

    @staticmethod
    def query_community_by_name(comm_name):
        """根据名称查询社区"""
        existing = db.session.query(Community).filter_by(name=comm_name).first()
        return existing

    @staticmethod
    def create_community(name, description, creator_id, location=None, settings=None, manager_id=None, location_lat=None, location_lon=None):
        """创建新社区"""
        # 检查社区名称是否已存在
        existing = db.session.query(Community).filter_by(name=name).first()
        if existing:
            raise ValueError(f"社区名称已存在: {name}")

        # 创建社区
        community = Community(
            name=name,
            description=description,
            creator_id=creator_id,
            location=location,
            settings=settings or {},
            manager_id=manager_id,
            location_lat=location_lat,
            location_lon=location_lon,
            status=1,
            created_at=datetime.now()
        )

        db.session.add(community)
        db.session.commit()
        db.session.refresh(community)

        logger.info(f"创建社区成功: {community.community_id}")
        return community

    @staticmethod
    def add_community_admin(community_id, user_id, role=2, operator_id=None):
        """添加社区管理员"""
        # 导入CommunityStaff模型
        from database.flask_models import CommunityStaff

        # 将role值映射到新的角色系统
        # role: 1(主管理员) -> 'manager', 2(普通管理员) -> 'staff'
        role_mapping = {1: 'manager', 2: 'staff'}
        staff_role = role_mapping.get(role, 'staff')

        # 检查用户是否已经是该社区的管理员
        existing = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if existing:
            raise ValueError("用户已经是该社区的管理员")

        # 添加管理员到CommunityStaff表
        staff_record = CommunityStaff(
            community_id=community_id,
            user_id=user_id,
            role=staff_role
        )
        db.session.add(staff_record)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="add_community_admin",
            detail=f"添加社区管理员: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区管理员添加成功: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}")
        return staff_record

    @staticmethod
    def remove_community_admin(community_id, user_id, operator_id=None):
        """移除社区管理员"""
        from database.flask_models import CommunityStaff

        # 查找管理员记录
        staff_record = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if not staff_record:
            raise ValueError("用户不是该社区的管理员")

        # 删除管理员记录
        db.session.delete(staff_record)

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="remove_community_admin",
            detail=f"移除社区管理员: 社区ID={community_id}, 用户ID={user_id}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区管理员移除成功: 社区ID={community_id}, 用户ID={user_id}")
        return True

    @staticmethod
    def get_communities_with_filters(filters=None, page=1, limit=20):
        """根据筛选条件获取社区列表"""
        query = db.session.query(Community)

        if filters:
            if 'name' in filters:
                query = query.filter(Community.name.like(f"%{filters['name']}%"))
            if 'status' in filters:
                query = query.filter(Community.status == filters['status'])

        # 分页
        offset = (page - 1) * limit
        communities = query.offset(offset).limit(limit).all()
        total = query.count()

        return communities, total

    @staticmethod
    def process_application(application_id, approve, processor_id, rejection_reason=None):
        """处理社区申请"""
        application = db.session.query(CommunityApplication).get(application_id)
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
            user = db.session.query(User).get(application.user_id)
            user.community_id = application.target_community_id

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
        query = db.session.query(User).filter_by(community_id=community_id)

        # 排除社区管理员
        from database.flask_models import CommunityStaff
        admin_user_ids = db.session.query(CommunityStaff.user_id).filter_by(
            community_id=community_id
        ).subquery()
        query = query.filter(~User.user_id.in_(admin_user_ids))

        if keyword:
            # 判断是电话号码还是昵称
            if keyword.isdigit() and len(keyword) >= 7:
                # 电话号码精确搜索
                phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
                phone_hash = sha256(f"{phone_secret}:{keyword}".encode('utf-8')).hexdigest()
                query = query.filter_by(phone_hash=phone_hash)
            else:
                # 昵称模糊搜索
                query = query.filter(User.nickname.like(f"%{keyword}%"))

        # 分页 - 使用offset和limit实现
        total = query.count()
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()

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
        return db.session.query(Community).filter(
            Community.status == 1,  # 启用状态
            Community.is_default == False  # 非默认社区
        ).all()

    @staticmethod
    def get_community_by_id(community_id):
        """根据ID获取社区"""
        return db.session.query(Community).get(community_id)

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
    def get_communities_with_filters(status_filter='all', page=1, page_size=20):
        """获取带过滤条件的社区列表"""
        query = db.session.query(Community)

        # 状态筛选
        if status_filter == 'active':
            query = query.filter_by(status=1)
        elif status_filter == 'inactive':
            query = query.filter_by(status=2)

        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        communities = query.order_by(Community.created_at.desc()).offset(offset).limit(page_size).all()

        # 转换为字典列表，避免会话分离问题
        community_dicts = [CommunityService._community_to_dict(comm) for comm in communities]
        return community_dicts, total

    @staticmethod
    def get_manager_communities(user_id, status_filter='all', page=1, page_size=20):
        """获取用户作为主管的社区列表"""
        from database.flask_models import CommunityStaff

        # 获取用户作为主管的社区ID
        staff_records = db.session.query(CommunityStaff).filter_by(
            user_id=user_id,
            role='manager'
        ).all()

        community_ids = [record.community_id for record in staff_records]

        if not community_ids:
            return [], 0

        query = db.session.query(Community).filter(
            Community.community_id.in_(community_ids)
        )

        # 状态筛选
        if status_filter == 'active':
            query = query.filter_by(status=1)
        elif status_filter == 'inactive':
            query = query.filter_by(status=2)

        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        communities = query.order_by(Community.created_at.desc()).offset(offset).limit(page_size).all()

        # 转换为字典列表，避免会话分离问题
        community_dicts = [CommunityService._community_to_dict(comm) for comm in communities]
        return community_dicts, total

    @staticmethod
    def get_staff_communities(user_id, status_filter='all', page=1, page_size=20):
        """获取用户作为工作人员的社区列表（包括主管和专员）"""
        from database.flask_models import CommunityStaff

        # 获取用户作为工作人员的社区ID
        staff_records = db.session.query(CommunityStaff).filter_by(
            user_id=user_id
        ).all()

        community_ids = [record.community_id for record in staff_records]

        if not community_ids:
            return [], 0

        query = db.session.query(Community).filter(
            Community.community_id.in_(community_ids)
        )

        # 状态筛选
        if status_filter == 'active':
            query = query.filter_by(status=1)
        elif status_filter == 'inactive':
            query = query.filter_by(status=2)

        # 分页
        total = query.count()
        offset = (page - 1) * page_size
        communities = query.order_by(Community.created_at.desc()).offset(offset).limit(page_size).all()

        # 转换为字典列表，避免会话分离问题
        community_dicts = [CommunityService._community_to_dict(comm) for comm in communities]
        return community_dicts, total

    @staticmethod
    def update_community_info(community_id, name=None, description=None, location=None, status=None):
        """更新社区信息"""
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 更新字段
        if name is not None:
            # 检查名称是否与其他社区重复
            existing = db.session.query(Community).filter(
                Community.name == name,
                Community.community_id != community_id
            ).first()
            if existing:
                raise ValueError("社区名称已存在")
            community.name = name

        if description is not None:
            community.description = description

        if location is not None:
            community.location = location

        if status is not None:
            community.status = status

        # 更新时间
        community.updated_at = datetime.now()

        db.session.commit()
        return community

    @staticmethod
    def get_community_staff_list(community_id, role_filter='all', sort_by='time'):
        """获取社区工作人员列表"""
        from database.flask_models import CommunityStaff

        # 构建查询
        query = db.session.query(CommunityStaff).filter_by(community_id=community_id)

        # 角色筛选
        if role_filter != 'all':
            query = query.filter_by(role=role_filter)

        # 排序
        if sort_by == 'name':
            query = query.join(User).order_by(User.nickname)
        elif sort_by == 'role':
            query = query.order_by(CommunityStaff.role.desc())  # manager在前
        else:  # time
            query = query.order_by(CommunityStaff.added_at.desc())

        return query.all()

    @staticmethod
    def add_community_staff(community_id, user_ids, role='staff'):
        """添加社区工作人员"""
        from database.flask_models import CommunityStaff

        # 检查社区是否存在
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 如果是添加主管,只能添加一个
        if role == 'manager' and len(user_ids) > 1:
            raise ValueError("主管只能添加一个")

        # 检查是否已有主管
        if role == 'manager':
            existing_manager = db.session.query(CommunityStaff).filter_by(
                community_id=community_id,
                role='manager'
            ).first()
            if existing_manager:
                raise ValueError("该社区已有主管")

        added_count = 0
        failed = []

        for user_id in user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.query(User).get(user_id)
                if not target_user:
                    failed.append({'user_id': user_id, 'reason': '用户不存在'})
                    continue

                # 检查用户是否已在当前社区任职（避免在同一社区重复任职）
                existing_in_current_community = db.session.query(CommunityStaff).filter_by(
                    community_id=community_id,
                    user_id=user_id
                ).first()

                if existing_in_current_community:
                    failed.append({'user_id': user_id, 'reason': '用户已在当前社区任职'})
                    continue

                # 添加工作人员
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=user_id,
                    role=role
                )
                db.session.add(staff)
                added_count += 1

            except Exception as e:
                logger.error(f'添加工作人员失败 user_id={user_id}: {str(e)}')
                failed.append({'user_id': user_id, 'reason': str(e)})

        db.session.commit()

        if added_count == 0:
            raise ValueError({'failed': failed}, '添加失败')

        return {
            'added_count': added_count,
            'failed': failed
        }

    @staticmethod
    def remove_community_staff(community_id, user_id):
        """移除社区工作人员"""
        from database.flask_models import CommunityStaff

        # 检查社区是否存在
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 查找工作人员记录
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user_id
        ).first()

        if not staff:
            raise ValueError("工作人员不存在")

        # 删除记录
        db.session.delete(staff)
        db.session.commit()

    @staticmethod
    def get_community_members(community_id, page=1, page_size=20):
        """获取社区成员列表"""
        from database.flask_models import CheckinRecord
        from datetime import date

        # 分页查询社区成员 - 使用User表查询
        offset = (page - 1) * page_size
        query = db.session.query(User).filter_by(community_id=community_id)
        total = query.count()
        members = query.order_by(User.community_joined_at.desc()).offset(offset).limit(page_size).all()

        # 格式化响应数据
        members_data = []
        today = date.today()

        for member_user in members:
            if not member_user:
                continue

            # 获取今日未完成打卡数和详情
            from sqlalchemy import and_, func
            unchecked_records = db.session.query(CheckinRecord).filter(
                and_(
                    CheckinRecord.user_id == member_user.user_id,
                    func.date(CheckinRecord.planned_time) == today,
                    CheckinRecord.status == 0  # 0-missed(未打卡)
                )
            ).all()

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
    def add_users_to_community(community_id, user_ids):
        """批量添加用户到社区"""
        from datetime import datetime

        # 检查社区是否存在
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        added_count = 0
        failed = []

        for user_id in user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.query(User).get(user_id)
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
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 查找用户
        target_user = db.session.query(User).get(user_id)
        if not target_user:
            raise ValueError("用户不存在")

        # 特殊社区逻辑处理
        moved_to = None

        # 获取特殊社区ID
        anka_family = db.session.query(Community).filter_by(name=DEFUALT_COMMUNITY_NAME).first()
        blackhouse = db.session.query(Community).filter_by(name=DEFAULT_BLACK_ROOM_NAME).first()

        # 如果从"黑屋"社区移除，不能删除用户
        if community.name == DEFAULT_BLACK_ROOM_NAME:
            raise ValueError("不能从黑屋社区删除用户")

        # 如果从"安卡大家庭"移除,移入"黑屋"
        elif community.name == DEFUALT_COMMUNITY_NAME and blackhouse:
            # 对于安卡大家庭，不检查用户是否在该社区，直接移入黑屋
            # 检查是否已在黑屋
            if target_user.community_id != blackhouse.community_id:
                target_user.community_id = blackhouse.community_id
                target_user.community_joined_at = datetime.now()
                moved_to = DEFAULT_BLACK_ROOM_NAME

        # 如果从普通社区移除
        elif community.name not in [DEFUALT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
            # 检查用户是否在该社区（普通社区需要这个检查）
            if target_user.community_id != community_id:
                raise ValueError("用户不在该社区")

            # 检查用户是否还属于其他普通社区
            from sqlalchemy import and_
            other_communities_count = db.session.query(User).filter(
                and_(
                    User.user_id == user_id,
                    User.community_id != community_id,
                    User.community_id.isnot(None)
                )
            ).join(Community).filter(
                Community.name.notin_([DEFUALT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME])
            ).count()

            # 如果不属于任何其他普通社区,移入"安卡大家庭"
            if other_communities_count == 0 and anka_family:
                # 检查是否已在安卡大家庭
                if target_user.community_id != anka_family.community_id:
                    target_user.community_id = anka_family.community_id
                    target_user.community_joined_at = datetime.now()
                    moved_to = DEFUALT_COMMUNITY_NAME
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
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 特殊社区不能删除
        if community.name in [DEFUALT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
            raise ValueError("特殊社区不能删除")

        # 检查社区状态
        if community.status == 1:
            raise ValueError("请先停用社区")

        # 检查社区内是否还有用户
        member_count = db.session.query(User).filter_by(community_id=community_id).count()
        if member_count > 0:
            raise ValueError({
                'user_count': member_count
            }, '社区内还有用户，无法删除')

        # 删除相关数据
        db.session.query(CommunityStaff).filter_by(community_id=community_id).delete()
        db.session.query(CommunityApplication).filter_by(target_community_id=community_id).delete()

        # 删除社区
        db.session.delete(community)
        db.session.commit()

    @staticmethod
    def toggle_community_status(community_id, status):
        """切换社区状态"""
        # 查找社区
        community = db.session.query(Community).get(community_id)
        if not community:
            raise ValueError("社区不存在")

        # 特殊社区不能停用
        if community.name in [DEFUALT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
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

        # 搜索用户 (按昵称或手机号)
        users_query = db.session.query(User).filter(
            (User.nickname.like(f'%{keyword}%')) |
            (User.phone_number.like(f'%{keyword}%'))
        ).limit(20)

        users = users_query.all()

        # 格式化响应
        result = []
        for u in users:
            # 检查是否已是任何社区的工作人员
            is_staff = db.session.query(CommunityStaff).filter_by(user_id=u.user_id).first() is not None

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
    def get_manageable_communities(user, page=1, per_page=7):
        """获取用户可管理的社区列表"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            query = db.session.query(Community).filter_by(status=1)  # 只显示启用状态
        else:
            # 获取用户作为工作人员的社区
            staff_communities = db.session.query(CommunityStaff).filter_by(
                user_id=user.user_id
            ).all()
            community_ids = [sc.community_id for sc in staff_communities]

            if not community_ids:
                return [], 0

            query = db.session.query(Community).filter(
                Community.community_id.in_(community_ids),
                Community.status == 1  # 启用状态
            )

        # 分页查询
        total = query.count()
        offset = (page - 1) * per_page
        communities = query.order_by(Community.created_at.desc()).offset(offset).limit(per_page).all()

        return communities, total

    @staticmethod
    def search_communities_with_permission(user, keyword):
        """搜索社区（根据权限过滤）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            query = db.session.query(Community).filter(
                Community.name.like(f'%{keyword}%'),
                Community.status == 1
            )
        else:
            # 获取用户有权限的社区
            staff_communities = db.session.query(CommunityStaff).filter_by(
                user_id=user.user_id
            ).all()
            community_ids = [sc.community_id for sc in staff_communities]

            if not community_ids:
                return []

            query = db.session.query(Community).filter(
                Community.community_id.in_(community_ids),
                Community.name.like(f'%{keyword}%'),
                Community.status == 1
            )

        communities = query.limit(20).all()  # 限制搜索结果数量
        return communities

    @staticmethod
    def can_access_community(user, community_id):
        """检查用户是否可以访问社区（查看详情）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 检查是否是社区工作人员
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user.user_id
        ).first()

        return staff is not None

    @staticmethod
    def can_manage_users(user, community_id):
        """检查用户是否可以管理社区用户（增删普通用户）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 检查是否是社区工作人员（主管或专员都可以管理用户）
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user.user_id
        ).first()

        return staff is not None

    @staticmethod
    def can_manage_staff(user, community_id):
        """检查用户是否可以管理社区工作人员（增删专员）"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        # 只有社区主管可以管理工作人员
        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user.user_id,
            role='manager'  # 主管角色
        ).first()

        return staff is not None

    @staticmethod
    def is_community_manager(user, community_id):
        """检查用户是否是社区主管"""
        from database.flask_models import CommunityStaff

        if user.role == 4:  # 超级管理员
            return True

        staff = db.session.query(CommunityStaff).filter_by(
            community_id=community_id,
            user_id=user.user_id,
            role='manager'  # 主管角色
        ).first()

        return staff is not None

    @staticmethod
    def validate_ankafamily_rule(user_id, target_community_id, operator):
        """验证安卡大家庭规则"""
        # 获取安卡大家庭社区
        ankafamily = db.session.query(Community).filter_by(is_default=True).first()
        if not ankafamily:
            raise ValueError("安卡大家庭社区不存在")

        # 检查用户当前社区
        user = db.session.query(User).get(user_id)
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
        user = db.session.query(User).get(user_id)
        if not user:
            logger.warning(f"用户不存在: user_id={user_id}")
            return False

        # 检查社区是否存在
        community = db.session.query(Community).get(community_id)
        if not community:
            logger.warning(f"社区不存在: community_id={community_id}")
            return False

        # 超级管理员有所有社区权限
        if user.role == 4:  # 超级管理员
            logger.info(f"超级管理员 {user_id} 有所有社区权限")
            return True

        # 检查用户是否是该社区的工作人员
        staff = db.session.query(CommunityStaff).filter_by(
            user_id=user_id,
            community_id=community_id
        ).first()

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
            user = db.session.query(User).get(user_id)
            if not user:
                logger.warning(f"用户不存在: user_id={user_id}")
                return False

            return user.community_id == community_id

        except Exception as e:
            logger.error(f"验证用户社区访问失败: {str(e)}")
            return False