"""
更新用户信息用例
"""
import logging
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.shared.utils.transaction import transactional
from database.flask_models import db, User


class UpdateUserUseCase(BaseUseCase):
    """更新用户信息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @transactional
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
            stmt = db.session.execute(
                db.select(User).where(User.user_id == user.user_id)
            )
            existing_user = stmt.scalar_one_or_none()

            if not existing_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 更新字段
            if user.nickname is not None:
                existing_user.nickname = user.nickname
            if user.avatar_url is not None:
                existing_user.avatar_url = user.avatar_url
            if user.name is not None:
                existing_user.name = user.name
            if user.work_id is not None:
                existing_user.work_id = user.work_id
            if user.phone_number is not None:
                existing_user.phone_number = user.phone_number
            if user.address is not None:
                existing_user.address = user.address
            if user.motto is not None:
                existing_user.motto = user.motto
            if user.emergency_contact_name is not None:
                existing_user.emergency_contact_name = user.emergency_contact_name
            if user.emergency_contact_phone is not None:
                existing_user.emergency_contact_phone = user.emergency_contact_phone
            if user.emergency_contact_address is not None:
                existing_user.emergency_contact_address = user.emergency_contact_address

            self.logger.info(f'更新用户信息成功: user_id={user.user_id}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='更新用户信息成功',
                data={'user_id': existing_user.user_id}
            )

        except Exception as e:
            self.logger.error(f'更新用户信息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'更新用户信息失败: {str(e)}'
            )