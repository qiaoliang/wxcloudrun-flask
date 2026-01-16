"""
通过ID查询用户用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserByIdUseCase(BaseUseCase):
    """通过ID查询用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()

    def _validate(self, user_id: int) -> UseCaseResult:
        """验证参数"""
        if not user_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='用户ID不能为空'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, user_id: int) -> UseCaseResult:
        """
        执行查询用户逻辑

        Args:
            user_id: 用户ID

        Returns:
            UseCaseResult: 执行结果，包含用户对象
        """
        try:
            user = self.user_repository.find_by_id(user_id)

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            self.logger.info(f'查询用户成功: user_id={user_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='查询成功',
                data=user
            )

        except Exception as e:
            self.logger.error(f'查询用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'查询失败: {str(e)}'
            )