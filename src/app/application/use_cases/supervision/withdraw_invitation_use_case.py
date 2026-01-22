"""
撤回监督邀请用例
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transactional

app_logger = logging.getLogger('log')


class WithdrawInvitationUseCase(BaseUseCase):
    """撤回监督邀请用例"""

    # 邀请状态常量
    STATUS_PENDING = 1  # 待处理
    STATUS_WITHDRAWN = 5  # 已撤回

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    @transactional
    def execute(self, invitation_id: int, operator_id: int) -> UseCaseResult:
        """
        执行撤回监督邀请

        Args:
            invitation_id: 邀请ID（关系ID）
            operator_id: 操作者ID（邀请发起者）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not invitation_id:
                return UseCaseResult.fail('邀请ID不能为空', status=UseCaseStatus.VALIDATION_ERROR)

            if not operator_id:
                return UseCaseResult.fail('操作者ID不能为空', status=UseCaseStatus.VALIDATION_ERROR)

            # 2. 查找并验证邀请
            invitation = self.supervision_relation_repository.find_by_id(invitation_id)
            if not invitation:
                return UseCaseResult.fail('邀请不存在', status=UseCaseStatus.NOT_FOUND)

            # 3. 验证权限（只有邀请发起者可以撤回）
            if invitation.solo_user_id != operator_id:
                return UseCaseResult.fail('无权限操作此邀请', status=UseCaseStatus.FORBIDDEN)

            # 4. 验证状态（只能撤回待处理的邀请）
            if invitation.status != self.STATUS_PENDING:
                return UseCaseResult.fail(
                    '只能撤回待处理的邀请',
                    status=UseCaseStatus.BUSINESS_ERROR
                )

            # 5. 验证是否过期
            if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                return UseCaseResult.fail(
                    '邀请已过期，无法撤回',
                    status=UseCaseStatus.BUSINESS_ERROR
                )

            # 6. 更新邀请状态为已撤回
            invitation.status = self.STATUS_WITHDRAWN
            invitation.updated_at = datetime.now()

            success = self.supervision_relation_repository.update(invitation)
            if not success:
                return UseCaseResult.fail('更新邀请状态失败')

            # 7. 通知被邀请人邀请已撤回（可选）
            self._notify_withdrawal(invitation)

            app_logger.info(
                f'用户 {operator_id} 撤回邀请成功，邀请ID: {invitation_id}, '
                f'监督人ID: {invitation.supervisor_user_id}'
            )

            return UseCaseResult.success(data={
                'invitation_id': invitation_id,
                'status': '已撤回',
                'withdrawn_at': datetime.now().isoformat()
            })

        except Exception as e:
            app_logger.error(f'撤回邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'撤回邀请失败: {str(e)}')

    def _notify_withdrawal(self, invitation) -> None:
        """
        通知被邀请人邀请已撤回

        Args:
            invitation: 邀请对象
        """
        from app.infrastructure.persistence.repository_factory import RepositoryFactory

        # 获取被邀请人信息
        user_repository = RepositoryFactory.get_user_repository()
        supervisor = user_repository.find_by_id(invitation.supervisor_user_id)
        if not supervisor:
            app_logger.warning(
                f'无法通知被邀请人：被邀请人不存在, supervisor_user_id={invitation.supervisor_user_id}'
            )
            return

        # 获取邀请人信息
        inviter = user_repository.find_by_id(invitation.solo_user_id)
        if not inviter:
            app_logger.warning(
                f'无法通知被邀请人：邀请人不存在, solo_user_id={invitation.solo_user_id}'
            )
            return

        # TODO: 实现通知逻辑（站内消息、推送等）
        message = f'{inviter.nickname} 撤回了监督邀请'

        app_logger.info(
            f'通知被邀请人已撤回: supervisor={supervisor.nickname}, '
            f'inviter={inviter.nickname}, invitation_id={invitation.relation_id}'
        )