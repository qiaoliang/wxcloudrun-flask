"""
获取待处理邀请数量用例
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory

app_logger = logging.getLogger('log')


class GetPendingInvitationsCountUseCase(BaseUseCase):
    """获取待处理邀请数量用例"""

    # 邀请状态常量
    STATUS_PENDING = 1  # 待处理
    STATUS_EXPIRED = 4  # 已过期

    # 规则状态常量
    RULE_STATUS_ACTIVE = 1  # 启用

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取待处理邀请数量

        Args:
            user_id: 用户ID（监督人）

        Returns:
            UseCaseResult: 执行结果，包含待处理邀请数量
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult.fail('用户ID不能为空', status=UseCaseStatus.VALIDATION_ERROR)

            # 2. 查询用户收到的所有邀请（作为监督人）
            invitations = self.supervision_relation_repository.find_by_supervisor_id(user_id)

            # 3. 筛选待处理的邀请
            pending_count = 0
            for invitation in invitations:
                # 检查邀请状态是否为待处理
                if invitation.status != self.STATUS_PENDING:
                    continue

                # 检查邀请是否过期
                if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                    continue

                # 检查规则是否活跃
                rule = self.checkin_rule_repository.find_by_id(invitation.rule_id)
                if not rule or rule.status != self.RULE_STATUS_ACTIVE:
                    continue

                # 检查规则是否被删除
                if not rule or rule.deleted_at is not None:
                    continue

                pending_count += 1

            app_logger.info(f'获取待处理邀请数量成功: user_id={user_id}, count={pending_count}')

            return UseCaseResult.success(data={
                'pending_count': pending_count
            })

        except Exception as e:
            app_logger.error(f'获取待处理邀请数量失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'获取待处理邀请数量失败: {str(e)}')