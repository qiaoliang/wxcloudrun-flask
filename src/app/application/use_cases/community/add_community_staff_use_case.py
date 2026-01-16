"""
添加社区工作人员用例
"""
import logging
from typing import List, Dict
from sqlalchemy import select

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, User, Community, CommunityStaff, UserAuditLog
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_COMMUNITY_ID
from app.shared.constants.roles import Role, COMMUNITY_STAFF_ROLES, ADMIN_ROLES, STAFF_ROLE_STAFF, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class AddCommunityStaffUseCase(BaseUseCase):
    """添加社区工作人员用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_repository = RepositoryFactory.get_community_repository()

    def execute(
        self,
        operator_user_id: int,
        community_id: int,
        user_ids: List[int],
        role: str = 'staff'
    ) -> UseCaseResult:
        """
        执行添加社区工作人员

        Args:
            operator_user_id: 操作者用户ID
            community_id: 社区ID
            user_ids: 要添加的用户ID列表
            role: 角色，'manager' 或 'staff'

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(operator_user_id, community_id, user_ids, role)
            if not validation_result.is_success:
                return validation_result

            # 2. 验证并处理用户ID
            processed_user_ids = self._process_user_ids(user_ids)
            if not processed_user_ids['valid_ids']:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'所有用户ID都无效: {processed_user_ids["failed"]}'
                )

            # 3. 验证权限
            operator_user = db.session.get(User, operator_user_id)
            if not operator_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='操作者用户不存在'
                )

            # 检查操作者权限
            if operator_user.role != Role.SUPER_ADMIN:
                stmt_staff = select(CommunityStaff).where(
                    CommunityStaff.community_id == community_id,
                    CommunityStaff.user_id == operator_user_id,
                    CommunityStaff.removed_at.is_(None)
                )
                staff_record = db.session.execute(stmt_staff).scalar_one_or_none()
                if not staff_record:
                    return UseCaseResult(
                        status=UseCaseStatus.FORBIDDEN,
                        message='权限不足，需要社区工作人员权限'
                    )

                # 如果是专员（非主管）尝试添加任何工作人员，则拒绝
                if staff_record.role == STAFF_ROLE_STAFF:
                    return UseCaseResult(
                        status=UseCaseStatus.FORBIDDEN,
                        message='专员不能添加工作人员，需要主管权限'
                    )

            # 4. 执行添加
            result = self._add_staff(
                operator_user, community_id, processed_user_ids['valid_ids'], role
            )

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加成功',
                data=result
            )

        except ValueError as e:
            logger.error(f'添加社区工作人员失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=str(e)
            )
        except Exception as e:
            logger.error(f'添加社区工作人员失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加失败: {str(e)}'
            )

    def _validate_params(
        self,
        operator_user_id: int,
        community_id: int,
        user_ids: List[int],
        role: str
    ) -> UseCaseResult:
        """验证参数"""
        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少社区ID'
            )

        if not user_ids or not isinstance(user_ids, list):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID列表不能为空'
            )

        if role not in [STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF]:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='角色参数错误，必须是manager或staff'
            )

        # 检查社区是否存在
        community = db.session.get(Community, community_id)
        if not community:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message='社区不存在'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _process_user_ids(self, user_ids: List[int]) -> Dict:
        """处理用户ID，返回有效和无效的ID"""
        valid_ids = []
        failed = []

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

                valid_ids.append(uid_int)
            except (ValueError, TypeError) as e:
                failed.append({'user_id': uid, 'reason': f'无效的用户ID格式: {str(e)}'})
                continue

        return {'valid_ids': valid_ids, 'failed': failed}

    def _add_staff(
        self,
        operator_user: User,
        community_id: int,
        user_ids: List[int],
        role: str
    ) -> Dict:
        """添加工作人员到社区"""
        from datetime import datetime

        # 如果是添加主管,只能添加一个
        if role == STAFF_ROLE_MANAGER and len(user_ids) > 1:
            raise ValueError('主管只能添加一个')

        # 检查是否已有主管（但排除正在升级的情况）
        if role == STAFF_ROLE_MANAGER:
            from sqlalchemy import select
            stmt_manager = select(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.role == STAFF_ROLE_MANAGER,
                CommunityStaff.removed_at.is_(None)
            )
            existing_manager = db.session.execute(stmt_manager).scalar_one_or_none()
            # 如果已有主管，且不是正在升级的这些用户之一，则拒绝
            if existing_manager and existing_manager.user_id not in user_ids:
                raise ValueError('该社区已有主管')

        added_users_info = []
        success_count = 0
        skipped_count = 0

        for uid in user_ids:
            try:
                # 检查用户是否存在
                target_user = db.session.get(User, uid)
                if not target_user:
                    logger.warning(f'用户{uid}不存在，跳过')
                    continue

                # Check if user has phone number
                if not target_user.phone_number or not target_user.phone_number.strip():
                    logger.warning(f'用户{uid}未绑定电话号码，跳过')
                    continue

                # 检查是否需要更新用户的社区归属
                if target_user.community_id == DEFAULT_COMMUNITY_ID:
                    target_user.community_id = community_id
                    target_user.community_joined_at = datetime.now()
                    logger.info(f'用户{uid}从安卡大家庭转入社区{community_id}')
                elif target_user.community_id != community_id:
                    logger.info(f'用户{uid}不在安卡大家庭，保持当前社区{target_user.community_id}')

                # 检查用户是否已在当前社区任职
                from sqlalchemy import select
                stmt_existing = select(CommunityStaff).where(
                    CommunityStaff.community_id == community_id,
                    CommunityStaff.user_id == uid,
                    CommunityStaff.removed_at.is_(None)
                )
                existing_in_current_community = db.session.execute(stmt_existing).scalar_one_or_none()

                if existing_in_current_community:
                    # 用户已在该社区有角色
                    if existing_in_current_community.role == role:
                        # 尝试添加相同角色，静默跳过
                        logger.info(f'用户{uid}已在社区{community_id}担任{role}角色，跳过')
                        skipped_count += 1
                        continue
                    elif existing_in_current_community.role == STAFF_ROLE_STAFF and role == STAFF_ROLE_MANAGER:
                        # 专员升级为主管：允许，更新角色记录
                        existing_in_current_community.role = STAFF_ROLE_MANAGER
                        logger.info(f'用户{uid}在社区{community_id}从专员升级为主管')
                        self._recalculate_user_role(uid)
                        success_count += 1

                        # 更新用户的 role 字段
                        target_user.role = Role.MANAGER

                        continue
                    elif existing_in_current_community.role == STAFF_ROLE_MANAGER and role == STAFF_ROLE_STAFF:
                        # 主管降级为专员：只有超级管理员可以操作
                        if operator_user.role == Role.SUPER_ADMIN:
                            # 允许降级
                            existing_in_current_community.role = STAFF_ROLE_STAFF
                            logger.info(f'超级管理员将用户{uid}在社区{community_id}从主管降级为专员')
                            self._recalculate_user_role(uid)
                            success_count += 1

                            # 更新用户的 role 字段
                            target_user.role = Role.STAFF

                            continue
                        else:
                            # 非超级管理员，拒绝降级
                            logger.warning(f'用户{uid}已是该社区的主管，只有超级管理员可以降级为专员')
                            continue

                # 添加工作人员
                staff = CommunityStaff(
                    community_id=community_id,
                    user_id=uid,
                    role=role
                )
                db.session.add(staff)

                # 更新用户的 role 字段
                if role == STAFF_ROLE_MANAGER:
                    target_user.role = Role.MANAGER
                elif role == STAFF_ROLE_STAFF:
                    target_user.role = Role.STAFF

                # 记录审计日志
                audit_log = UserAuditLog(
                    user_id=operator_user.user_id,
                    action="add_community_staff",
                    detail=f"添加用户{uid}为社区{community_id}的{role}，更新角色为{target_user.role}"
                )
                db.session.add(audit_log)

                success_count += 1

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

        # 如果添加的是主管，更新Community表的manager_id字段
        if role == STAFF_ROLE_MANAGER and success_count > 0:
            # 获取添加的主管用户ID（只取第一个，因为前面已经验证只能添加一个）
            manager_user_id = user_ids[0]
            logger.info(f'准备更新社区{community_id}的主管ID为{manager_user_id}')

            # 更新Community表的manager_id字段
            community = db.session.get(Community, community_id)
            if community:
                old_manager_id = community.manager_id
                community.manager_id = manager_user_id
                logger.info(f'成功更新社区{community_id}的manager_id: {old_manager_id} -> {manager_user_id}')

        return {
            'success_count': success_count,
            'failed': [],
            'added_users': added_users_info,
            'skipped_count': skipped_count
        }

    def _recalculate_user_role(self, user_id: int) -> int:
        """
        重新计算用户的角色（role字段）

        Args:
            user_id: 用户ID

        Returns:
            int: 计算后的角色ID
        """
        from sqlalchemy import select

        # 如果用户当前是超级管理员，保持不变
        user = db.session.get(User, user_id)
        if user and user.role == Role.SUPER_ADMIN:
            return Role.SUPER_ADMIN

        # 查询用户在所有社区的工作人员角色
        stmt = select(CommunityStaff).where(
            CommunityStaff.user_id == user_id,
            CommunityStaff.removed_at.is_(None)
        )
        staff_records = db.session.execute(stmt).scalars().all()

        # 如果没有任何工作人员记录，设为普通用户
        if not staff_records:
            if user:
                user.role = Role.SOLO
            db.session.flush()
            return Role.SOLO

        # 检查是否有主管角色
        has_manager = any(record.role == STAFF_ROLE_MANAGER for record in staff_records)

        if has_manager:
            # 有主管角色，设为主管（role=3）
            if user:
                user.role = Role.MANAGER
            db.session.flush()
            return Role.MANAGER
        else:
            # 只有专员角色，设为专员（role=2）
            if user:
                user.role = Role.STAFF
            db.session.flush()
            return Role.STAFF
