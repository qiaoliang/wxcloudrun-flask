"""
离开社区用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.events.community_events import CommunityMemberRemovedEvent
from app.domain.events.event_bus import EventBus
from database.flask_models import User


class LeaveCommunityUseCase(BaseUseCase):
    """离开社区用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行离开社区用例

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 检查用户是否在社区
            if not user.community_id:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='用户不在任何社区'
                )

            old_community_id = user.community_id

            # 4. 清除用户的社区ID
            user.community_id = None
            updated_user = self.user_repository.save(user)

            self.logger.info(f'用户 {user_id} 已离开社区 {old_community_id}')

            # 5. 发布领域事件
            event = CommunityMemberRemovedEvent(
                community_id=old_community_id,
                user_id=user_id,
                role=user.role
            )
            EventBus.publish(event)

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='离开社区成功',
                data={
                    'user_id': updated_user.user_id,
                    'old_community_id': old_community_id
                }
            )

        except ValueError as e:
            self.logger.error(f'离开社区失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'离开社区失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'离开社区失败: {str(e)}'
            )