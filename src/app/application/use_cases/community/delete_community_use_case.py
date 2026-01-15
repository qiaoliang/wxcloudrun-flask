"""
删除社区用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.community_events import CommunityDeletedEvent
from app.domain.events.event_bus import EventBus


class DeleteCommunityUseCase(BaseUseCase):
    """删除社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.community_repository = RepositoryFactory.get_community_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, community_id: int, user_id: int) -> UseCaseResult:
        """
        执行删除社区用例

        Args:
            community_id: 社区ID
            user_id: 用户ID（用于权限验证）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询社区
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 验证权限（只有创建者或超级管理员可以删除）
            if community.creator_id != user_id:
                user = self.user_repository.find_by_id(user_id)
                if not user or user.role != 4:  # 不是超级管理员
                    return UseCaseResult(
                        status=UseCaseStatus.UNAUTHORIZED,
                        message='无权删除此社区'
                    )

            # 4. 检查社区是否有用户
            users = self.user_repository.find_by_community_id(community_id)
            if users:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='社区中还有用户，无法删除'
                )

            # 5. 删除社区
            community_name = community.name
            self.community_repository.delete(community)

            self.logger.info(f'删除社区成功: community_id={community_id}')

            # 6. 发布领域事件
            event = CommunityDeletedEvent(
                community_id=community_id,
                deleter_id=user_id,
                community_name=community_name
            )
            EventBus.publish(event)

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='社区删除成功',
                data={
                    'community_id': community_id
                }
            )

        except Exception as e:
            self.logger.error(f'删除社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'删除社区失败: {str(e)}'
            )