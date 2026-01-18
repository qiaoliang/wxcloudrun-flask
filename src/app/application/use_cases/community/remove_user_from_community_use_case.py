"""
从社区移除用户用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class RemoveUserFromCommunityUseCase(BaseUseCase):
    """从社区移除用户用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()

    @transactional


    def execute(self, community_id: int, target_user_id: int) -> UseCaseResult:
        """
        从社区移除用户

        Args:
            community_id: 社区ID
            target_user_id: 目标用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
from app.shared.utils.transaction import transactional
            if not community_id or not target_user_id:
                return UseCaseResult.fail("参数不能为空")

            # ✅ 使用Repository代替 db.session.get(User, target_user_id)
            user = self.user_repository.find_by_id(target_user_id)

            if not user:
                return UseCaseResult.fail("用户不存在")

            # 检查用户是否属于该社区
            if user.community_id != community_id:
                return UseCaseResult.fail("用户不属于该社区")

            # 移除用户（将 community_id 设为 None）
            user.community_id = None
            # ✅ 使用Repository保存
            self.user_repository.save(user)

            return UseCaseResult.success({
                'user_id': target_user_id,
                'community_id': community_id
            }, "移除用户成功")

        except Exception as e:
            return UseCaseResult.fail(f"移除用户失败: {str(e)}")
