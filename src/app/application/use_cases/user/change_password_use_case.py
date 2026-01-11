"""
修改密码用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.domain.entities.user_entity import UserEntity


class ChangePasswordUseCase(BaseUseCase):
    """修改密码用例"""

    def __init__(self):
        super().__init__()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user_id: int, old_password: str, new_password: str) -> UseCaseResult:
        """
        执行修改密码用例

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

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

            if not old_password:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='旧密码不能为空'
                )

            if not new_password:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='新密码不能为空'
                )

            # 验证新密码强度
            if len(new_password) < 8:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='新密码长度不能少于8位'
                )

            if not any(c.isalpha() for c in new_password) or not any(c.isdigit() for c in new_password):
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='新密码必须包含字母和数字'
                )

            # 2. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 验证旧密码
            user_entity = UserEntity(user)
            if not user_entity.verify_password(old_password):
                return UseCaseResult(
                    status=UseCaseStatus.UNAUTHORIZED,
                    message='旧密码错误'
                )

            # 4. 设置新密码
            user_entity.set_password(new_password)

            # 5. 保存更新
            self.user_repository.save(user)

            self.logger.info(f'修改密码成功: user_id={user_id}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='密码修改成功',
                data={
                    'user_id': user_id
                }
            )

        except Exception as e:
            self.logger.error(f'修改密码失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'修改密码失败: {str(e)}'
            )