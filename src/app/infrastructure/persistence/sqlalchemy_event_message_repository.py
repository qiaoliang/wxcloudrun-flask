"""
事件消息仓储 SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, EventMessage
from app.domain.repositories.event_message_repository import EventMessageRepository


class SQLAlchemyEventMessageRepository(EventMessageRepository):
    """事件消息仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, message_id: int) -> Optional[EventMessage]:
        """根据ID查找事件消息"""
        return self.session.get(EventMessage, message_id)

    def find_by_event_id(self, event_id: int, limit: int = None) -> List[EventMessage]:
        """根据事件ID查找消息"""
        stmt = select(EventMessage).where(EventMessage.event_id == event_id)
        stmt = stmt.order_by(EventMessage.created_at.asc())
        if limit:
            stmt = stmt.limit(limit)
        return list(self.session.execute(stmt).scalars().all())

    def find_by_sender_id(self, sender_id: int) -> List[EventMessage]:
        """根据发送者ID查找消息"""
        stmt = select(EventMessage).where(EventMessage.sender_id == sender_id)
        stmt = stmt.order_by(EventMessage.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_active_by_event_id(self, event_id: int) -> List[EventMessage]:
        """查找事件的有效消息"""
        stmt = select(EventMessage).where(
            EventMessage.event_id == event_id,
            EventMessage.status == 1  # 1=有效
        )
        stmt = stmt.order_by(EventMessage.created_at.asc())
        return list(self.session.execute(stmt).scalars().all())

    def save(self, message: EventMessage) -> EventMessage:
        """保存事件消息"""
        self.session.add(message)
        self.session.flush()
        return message

    def update(self, message: EventMessage) -> EventMessage:
        """更新事件消息"""
        self.session.merge(message)
        self.session.flush()
        return message

    def delete(self, message_id: int) -> bool:
        """删除事件消息"""
        message = self.find_by_id(message_id)
        if message:
            self.session.delete(message)
            self.session.flush()
            return True
        return False

    def cancel(self, message_id: int) -> bool:
        """取消事件消息"""
        message = self.find_by_id(message_id)
        if message:
            message.status = 2  # 2=已取消
            self.session.flush()
            return True
        return False

    def count_by_event_id(self, event_id: int) -> int:
        """统计事件消息数量"""
        stmt = select(EventMessage).where(EventMessage.event_id == event_id)
        return len(list(self.session.execute(stmt).scalars().all()))

    def count_active_by_event_id(self, event_id: int) -> int:
        """统计事件有效消息数量"""
        stmt = select(EventMessage).where(
            EventMessage.event_id == event_id,
            EventMessage.status == 1  # 1=有效
        )
        return len(list(self.session.execute(stmt).scalars().all()))