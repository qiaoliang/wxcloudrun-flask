"""
添加事件消息用例
"""
import logging
from datetime import datetime
from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.shared.utils.transaction import transactional
from database.flask_models import db, CommunityEventMessage


class AddEventMessageUseCase(BaseUseCase):
    """添加事件消息用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    @transactional
    def execute(self, event_id: int, user_id: int, message: str, message_type: str = 'text') -> UseCaseResult:
        """
        执行添加事件消息用例

        Args:
            event_id: 事件ID
            user_id: 用户ID
            message: 消息内容
            message_type: 消息类型（text/image/voice）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not event_id or not user_id or not message:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='参数不能为空'
                )

            # 2. 创建事件消息
            event_message = CommunityEventMessage(
                event_id=event_id,
                user_id=user_id,
                message=message,
                message_type=message_type,
                created_at=datetime.now()
            )

            db.session.add(event_message)

            self.logger.info(f'添加事件消息成功: event_id={event_id}, user_id={user_id}')

            # 3. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='添加消息成功',
                data={'message_id': event_message.message_id}
            )

        except Exception as e:
            self.logger.error(f'添加事件消息失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'添加消息失败: {str(e)}'
            )