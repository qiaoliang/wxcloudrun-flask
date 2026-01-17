"""
获取社区未处理的求助事件用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetPendingEventsUseCase(BaseUseCase):
    """获取社区未处理的求助事件用例"""

    def __init__(self):
        """
        初始化用例，注入Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.community_repository = RepositoryFactory.get_community_repository()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()

    def execute(self, community_id: int) -> UseCaseResult:
        """
        执行获取社区未处理的求助事件用例

        Args:
            community_id: 社区ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not community_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='社区ID不能为空'
                )

            # 2. 验证社区是否存在
            community = self.community_repository.find_by_id(community_id)
            if not community:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='社区不存在'
                )

            # 3. 查询未处理的call_for_help类型事件
            # ✅ 使用Repository代替 db.session.execute(select(CommunityEvent)...)
            events = self.community_event_repository.find_by_community_id(
                community_id,
                status=1,  # 待处理
                event_type='call_for_help'
            )

            # 4. 构造响应数据
            event_list = []
            for event in events:
                event_list.append({
                    'event_id': event.event_id,
                    'community_id': event.community_id,
                    'target_user_id': event.target_user_id,
                    'event_type': event.event_type,
                    'status': event.status,
                    'location': event.location,
                    'description': event.description,
                    'created_at': event.created_at.isoformat() if event.created_at else None,
                    'updated_at': event.updated_at.isoformat() if event.updated_at else None
                })

            self.logger.info(f'获取未处理事件成功: community_id={community_id}, count={len(event_list)}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取未处理事件成功',
                data={
                    'events': event_list,
                    'count': len(event_list)
                }
            )

        except Exception as e:
            self.logger.error(f'获取未处理事件失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取未处理事件失败: {str(e)}'
            )