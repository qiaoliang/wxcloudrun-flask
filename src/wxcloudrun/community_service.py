"""
社区服务模块
处理社区相关的核心业务逻辑
"""

import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from .dao import get_db
from database.models import User, Community, CommunityApplication, UserAuditLog
from const_default import DEFUALT_COMMUNITY_NAME,DEFUALT_COMMUNITY_ID
logger = logging.getLogger('log')


class CommunityService:
    """社区服务类"""

    @staticmethod
    def assign_user_to_community(user, community_name):
        """将用户分配到社区"""
        if not community_name:
            raise ValueError("社区名称不能为空")

        db = get_db()
        with db.get_session() as session:
            community = session.query(Community).filter_by(name=community_name).first()
            if not community:
                raise ValueError(f"社区不存在: {community_name}")

            # 更新用户的社区ID
            user.community_id = community.community_id
            session.merge(user)
            session.commit()

            logger.info(f"用户 {user.user_id} 已分配到社区 {community.community_id}")
            return community

    @staticmethod
    def create_community(name, description, creator_id, location=None, settings=None, manager_id=None, location_lat=None, location_lon=None):
        """创建新社区"""
        db = get_db()
        with db.get_session() as session:
            # 检查社区名称是否已存在
            existing = session.query(Community).filter_by(name=name).first()
            if existing:
                raise ValueError("社区名称已存在")

            # 如果指定了主管,检查用户是否存在
            if manager_id:
                manager = session.query(User).get(manager_id)
                if not manager:
                    raise ValueError("指定的主管不存在")

            # 创建社区
            community = Community(
                name=name,
                description=description,
                creator_user_id=creator_id,
                location=location,
                settings=json.dumps(settings or {}, ensure_ascii=False)
            )

            # 注意：location_lat 和 location_lon 字段在当前模型中不存在

            session.add(community)
            session.flush()  # 获取community_id

            # 设置主管：优先使用指定的manager_id，否则创建者自动成为主管
            from database.models import CommunityStaff
            final_manager_id = manager_id if manager_id else creator_id

            staff_role = CommunityStaff(
                community_id=community.community_id,
                user_id=final_manager_id,
                role='manager'  # 主管
            )
            session.add(staff_role)

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=creator_id,
                action="create_community",
                detail=f"创建社区: {name}, 主管: {final_manager_id}"
            )
            session.add(audit_log)

            session.commit()
            session.refresh(community)  # 确保所有属性都已加载
            logger.info(f"社区创建成功: {name}, ID: {community.community_id}, 主管: {final_manager_id}")

            # 返回字典而不是对象，避免 session 关闭后的 DetachedInstanceError
            return {
                'community_id': community.community_id,
                'name': community.name,
                'description': community.description,
                'location': community.location,
                'status': community.status,
                'is_default': community.is_default,
                'creator_user_id': community.creator_user_id,
                'created_at': community.created_at,
                'updated_at': community.updated_at
            }

    @staticmethod
    def add_community_admin(community_id, user_id, role=2, operator_id=None):
        """添加社区管理员"""
        # 导入新的CommunityStaff模型
        from database.models import CommunityStaff

        # 将role值映射到新的角色系统
        # role: 1(主管理员) -> 'manager', 2(普通管理员) -> 'staff'
        role_mapping = {1: 'manager', 2: 'staff'}
        staff_role = role_mapping.get(role, 'staff')

        db = get_db()
        with db.get_session() as session:
            # 检查用户是否已经是该社区的管理员
            existing = session.query(CommunityStaff).filter_by(
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
            session.add(staff_record)

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=operator_id or user_id,
                action="add_community_admin",
                detail=f"添加社区管理员: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}"
            )
            session.add(audit_log)

            session.commit()
            logger.info(f"社区管理员添加成功: 社区ID={community_id}, 用户ID={user_id}, 角色={staff_role}")
            return staff_record

    @staticmethod
    def remove_community_admin(community_id, user_id, operator_id=None):
        """移除社区管理员"""
        # 导入新的CommunityStaff模型
        from database.models import CommunityStaff

        db = get_db()
        with db.get_session() as session:
            # 从CommunityStaff表中查找
            staff_record = session.query(CommunityStaff).filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()

            if not staff_record:
                raise ValueError("用户不是该社区的管理员")

            # 检查是否是唯一的主管理员
            if staff_record.role == 'manager':
                manager_count = session.query(CommunityStaff).filter_by(
                    community_id=community_id,
                    role='manager'
                ).count()
                if manager_count <= 1:
                    raise ValueError("不能移除唯一的主管理员")

            # 删除CommunityStaff记录
            session.delete(staff_record)

            # 记录审计日志
            audit_log = UserAuditLog(
                user_id=operator_id,
                action="remove_community_admin",
                detail=f"移除社区管理员: 社区ID={community_id}, 用户ID={user_id}"
            )
            session.add(audit_log)

            session.commit()
            logger.info(f"社区管理员移除成功: 社区ID={community_id}, 用户ID={user_id}")

    @staticmethod
    def process_application(application_id, approve, processor_id, rejection_reason=None):
        """处理社区申请"""
        db = get_db()
        with db.get_session() as session:
            application = session.query(CommunityApplication).get(application_id)
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
                user = session.query(User).get(application.user_id)
                user.community_id = application.target_community_id

                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=processor_id,
                    action="approve_community_application",
                    detail=f"批准社区申请: 申请ID={application_id}, 用户ID={application.user_id}"
                )
                session.add(audit_log)

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
                session.add(audit_log)

                logger.info(f"社区申请拒绝: 申请ID={application_id}, 理由={rejection_reason}")

            session.commit()
            return application

    @staticmethod
    def search_community_users(community_id, keyword=None, page=1, per_page=20):
        """搜索社区用户（非管理员）"""
        db = get_db()
        with db.get_session() as session:
            query = session.query(User).filter_by(community_id=community_id)

            # 排除社区管理员
            from database.models import CommunityStaff
            admin_user_ids = session.query(CommunityStaff.user_id).filter_by(
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

            # 分页
            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

            return pagination

    @staticmethod
    def get_available_communities():
        """获取可申请的社区列表（排除默认社区）"""
        db = get_db()
        with db.get_session() as session:
            return session.query(Community).filter(
                Community.status == 1,  # 启用状态
                Community.is_default == False  # 非默认社区
            ).all()

    @staticmethod
    def get_community_by_id(community_id):
        """根据ID获取社区"""
        db = get_db()
        with db.get_session() as session:
            return session.query(Community).get(community_id)

    @staticmethod
    def get_communities_with_filters(status_filter='all', page=1, page_size=20):
        """获取带过滤条件的社区列表"""
        db = get_db()
        with db.get_session() as session:
            query = session.query(Community)

            # 状态筛选
            if status_filter == 'active':
                query = query.filter_by(status=1)
            elif status_filter == 'inactive':
                query = query.filter_by(status=2)

            # 分页
            total = query.count()
            offset = (page - 1) * page_size
            communities = query.order_by(Community.created_at.desc()).offset(offset).limit(page_size).all()

            return communities, total

    @staticmethod
    def update_community_info(community_id, name=None, description=None, location=None, status=None):
        """更新社区信息"""
        db = get_db()
        with db.get_session() as session:
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 更新字段
            if name is not None:
                # 检查名称是否与其他社区重复
                existing = session.query(Community).filter(
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

            session.commit()
            return community

    @staticmethod
    def get_community_staff_list(community_id, role_filter='all', sort_by='time'):
        """获取社区工作人员列表"""
        from database.models import CommunityStaff

        db = get_db()
        with db.get_session() as session:
            # 构建查询
            query = session.query(CommunityStaff).filter_by(community_id=community_id)

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
        from database.models import CommunityStaff

        db = get_db()
        with db.get_session() as session:
            # 检查社区是否存在
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 如果是添加主管,只能添加一个
            if role == 'manager' and len(user_ids) > 1:
                raise ValueError("主管只能添加一个")

            # 检查是否已有主管
            if role == 'manager':
                existing_manager = session.query(CommunityStaff).filter_by(
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
                    target_user = session.query(User).get(user_id)
                    if not target_user:
                        failed.append({'user_id': user_id, 'reason': '用户不存在'})
                        continue

                    # 检查用户是否已在当前社区任职（避免在同一社区重复任职）
                    existing_in_current_community = session.query(CommunityStaff).filter_by(
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
                    session.add(staff)
                    added_count += 1

                except Exception as e:
                    logger.error(f'添加工作人员失败 user_id={user_id}: {str(e)}')
                    failed.append({'user_id': user_id, 'reason': str(e)})

            session.commit()

            if added_count == 0:
                raise ValueError({'failed': failed}, '添加失败')

            return {
                'added_count': added_count,
                'failed': failed
            }

    @staticmethod
    def remove_community_staff(community_id, user_id):
        """移除社区工作人员"""
        from database.models import CommunityStaff

        db = get_db()
        with db.get_session() as session:
            # 检查社区是否存在
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 查找工作人员记录
            staff = session.query(CommunityStaff).filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()

            if not staff:
                raise ValueError("工作人员不存在")

            # 删除记录
            session.delete(staff)
            session.commit()

    @staticmethod
    def get_community_members(community_id, page=1, page_size=20):
        """获取社区成员列表"""
        from database.models import CommunityMember
        from database.models import CheckinRecord
        from datetime import date

        db = get_db()
        with db.get_session() as session:
            # 分页查询社区成员
            offset = (page - 1) * page_size
            query = session.query(CommunityMember).filter_by(community_id=community_id)
            total = query.count()
            members = query.order_by(CommunityMember.joined_at.desc()).offset(offset).limit(page_size).all()

            # 格式化响应数据
            members_data = []
            today = date.today()

            for member in members:
                member_user = session.query(User).get(member.user_id)
                if not member_user:
                    continue

                # 获取今日未完成打卡数和详情
                from sqlalchemy import and_, func
                unchecked_records = session.query(CheckinRecord).filter(
                    and_(
                        CheckinRecord.solo_user_id == member.user_id,
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
                    'join_time': member.joined_at.isoformat() if member.joined_at else None,
                    'unchecked_count': len(unchecked_items),
                    'unchecked_items': unchecked_items
                }

                members_data.append(user_data)

            return members_data, total

    @staticmethod
    def add_users_to_community(community_id, user_ids):
        """批量添加用户到社区"""
        from database.models import CommunityMember

        db = get_db()
        with db.get_session() as session:
            # 检查社区是否存在
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            added_count = 0
            failed = []

            for user_id in user_ids:
                try:
                    # 检查用户是否存在
                    target_user = session.query(User).get(user_id)
                    if not target_user:
                        failed.append({'user_id': user_id, 'reason': '用户不存在'})
                        continue

                    # 检查是否已在社区
                    existing = session.query(CommunityMember).filter_by(
                        community_id=community_id,
                        user_id=user_id
                    ).first()

                    if existing:
                        failed.append({'user_id': user_id, 'reason': '用户已在社区'})
                        continue

                    # 添加用户到社区
                    member = CommunityMember(
                        community_id=community_id,
                        user_id=user_id
                    )
                    session.add(member)
                    added_count += 1

                except Exception as e:
                    logger.error(f'添加用户失败 user_id={user_id}: {str(e)}')
                    failed.append({'user_id': user_id, 'reason': str(e)})

            session.commit()

            if added_count == 0:
                raise ValueError({'added_count': added_count, 'failed': failed}, '添加失败')

            return {
                'added_count': added_count,
                'failed': failed
            }

    @staticmethod
    def remove_user_from_community(community_id, user_id):
        """从社区移除用户"""
        from database.models import CommunityMember, CommunityStaff
        from const_default import DEFUALT_COMMUNITY_NAME
        db = get_db()
        with db.get_session() as session:
            # 检查社区是否存在
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 查找成员记录
            member = session.query(CommunityMember).filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()

            if not member:
                raise ValueError("用户不在该社区")

            # 特殊社区逻辑处理
            moved_to = None

            # 获取特殊社区ID
            anka_family = session.query(Community).filter_by(name=DEFUALT_COMMUNITY_NAME).first()
            blackhouse = session.query(Community).filter_by(name='黑屋').first()

            # 如果从"安卡大家庭"移除,移入"黑屋"
            if community.name == DEFUALT_COMMUNITY_NAME and blackhouse:
                # 检查是否已在黑屋
                existing_in_blackhouse = session.query(CommunityMember).filter_by(
                    community_id=blackhouse.community_id,
                    user_id=user_id
                ).first()

                if not existing_in_blackhouse:
                    blackhouse_member = CommunityMember(
                        community_id=blackhouse.community_id,
                        user_id=user_id
                    )
                    session.add(blackhouse_member)
                    moved_to = '黑屋'

            # 如果从普通社区移除
            elif community.name not in [DEFUALT_COMMUNITY_NAME, '黑屋']:
                # 检查用户是否还属于其他普通社区
                other_memberships = session.query(CommunityMember).filter(
                    CommunityMember.user_id == user_id,
                    CommunityMember.community_id != community_id
                ).join(Community).filter(
                    Community.name.notin_([DEFUALT_COMMUNITY_NAME, '黑屋'])
                ).count()

                # 如果不属于任何其他普通社区,移入"安卡大家庭"
                if other_memberships == 0 and anka_family:
                    # 检查是否已在安卡大家庭
                    existing_in_anka = session.query(CommunityMember).filter_by(
                        community_id=anka_family.community_id,
                        user_id=user_id
                    ).first()

                    if not existing_in_anka:
                        anka_member = CommunityMember(
                            community_id=anka_family.community_id,
                            user_id=user_id
                        )
                        session.add(anka_member)
                        moved_to = DEFUALT_COMMUNITY_NAME

            # 删除成员记录
            session.delete(member)
            session.commit()

            return {'moved_to': moved_to}

    @staticmethod
    def delete_community(community_id):
        """删除社区"""
        from database.models import CommunityMember, CommunityStaff
        from const_default import DEFUALT_COMMUNITY_NAME
        db = get_db()
        with db.get_session() as session:
            # 查找社区
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 特殊社区不能删除
            if community.name in [DEFUALT_COMMUNITY_NAME, '黑屋']:
                raise ValueError("特殊社区不能删除")

            # 检查社区状态
            if community.status == 1:
                raise ValueError("请先停用社区")

            # 检查社区内是否还有用户
            member_count = session.query(CommunityMember).filter_by(community_id=community_id).count()
            if member_count > 0:
                raise ValueError({
                    'user_count': member_count
                }, '社区内还有用户，无法删除')

            # 删除相关数据
            session.query(CommunityStaff).filter_by(community_id=community_id).delete()
            session.query(CommunityApplication).filter_by(target_community_id=community_id).delete()

            # 删除社区
            session.delete(community)
            session.commit()

    @staticmethod
    def toggle_community_status(community_id, status):
        """切换社区状态"""
        from const_default import DEFUALT_COMMUNITY_NAME
        db = get_db()
        with db.get_session() as session:
            # 查找社区
            community = session.query(Community).get(community_id)
            if not community:
                raise ValueError("社区不存在")

            # 特殊社区不能停用
            if community.name in [DEFUALT_COMMUNITY_NAME, '黑屋']:
                raise ValueError("特殊社区不能停用")

            # 更新状态
            community.status = 1 if status == 'active' else 2
            session.commit()

            return {
                'community_id': community_id,
                'status': status
            }

    @staticmethod
    def search_users(keyword, community_id=None):
        """搜索用户"""
        from database.models import CommunityStaff, CommunityMember

        db = get_db()
        with db.get_session() as session:
            # 搜索用户 (按昵称或手机号)
            users_query = session.query(User).filter(
                (User.nickname.like(f'%{keyword}%')) |
                (User.phone_number.like(f'%{keyword}%'))
            ).limit(20)

            users = users_query.all()

            # 格式化响应
            result = []
            for u in users:
                # 检查是否已是任何社区的工作人员
                is_staff = session.query(CommunityStaff).filter_by(user_id=u.user_id).first() is not None

                user_data = {
                    'user_id': str(u.user_id),
                    'nickname': u.nickname,
                    'avatar_url': u.avatar_url,
                    'phone_number': u.phone_number,
                    'is_staff': is_staff
                }

                # 如果指定了community_id,检查是否已在该社区
                if community_id:
                    already_in = session.query(CommunityMember).filter_by(
                        community_id=community_id,
                        user_id=u.user_id
                    ).first() is not None
                    user_data['already_in_community'] = already_in

                result.append(user_data)

            return result