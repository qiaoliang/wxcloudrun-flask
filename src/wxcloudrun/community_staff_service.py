"""
社区工作人员服务模块 - Flask-SQLAlchemy版本
"""
import logging
import os
import json
from datetime import datetime
from hashlib import sha256
from sqlalchemy import select, func
from wxcloudrun.user_service import UserService
from database.flask_models import db, User, Community, CommunityStaff, CommunityApplication, UserAuditLog
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_COMMUNITY_ID
logger = logging.getLogger('CommunityService')


class CommunityStaffService:
    @staticmethod
    def check_user_is_staff(user_id):
        """
        检查用户是否是任何社区的工作人员

        Args:
            user_id (int): 用户ID

        Returns:
            bool: 如果是工作人员返回True，否则返回False
        """
        stmt = select(CommunityStaff).where(CommunityStaff.user_id == user_id)
        staff_record = db.session.execute(stmt).scalar_one_or_none()
        return staff_record is not None

    @staticmethod
    def add_staff(operator_user_id, community_id, user_ids, role='staff'):
        """
        添加社区工作人员（支持批量操作）

        Args:
            operator_user_id (int): 操作者用户ID
            community_id (int): 社区ID
            user_ids (list): 要添加的用户ID列表
            role (str): 角色，'manager' 或 'staff'

        Returns:
            dict: 包含添加结果的字典
            {
                'success_count': int,
                'failed': list,
                'added_users': list
            }

        Raises:
            ValueError: 当参数无效或权限不足时
        """
        # 参数验证
        if not community_id:
            raise ValueError('缺少社区ID')

        if not user_ids or not isinstance(user_ids, list):
            raise ValueError('用户ID列表不能为空')

        if role not in ['manager', 'staff']:
            raise ValueError('角色参数错误，必须是manager或staff')

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            raise ValueError('社区不存在')

        # 检查操作用户是否存在
        operator_user = db.session.get(User, operator_user_id)
        if not operator_user:
            raise ValueError('操作者用户不存在')

        # 检查操作者权限
        if operator_user.role != 4:  # 不是超级管理员
            stmt_staff = select(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.user_id == operator_user_id
            )
            staff_record = db.session.execute(stmt_staff).scalar_one_or_none()
            if not staff_record:
                raise ValueError('权限不足，需要社区工作人员权限')

            # 如果是专员（非主管）尝试添加主管，则拒绝
            if staff_record.role == 'staff' and role == 'manager':
                raise ValueError('专员不能添加主管，需要主管权限')

        # 如果是添加主管,只能添加一个
        if role == 'manager' and len(user_ids) > 1:
            raise ValueError('主管只能添加一个')

        # 检查是否已有主管
        if role == 'manager':
            stmt_manager = select(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.role == 'manager'
            )
            existing_manager = db.session.execute(stmt_manager).scalar_one_or_none()
            if existing_manager:
                raise ValueError('该社区已有主管')

        added_count = 0
        failed = []
        skipped_count = 0  # 跟踪静默跳过的用户数量

        # 验证并处理用户ID
        processed_user_ids = []
        for uid in user_ids:
            try:
                # 尝试转换为整数
                if isinstance(uid, str):
                    uid_int = int(uid)
                elif isinstance(uid, int):
                    uid_int = uid
                else:
                    failed.append({'user_id': uid, 'reason': f'无效的用户ID类型: {type(uid).__name__}'})
                    continue

                # 验证整数是否有效（正数）
                if uid_int <= 0:
                    failed.append({'user_id': uid, 'reason': '用户ID必须为正整数'})
                    continue

                processed_user_ids.append(uid_int)
            except (ValueError, TypeError) as e:
                failed.append({'user_id': uid, 'reason': f'无效的用户ID格式: {str(e)}'})
                continue

        # 如果没有有效的用户ID，抛出异常
        if not processed_user_ids:
            raise ValueError(f'所有用户ID都无效: {failed}')

        added_users_info = []

        for uid in processed_user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.get(User, uid)
                if not target_user:
                    failed.append({'user_id': uid, 'reason': '用户不存在'})
                    continue

                # 检查用户是否已在当前社区任职
                stmt_existing = select(CommunityStaff).where(
                    CommunityStaff.community_id == community_id,
                    CommunityStaff.user_id == uid
                )
                existing_in_current_community = db.session.execute(stmt_existing).scalar_one_or_none()

                if existing_in_current_community:
                    # 静默跳过已任职用户，不计入失败
                    logger.info(f'用户{uid}已在社区{community_id}任职，跳过添加')
                    skipped_count += 1
                    continue

                # 添加工作人员
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=uid,
                    role=role
                )
                db.session.add(staff)

                # 更新用户的 role 字段
                if role == 'manager':
                    target_user.role = 3  # 社区主管
                elif role == 'staff':
                    target_user.role = 2  # 社区专员

                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="add_community_staff",
                    detail=f"添加用户{uid}为社区{community_id}的{role}，更新角色为{target_user.role}"
                )
                db.session.add(audit_log)

                added_count += 1

                # 添加成功用户信息
                added_users_info.append({
                    'user_id': uid,
                    'nickname': target_user.nickname,
                    'phone_number': target_user.phone_number,
                    'role': role
                })

                logger.info(f'成功添加工作人员: 社区{community_id}, 用户{uid}, 角色{role}')

            except Exception as e:
                logger.error(f'添加工作人员失败 user_id={uid}: {str(e)}')
                failed.append({'user_id': uid, 'reason': str(e)})

        if added_count == 0:
            if failed:
                # 有真正的失败，报错
                error_details = "; ".join([f"用户{f['user_id']}: {f['reason']}" for f in failed])
                raise ValueError(f'添加失败: {error_details}')
            elif skipped_count > 0:
                # 所有用户都已被任职，这是正常情况，返回成功
                logger.info(f'所有{skipped_count}个用户都已在社区{community_id}任职，无需添加')
                return {
                    'success_count': 0,
                    'failed': [],
                    'added_users': [],
                    'skipped_count': skipped_count,
                    'message': '所有用户都已在社区任职'
                }
            else:
                # 既没有成功也没有失败，也没有跳过，这是异常情况
                raise ValueError('添加失败: 未知错误')

        # Layer 4: 调试仪表 - 如果添加的是主管，更新Community表的manager_id字段
        if role == 'manager' and added_count > 0:
            # 获取添加的主管用户ID（只取第一个，因为前面已经验证只能添加一个）
            manager_user_id = processed_user_ids[0]
            logger.info(f'Layer 4调试仪表 - 准备更新社区{community_id}的主管ID为{manager_user_id}')

            # 更新Community表的manager_id字段
            community = db.session.get(Community, community_id)
            if community:
                old_manager_id = community.manager_id
                community.manager_id = manager_user_id
                logger.info(f'Layer 4调试仪表 - 成功更新社区{community_id}的manager_id: {old_manager_id} -> {manager_user_id}')
            else:
                logger.error(f'Layer 4调试仪表 - 社区{community_id}不存在，无法更新manager_id')

        # 提交事务
        db.session.commit()

        return {
            'success_count': added_count,
            'failed': failed,
            'added_users': added_users_info,
            'skipped_count': skipped_count
        }

    @staticmethod
    def add_staff_single(community_id, user_id, role='staff', operator_id=None):
        """
        添加单个社区工作人员（保持向后兼容）

        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            role (str): 角色 ('manager' 或 'staff')
            operator_id (int): 操作者ID

        Returns:
            CommunityStaff: 工作人员记录
        """
        # 检查是否已经是工作人员
        stmt_existing = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user_id
        )
        existing = db.session.execute(stmt_existing).scalar_one_or_none()

        if existing:
            raise ValueError("用户已经是该社区的工作人员")

        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=community_id,
            user_id=user_id,
            role=role
        )
        db.session.add(staff)

        # 更新用户的 role 字段
        target_user = db.session.get(User, user_id)
        if target_user:
            if role == 'manager':
                target_user.role = 3  # 社区主管
            elif role == 'staff':
                target_user.role = 2  # 社区专员

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="add_staff",
            detail=f"添加社区工作人员: 社区ID={community_id}, 用户ID={user_id}, 角色={role}，更新角色为{target_user.role if target_user else 'N/A'}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区工作人员添加成功: 社区ID={community_id}, 用户ID={user_id}")
        return staff

    @staticmethod
    def remove_staff(community_id, user_id, operator_id=None):
        """
        移除社区工作人员

        Args:
            community_id (int): 社区ID
            user_id (int): 用户ID
            operator_id (int): 操作者ID

        Returns:
            bool: 是否成功
        """
        # Layer 1: 入口点验证 - 检查工作人员记录是否存在
        stmt_staff = select(CommunityStaff).where(
            CommunityStaff.community_id == community_id,
            CommunityStaff.user_id == user_id
        )
        staff = db.session.execute(stmt_staff).scalar_one_or_none()

        if not staff:
            raise ValueError("用户不是该社区的工作人员")

        # Layer 2: 业务逻辑验证 - 记录被移除工作人员的角色
        removed_role = staff.role
        logger.info(f'Layer 2验证 - 准备移除工作人员: 社区{community_id}, 用户{user_id}, 角色{removed_role}')

        db.session.delete(staff)

        # Layer 3: 环境守卫 - 如果移除的是主管，清理Community表的manager_id字段
        if removed_role == 'manager':
            logger.info(f'Layer 3环境守卫 - 移除的是主管，清理社区{community_id}的manager_id字段')
            community = db.session.get(Community, community_id)
            if community and community.manager_id == user_id:
                community.manager_id = None
                logger.info(f'Layer 3环境守卫 - 成功清理社区{community_id}的manager_id字段')

        # Layer 3: 环境守卫 - 检查用户是否还在其他社区担任工作人员
        target_user = db.session.get(User, user_id)
        if target_user:
            stmt_count = select(func.count()).select_from(CommunityStaff).where(CommunityStaff.user_id == user_id)
            other_staff_records = db.session.execute(stmt_count).scalar()
            if other_staff_records == 0:
                # 用户不在任何社区担任工作人员，重置为普通用户
                logger.info(f'Layer 3环境守卫 - 用户{user_id}不在任何社区担任工作人员，重置为普通用户')
                target_user.role = 1  # 普通用户
            else:
                logger.info(f'Layer 3环境守卫 - 用户{user_id}还在{other_staff_records}个社区担任工作人员，保持当前角色')

        # 记录审计日志
        audit_log = UserAuditLog(
            user_id=operator_id or user_id,
            action="remove_staff",
            detail=f"移除社区工作人员: 社区ID={community_id}, 用户ID={user_id}, 角色={removed_role}，用户当前角色={target_user.role if target_user else 'N/A'}"
        )
        db.session.add(audit_log)

        db.session.commit()
        logger.info(f"社区工作人员移除成功: 社区ID={community_id}, 用户ID={user_id}, 角色={removed_role}")
        return True

    @staticmethod
    def get_community_staff(community_id, role=None):
        """
        获取社区工作人员列表

        Args:
            community_id (int): 社区ID
            role (str): 角色筛选 (可选)

        Returns:
            list: 工作人员列表
        """
        stmt = select(CommunityStaff).where(CommunityStaff.community_id == community_id)

        if role:
            stmt = stmt.where(CommunityStaff.role == role)

        return db.session.execute(stmt).scalars().all()

    @staticmethod
    def handle_user_community_change(user_id, old_community_id, new_community_id):
        """
        处理用户社区变更时的规则管理

        Args:
            user_id (int): 用户ID
            old_community_id (int): 原社区ID（可能为None）
            new_community_id (int): 新社区ID

        Returns:
            dict: 处理结果
        """
        try:
            from datetime import datetime

            # 0. 更新用户的社区归属
            user = db.session.get(User, user_id)
            if not user:
                raise ValueError(f'用户不存在: {user_id}')

            old_user_community_id = user.community_id
            user.community_id = new_community_id
            if new_community_id != old_user_community_id:
                user.community_joined_at = datetime.now()

            # 1. 停用旧社区的社区规则
            deactivated_count = 0
            if old_community_id:
                deactivated_count = CommunityStaffService._deactivate_old_community_rules(
                    user_id, old_community_id
                )

            # 2. 激活新社区的社区规则
            activated_count = CommunityStaffService._activate_new_community_rules(
                user_id, new_community_id
            )

            # 3. 处理工作人员关系
            # 移除旧社区的工作人员关系
            if old_community_id:
                from sqlalchemy import delete
                stmt_delete = delete(CommunityStaff).where(
                    CommunityStaff.community_id == old_community_id,
                    CommunityStaff.user_id == user_id
                )
                db.session.execute(stmt_delete)

            # 如果新社区存在，检查是否需要添加工作人员关系
            if new_community_id:
                if user and user.role >= 2:  # 如果是管理员或以上
                    staff = CommunityStaff(
                        community_id=new_community_id,
                        user_id=user_id,
                        role='manager' if user.role >= 3 else 'staff'
                    )
                    db.session.add(staff)

            db.session.commit()

            logger.info(f"用户{user_id}社区切换完成: 停用{deactivated_count}个旧规则，激活{activated_count}个新规则")

            return {
                'success': True,
                'deactivated_count': deactivated_count,
                'activated_count': activated_count,
                'message': f'成功停用{deactivated_count}个旧规则，激活{activated_count}个新规则'
            }

        except Exception as e:
            logger.error(f"处理用户社区切换失败: {str(e)}")
            raise ValueError(f"处理社区切换失败: {str(e)}")

    @staticmethod
    def _deactivate_old_community_rules(user_id, old_community_id):
        """
        停用旧社区的规则

        Args:
            user_id (int): 用户ID
            old_community_id (int): 原社区ID

        Returns:
            int: 停用的规则数量
        """
        from database.flask_models import UserCommunityRule, CommunityCheckinRule

        # 查找用户与旧社区规则的激活映射记录
        stmt_old = select(UserCommunityRule).join(CommunityCheckinRule).where(
            UserCommunityRule.user_id == user_id,
            CommunityCheckinRule.community_id == old_community_id,
            UserCommunityRule.is_active == True
        )
        old_mappings = db.session.execute(stmt_old).scalars().all()

        # 将这些规则标记为停用
        deactivated_count = 0
        for mapping in old_mappings:
            mapping.is_active = False
            deactivated_count += 1

        logger.info(f"用户{user_id}的{deactivated_count}个旧社区规则已停用")
        return deactivated_count

    @staticmethod
    def _activate_new_community_rules(user_id, new_community_id):
        """
        激活新社区的规则

        Args:
            user_id (int): 用户ID
            new_community_id (int): 新社区ID

        Returns:
            int: 激活的规则数量
        """
        from database.flask_models import UserCommunityRule, CommunityCheckinRule

        # 获取新社区的所有启用规则
        stmt_new = select(CommunityCheckinRule).where(
            CommunityCheckinRule.community_id == new_community_id,
            CommunityCheckinRule.status == 1  # 启用状态
        )
        new_community_rules = db.session.execute(stmt_new).scalars().all()

        activated_count = 0

        # 为用户创建或激活规则映射
        for rule in new_community_rules:
            # 查找是否已存在映射记录
            stmt_mapping = select(UserCommunityRule).where(
                UserCommunityRule.user_id == user_id,
                UserCommunityRule.community_rule_id == rule.community_rule_id
            )
            existing_mapping = db.session.execute(stmt_mapping).scalar_one_or_none()

            if existing_mapping:
                # 如果存在且当前是停用状态，重新激活
                if not existing_mapping.is_active:
                    existing_mapping.is_active = True
                    activated_count += 1
            else:
                # 如果不存在，创建新映射
                new_mapping = UserCommunityRule(
                    user_id=user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                db.session.add(new_mapping)
                activated_count += 1

        logger.info(f"用户{user_id}已激活{activated_count}个新社区规则")
        return activated_count