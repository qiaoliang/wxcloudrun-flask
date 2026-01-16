"""
根据手机号哈希获取用户用例
"""
import logging
from sqlalchemy.orm import joinedload

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User


class GetUserByPhoneHashUseCase(BaseUseCase):
    """根据手机号哈希获取用户用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(self, phone_hash: str) -> UseCaseResult:
        """
        执行根据手机号哈希获取用户用例

        Args:
            phone_hash: 手机号哈希值

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not phone_hash:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='手机号哈希不能为空'
                )

            # 2. 查询用户（包含社区关联）
            stmt = db.session.execute(
                db.select(User).options(joinedload(User.community)).where(User.phone_hash == phone_hash)
            )
            user = stmt.scalar_one_or_none()

            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 构造用户数据
            user_data = {
                'user_id': user.user_id,
                'wechat_openid': user.wechat_openid,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'name': user.name,
                'avatar_url': user.avatar_url,
                'address': user.address,
                'motto': user.motto,
                'emergency_contact_name': user.emergency_contact_name,
                'emergency_contact_phone': user.emergency_contact_phone,
                'emergency_contact_address': user.emergency_contact_address,
                'role': user.role,
                'role_name': user.role_name,
                'community_id': user.community_id,
                'community_name': user.community.name if user.community else None,
                'status': user.status,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'updated_at': user.updated_at.isoformat() if user.updated_at else None
            }

            self.logger.info(f'根据手机号哈希获取用户成功: phone_hash={phone_hash}, user_id={user.user_id}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取用户成功',
                data=user_data
            )

        except Exception as e:
            self.logger.error(f'根据手机号哈希获取用户失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取用户失败: {str(e)}'
            )