"""
检查过期邀请UseCase
用于定时任务检查并更新过期的邀请
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory

logger = logging.getLogger(__name__)


class CheckExpiredInvitationsUseCase(BaseUseCase):
    """检查过期邀请用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(self) -> UseCaseResult:
        """执行邀请过期检查

        Returns:
            UseCaseResult: 包含统计信息
        """
        try:
            self.logger.info("开始执行邀请过期检查任务")

            # 查找所有已过期的邀请
            expired_invitations = self.supervision_relation_repository.find_expired_invitations()

            if expired_invitations:
                # 提取所有过期邀请的ID
                expired_ids = [inv.relation_id for inv in expired_invitations]

                # 批量更新状态为已过期（status=4）
                updated_count = self.supervision_relation_repository.batch_update_status(expired_ids, 4)

                self.logger.info(f"邀请过期检查完成: 更新了 {updated_count} 个过期邀请")
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='邀请过期检查完成',
                    data={'updated_count': updated_count, 'expired_count': len(expired_invitations)}
                )
            else:
                self.logger.info("邀请过期检查完成: 没有找到过期的邀请")
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='邀请过期检查完成',
                    data={'updated_count': 0, 'expired_count': 0}
                )

        except Exception as e:
            self.logger.error(f"邀请过期检查任务执行失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'邀请过期检查失败: {str(e)}',
                data={'errors': 1}
            )