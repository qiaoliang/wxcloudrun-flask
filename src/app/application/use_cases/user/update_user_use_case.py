"""
更新用户信息用例
"""
import logging
from database.flask_models import User

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.user_entity import UserEntity
from app.domain.aggregates.user_aggregate import UserAggregate
from app.domain.events.event_bus import EventBus


class UpdateUserUseCase(BaseUseCase):
    """更新用户信息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.event_bus = EventBus()

    def execute(self, user: User) -> UseCaseResult:
        """
        执行更新用户信息用例

        Args:
            user: 用户实体

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user or not user.user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户或用户ID不能为空'
                )

            # 2. 查询现有用户
            existing_user = self.user_repository.find_by_id(user.user_id)
            if not existing_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 创建用户聚合根
            user_entity = UserEntity(existing_user)
            user_aggregate = UserAggregate(user_entity)

            # 4. 更新字段（业务规则在聚合根内）
            if user.nickname is not None:
                user_aggregate.update_profile(nickname=user.nickname)
            if user.avatar_url is not None:
                user_aggregate.update_profile(avatar_url=user.avatar_url)
            if user.name is not None:
                user_aggregate.update_profile(name=user.name)
            if user.address is not None:
                user_aggregate.update_profile(address=user.address)
            if user.motto is not None:
                user_aggregate.update_profile(motto=user.motto)

            # 5. 保存更新
            updated_user = self.user_repository.save(existing_user)

            # 6. 发布领域事件
            for event in user_aggregate.domain_events:
                self.event_bus.publish(event)
            user_aggregate.clear_domain_events()

            self.logger.info(f'更新用户信息成功: user_id={user.user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='更新用户信息成功',
                data={'user_id': updated_user.user_id}
            )

        except Exception as e:
            self.logger.error(f'更新用户信息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新用户信息失败: {str(e)}'
            )