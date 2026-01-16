"""
获取当前用户用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCurrentUserUseCase(BaseUseCase):
    """获取当前用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取当前用户用例

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

            # 2. 查询用户
            user = self.user_repository.find_by_id(user_id)

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取用户成功',
                data=user
            )

        except Exception as e:
            self.logger.error(f'获取当前用户失败: user_id={user_id}, error={str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取当前用户失败: {str(e)}'
            )