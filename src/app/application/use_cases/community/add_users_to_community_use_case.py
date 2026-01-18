"""
from app.shared.utils.transaction import transactional
批量添加用户到社区用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from datetime import datetime


class AddUsersToCommunityUseCase(BaseUseCase):
    """批量添加用户到社区用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()

    @transactional


    def execute(self, community_id: int, user_ids: list) -> UseCaseResult:
        """
        批量添加用户到社区

        Args:
            community_id: 社区ID
            user_ids: 用户ID列表

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if not community_id or not user_ids:
                return UseCaseResult.fail("参数不能为空")

            # 更新用户的社区ID
            updated_count = 0
            for user_id in user_ids:
                # ✅ 使用Repository代替 db.session.get(User, user_id)
                user = self.user_repository.find_by_id(user_id)
                if user and user.community_id != community_id:
                    user.community_id = community_id
                    user.community_joined_at = datetime.now()
                    # ✅ 使用Repository保存
                    self.user_repository.save(user)
                    updated_count += 1

            if updated_count == 0:
                return UseCaseResult.fail("未找到用户或用户已在社区中")

            return UseCaseResult.success({
                'community_id': community_id,
                'updated_count': updated_count
            }, f"成功添加 {updated_count} 个用户到社区")

        except Exception as e:
            return UseCaseResult.fail(f"添加用户失败: {str(e)}")
