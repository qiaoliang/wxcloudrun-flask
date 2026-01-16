"""
生成认证Token用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GenerateAuthTokensUseCase(BaseUseCase):
    """生成认证Token用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user) -> UseCaseResult:
        """
        执行生成认证Token用例

        Args:
            user: 用户对象

        Returns:
            UseCaseResult: 执行结果，包含 token 和 refresh_token
        """
        try:
            # 1. 生成 JWT token
            self.logger.info('开始生成JWT token...')
            token, error_response = generate_jwt_token(user, expires_hours=2)
            if error_response:
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='生成JWT token失败',
                    data={'error_response': error_response}
                )

            # 2. 生成 refresh token
            refresh_token = generate_refresh_token(user, expires_days=7)

            # 3. 更新用户信息（保存 refresh token）
            from app.application.use_cases.user import UpdateUserUseCase
            update_use_case = UpdateUserUseCase()
            update_result = update_use_case.execute(user)
            if not update_result.is_success:
                self.logger.warning(f'更新用户信息失败: {update_result.message}')

            self.logger.info('保存refresh token到数据库...')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='生成认证Token成功',
                data={
                    'token': token,
                    'refresh_token': refresh_token
                }
            )

        except Exception as e:
            self.logger.error(f'生成认证Token失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'生成认证Token失败: {str(e)}'
            )