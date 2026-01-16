"""
确保用户昵称用例
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

                # 更新用户信息
                from app.application.use_cases.user import UpdateUserUseCase
                update_use_case = UpdateUserUseCase()
                update_result = update_use_case.execute(user)

                if not update_result.is_success:
                    self.logger.warning(f'更新用户昵称失败: {update_result.message}')
                    return UseCaseResult(
                        status=UseCaseStatus.FAILURE,
                        message='更新用户昵称失败',
                        data={'error': update_result.message}
                    )
                else:
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