"""
生成认证Token用例（重构后 - 符合DDD架构）

重构要点：
- 移除对 UpdateUserUseCase 的调用
- 将更新令牌的逻辑内联到 UseCase 中
- 符合 DDD 原则，UseCase 之间不应相互调用
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.shared.utils.auth import generate_jwt_token, generate_refresh_token
from app.shared.utils.transaction import transactional
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GenerateAuthTokensUseCase(BaseUseCase):
    """生成认证Token用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    @transactional
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

            # 3. ✅ 直接更新用户令牌，不调用其他 UseCase
            self.user_repository.save(user)

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