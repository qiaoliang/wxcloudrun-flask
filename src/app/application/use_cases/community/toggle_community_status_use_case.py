"""
from app.shared.utils.transaction import transactional
切换社区状态用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, Community
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""

from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class ToggleCommunityStatusUseCase(BaseUseCase):
    """切换社区状态用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        # ✅ 通过RepositoryFactory获取Repository接口
        self.community_repository = RepositoryFactory.get_community_repository()

    @transactional


    def execute(self, community_id: int, status: int) -> UseCaseResult:
        """
        切换社区状态

        Args:
            community_id: 社区ID
            status: 状态 (1=正常, 0=禁用)

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if not community_id or status is None:
                return UseCaseResult.fail("参数不能为空")

            # ✅ 使用Repository代替 db.session.execute(db.select(Community)...)
            community = self.community_repository.find_by_id(community_id)

            if not community:
                return UseCaseResult.fail("社区不存在")

            # 更新状态
            community.status = status
            # ✅ 使用Repository保存
            self.community_repository.save(community)

            return UseCaseResult.success({
                'community_id': community_id,
                'status': status
            }, "状态更新成功")

        except Exception as e:
            return UseCaseResult.fail(f"状态更新失败: {str(e)}")
