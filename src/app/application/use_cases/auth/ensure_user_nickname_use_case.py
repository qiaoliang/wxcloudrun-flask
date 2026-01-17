"""
确保用户昵称用例（重构后 - 符合DDD架构）

重构要点：
- 移除对 UpdateUserUseCase 的调用
- 将更新昵称的逻辑内联到 UseCase 中
- 符合 DDD 原则，UseCase 之间不应相互调用
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class EnsureUserNicknameUseCase(BaseUseCase):
    """确保用户昵称用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user) -> UseCaseResult:
        """
        执行确保用户昵称用例

        Args:
            user: 用户对象

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 检查用户是否有昵称
            if not user.nickname:
                # 生成默认昵称
                from wxcloudrun.utils.validators import _gen_phone_nickname
                user.nickname = _gen_phone_nickname()

                # ✅ 直接更新用户，不调用其他 UseCase
                self.user_repository.save(user)

                self.logger.info(f'已更新用户昵称: {user.nickname}')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='用户昵称已更新',
                    data={'nickname': user.nickname}
                )
            else:
                self.logger.info(f'用户已有昵称: {user.nickname}')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='用户已有昵称',
                    data={'nickname': user.nickname}
                )

        except Exception as e:
            self.logger.error(f'确保用户昵称失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'确保用户昵称失败: {str(e)}'
            )