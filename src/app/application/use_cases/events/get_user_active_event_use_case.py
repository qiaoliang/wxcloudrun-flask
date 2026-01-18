"""
获取用户活跃事件用例（重构后 - 符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db
- 使用Repository接口访问数据，符合依赖倒置原则（DIP）
- 所有数据库操作通过Repository抽象层
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetUserActiveEventUseCase(BaseUseCase):
    """获取用户活跃事件用例"""

    def __init__(self):
        """
        初始化用例，注入Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, user_id: int) -> UseCaseResult:
        """
        执行获取用户活跃事件用例

        Args:
            user_id: 用户ID

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

            # 2. 查询用户活跃事件（状态为1的待处理事件）
            # ✅ 使用Repository代替 db.session.execute(select(CommunityEvent)...)
            # 注意：这里使用target_user_id而不是user_id
            events = self.community_event_repository.find_by_target_user_id(user_id, status=1)

            if not events:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='无活跃事件',
                    data=None
                )

            event = events[0]  # 取第一个（最新的）

            # 3. 获取创建者信息
            creator_user = self.user_repository.find_by_id(event.created_by)
            creator_nickname = creator_user.nickname if creator_user else "未知用户"

            # 4. 构造事件数据
            event_data = {
                'event_id': event.event_id,
                'target_user_id': event.target_user_id,
                'community_id': event.community_id,
                'event_type': event.event_type,
                'title': event.title,  # 添加 title
                'description': event.description,
                'status': event.status,
                'location': event.location,
                'created_by': event.created_by,  # 添加创建者ID
                'creator_nickname': creator_nickname,  # 添加创建者昵称
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'updated_at': event.updated_at.isoformat() if event.updated_at else None
            }

            self.logger.info(f'获取用户活跃事件成功: user_id={user_id}, event_id={event.event_id}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取活跃事件成功',
                data=event_data
            )

        except Exception as e:
            self.logger.error(f'获取用户活跃事件失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取活跃事件失败: {str(e)}'
            )