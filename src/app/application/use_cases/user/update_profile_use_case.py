"""
更新用户资料用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.user_entity import UserEntity
from app.domain.aggregates.user_aggregate import UserAggregate
from app.domain.events.event_bus import EventBus
from app.domain.repositories.user_repository import UserRepository


class UpdateProfileUseCase(BaseUseCase):
    """更新用户资料用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.event_bus = EventBus()

    @transactional


    def execute(
        self,
        user_id: int,
        nickname: str = None,
        name: str = None,
        avatar_url: str = None
    ) -> UseCaseResult:
        """
        执行更新用户资料用例

        Args:
            user_id: 用户ID
            nickname: 昵称
            name: 姓名
            avatar_url: 头像URL

        Returns:
            UseCaseResult: 执行结果
        """
        try:
from app.shared.utils.transaction import transactional
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 创建用户聚合根
            user_entity = UserEntity(user)
            user_aggregate = UserAggregate(user_entity)

            # 4. 更新用户信息
            if nickname is not None:
                if not nickname or not nickname.strip():
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='昵称不能为空'
                    )
                user_aggregate.update_profile(nickname=nickname.strip())

            if name is not None:
                user_aggregate.update_profile(name=name.strip() if name else None)

            if avatar_url is not None:
                user_aggregate.update_profile(avatar_url=avatar_url.strip() if avatar_url else None)

            # 5. 保存更新
            updated_user = self.user_repository.save(user)

            # 6. 发布领域事件
            for event in user_aggregate.domain_events:
                self.event_bus.publish(event)
            user_aggregate.clear_domain_events()

            self.logger.info(f'更新用户资料成功: user_id={user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='用户资料更新成功',
                data={
                    'user_id': updated_user.user_id,
                    'nickname': updated_user.nickname,
                    'name': updated_user.name,
                    'avatar_url': updated_user.avatar_url,
                    'phone_number': updated_user.phone_number
                }
            )

        except Exception as e:
            self.logger.error(f'更新用户资料失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新用户资料失败: {str(e)}'
            )