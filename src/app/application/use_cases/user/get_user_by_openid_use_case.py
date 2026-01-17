"""
根据微信 OpenID 获取用户用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db
- 使用UserRepository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserByOpenidUseCase(BaseUseCase):
    """根据微信 OpenID 获取用户用例"""

    def __init__(self):
        """
        初始化用例，注入UserRepository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取UserRepository接口
        self.user_repository = RepositoryFactory.get_user_repository()

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
            # ✅ 使用Repository代替 db.session.execute(select(User)...)
            user = self.user_repository.find_by_openid(openid)

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