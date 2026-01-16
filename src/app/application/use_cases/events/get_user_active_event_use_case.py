"""
获取用户活跃事件用例
"""
import logging
from sqlalchemy import and_
from sqlalchemy.orm import joinedload

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, CommunityEvent


class GetUserActiveEventUseCase(BaseUseCase):
    """获取用户活跃事件用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

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
            stmt = db.session.execute(
                db.select(CommunityEvent)
                .options(joinedload(CommunityEvent.community))
                .where(
                    and_(
                        CommunityEvent.user_id == user_id,
                        CommunityEvent.status == 1  # 待处理
                    )
                )
                .order_by(CommunityEvent.created_at.desc())
            )
            event = stmt.scalar_one_or_none()

            if not event:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='无活跃事件',
                    data=None
                )

            # 3. 构造事件数据
            event_data = {
                'event_id': event.event_id,
                'user_id': event.user_id,
                'community_id': event.community_id,
                'community_name': event.community.name if event.community else None,
                'event_type': event.event_type,
                'status': event.status,
                'location': event.location,
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