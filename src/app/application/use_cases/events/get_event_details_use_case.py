"""
获取事件详情用例
"""
import logging

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetEventDetailsUseCase(BaseUseCase):
    """获取事件详情用例"""

    def __init__(self):
        super().__init__()
        self.community_event_repository = RepositoryFactory.get_community_event_repository()
        self.event_message_repository = RepositoryFactory.get_event_message_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(self, event_id: int) -> UseCaseResult:
        """
        执行获取事件详情用例

        Args:
            event_id: 事件ID

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

            # 2. 查询事件
            event = self.community_event_repository.find_by_id(event_id)
            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='事件不存在'
                )

            # 3. 查询目标用户信息
            target_user = None
            if event.target_user_id:
                target_user = self.user_repository.find_by_id(event.target_user_id)

            # 4. 查询事件消息
            messages = self.event_message_repository.find_by_event_id(event_id)
            active_messages = [msg for msg in messages if not msg.is_cancelled]

            # 5. 构造消息列表
            message_list = []
            for msg in active_messages:
                sender = None
                if msg.sender_id:
                    sender = self.user_repository.find_by_id(msg.sender_id)

                message_list.append({
                    'message_id': msg.message_id,
                    'sender_id': msg.sender_id,
                    'sender_name': sender.nickname if sender else None,
                    'sender_avatar': sender.avatar_url if sender else None,
                    'message': msg.message,
                    'created_at': msg.created_at.isoformat() if msg.created_at else None
                })

            # 6. 构造响应数据
            response_data = {
                'event_id': event.event_id,
                'community_id': event.community_id,
                'target_user_id': event.target_user_id,
                'target_user_name': target_user.nickname if target_user else None,
                'target_user_avatar': target_user.avatar_url if target_user else None,
                'event_type': event.event_type,
                'status': event.status,
                'location': event.location,
                'description': event.description,
                'close_reason': event.close_reason,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'updated_at': event.updated_at.isoformat() if event.updated_at else None,
                'closed_at': event.closed_at.isoformat() if event.closed_at else None,
                'messages': message_list,
                'message_count': len(message_list)
            }

            self.logger.info(f'获取事件详情成功: event_id={event_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取事件详情成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'获取事件详情失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取事件详情失败: {str(e)}'
            )