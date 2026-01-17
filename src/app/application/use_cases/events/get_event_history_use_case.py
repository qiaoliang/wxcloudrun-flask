"""
获取事件历史记录用例
"""
import logging
# from sqlalchemy.orm import joinedload  # 不再需要，使用Repository
from app.infrastructure.persistence.repository_factory import RepositoryFactory

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
# 移除db导入，使用Repository代替


class GetEventHistoryUseCase(BaseUseCase):
    """获取事件历史记录用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.event_message_repository = RepositoryFactory.get_event_message_repository()

    def execute(self, event_id: int, limit: int = 50) -> UseCaseResult:
        """
        执行获取事件历史记录用例

        Args:
            event_id: 事件ID
            limit: 返回记录数量限制

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not event_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='事件ID不能为空'
                )

            # 2. 查询事件消息
            messages = self.event_message_repository.find_by_event_id(event_id, limit)

            # 3. 构造消息列表
            messages_data = []
            for msg in messages:
                messages_data.append({
                    'message_id': msg.message_id,
                    'event_id': msg.event_id,
                    'sender_id': msg.sender_id,
                    'message_content': msg.message_content,
                    'message_type': msg.message_type,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                })

            self.logger.info(f'获取事件历史记录成功: event_id={event_id}, count={len(messages_data)}')

            # 4. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取历史记录成功',
                data={'messages': messages_data, 'count': len(messages_data)}
            )

        except Exception as e:
            self.logger.error(f'获取事件历史记录失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取历史记录失败: {str(e)}'
            )