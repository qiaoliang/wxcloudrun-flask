"""
移除社区工作人员用例
"""

import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from database.flask_models import db, User, CommunityStaff, Community, UserAuditLog
from sqlalchemy import select
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER

logger = logging.getLogger(__name__)


class RemoveCommunityStaffUseCase(BaseUseCase):
    """移除社区工作人员用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        community_id: int,
        target_user_id: int,
        operator_user_id: Optional[int] = None
    ) -> UseCaseResult:
        """
        执行移除社区工作人员

        Args:
            community_id: 社区ID
            target_user_id: 目标用户ID
            operator_user_id: 操作者用户ID（可选，用于审计）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_params(community_id, target_user_id)
            if not validation_result.is_success:
                return validation_result

            # 2. 查询工作人员记录
            stmt_staff = select(CommunityStaff).where(
                CommunityStaff.community_id == community_id,
                CommunityStaff.user_id == target_user_id
            )
            staff = db.session.execute(stmt_staff).scalar_one_or_none()

            if not staff:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不是该社区的工作人员'
                )

            # 3. 获取被移除工作人员的角色
            removed_role = staff.role
            logger.info(f'准备移除工作人员: 社区{community_id}, 用户{target_user_id}, 角色{removed_role}')

            # 4. 软删除：设置 removed_at 时间戳
            staff.removed_at = datetime.now()

            # 5. 如果移除的是主管，清理Community表的manager_id字段
            if removed_role == STAFF_ROLE_MANAGER:
                logger.info(f'移除的是主管，清理社区{community_id}的manager_id字段')
                community = db.session.get(Community, community_id)
                if community and community.manager_id == target_user_id:
                    community.manager_id = None
                    logger.info(f'成功清理社区{community_id}的manager_id字段')

            # 6. 重新计算用户角色
            target_user = db.session.get(User, target_user_id)
            if target_user:
                new_role = self._recalculate_user_role(target_user_id)
                logger.info(f'用户{target_user_id}的角色重新计算为: {new_role}')

            # 7. 记录审计日志
            if operator_user_id:
                audit_log = UserAuditLog(
                    user_id=operator_user_id,
                    action="remove_community_staff",
                    detail=f"移除社区工作人员: 社区ID={community_id}, 用户ID={target_user_id}, 角色={removed_role}，用户当前角色={target_user.role if target_user else 'N/A'}"
                )
                db.session.add(audit_log)

            logger.info(f"社区工作人员移除成功: 社区ID={community_id}, 用户ID={target_user_id}, 角色={removed_role}")

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='移除成功',
                data={
                    'user_id': target_user_id,
                    'community_id': community_id,
                    'removed_role': removed_role
                }
            )

        except Exception as e:
            logger.error(f'移除社区工作人员失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'移除失败: {str(e)}'
            )

    def _validate_params(
        self,
        community_id: int,
        target_user_id: int
    ) -> UseCaseResult:
        """验证参数"""
        if not community_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少社区ID'
            )

        if not target_user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='缺少用户ID'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _recalculate_user_role(self, user_id: int) -> int:
        """
        重新计算用户的角色（role字段）

        Args:
            user_id: 用户ID

        Returns:
            int: 计算后的角色ID
        """
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