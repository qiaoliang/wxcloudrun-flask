"""
根据微信 OpenID 获取用户用例
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from database.flask_models import db, User
from sqlalchemy.orm import joinedload


class GetUserByOpenidUseCase(BaseUseCase):
    """根据微信 OpenID 获取用户用例"""

    def execute(self, openid: str) -> UseCaseResult:
        """
        根据微信 OpenID 获取用户

        Args:
            openid: 微信 OpenID

        Returns:
            UseCaseResult: 包含用户信息或错误信息
        """
        try:
            if not openid:
                return UseCaseResult.fail("微信 OpenID 不能为空")

            # 查询用户
            stmt = db.session.execute(
                db.select(User).options(joinedload(User.community)).where(User.wechat_openid == openid)
            )
            user = stmt.scalar_one_or_none()

            if not user:
                return UseCaseResult.fail("用户不存在")

            # 构造返回数据
            user_data = {
                'user_id': user.user_id,
                'phone_number': user.phone_number,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url,
                'name': user.name,
                'role': user.role,
                'role_name': user.role_name,
                'wechat_openid': user.wechat_openid,
                'community_id': user.community_id,
                'community': {
                    'community_id': user.community.community_id,
                    'name': user.community.name
                } if user.community else None
            }

            return UseCaseResult.success(user_data, "获取用户信息成功")

        except Exception as e:
            return UseCaseResult.fail(f"获取用户信息失败: {str(e)}")