"""
Outbox 仓储的 SQLAlchemy 实现

提供 Outbox 事件的持久化操作，使用 Flask-SQLAlchemy。
"""
from typing import List
from datetime import datetime
from sqlalchemy import select, and_

from app.domain.entities.outbox_event_entity import OutboxEventEntity
from app.domain.repositories.outbox_repository import OutboxRepository
from app.domain.enums.outbox_status import OutboxStatus
from database.flask_models import OutboxEvent
from app.extensions import db


class SQLAlchemyOutboxRepository(OutboxRepository):
    """Outbox 仓储的 SQLAlchemy 实现"""

    def save(self, event: OutboxEventEntity) -> OutboxEventEntity:
        """
        保存事件到 Outbox

        Args:
            event: Outbox 事件实体

        Returns:
            OutboxEventEntity: 保存后的实体（带 ID）
        """
        orm_model = OutboxEvent(
            event_type=event.event_type,
            payload=event.payload,
            status=event.status.value,
            retry_count=event.retry_count,
            created_at=event.created_at,
            next_retry_at=event.next_retry_at
        )

        with db.session.begin():
            db.session.add(orm_model)
            db.session.flush()  # 获取 ID

        # 转换回领域实体
        return self._to_entity(orm_model)

    def find_pending_events(self, limit: int = 100) -> List[OutboxEventEntity]:
        """
        查找待处理事件

        Args:
            limit: 最大返回数量

        Returns:
            List[OutboxEventEntity]: 待处理事件列表
        """
        now = datetime.now()

        stmt = select(OutboxEvent).where(
            and_(
                OutboxEvent.status == OutboxStatus.PENDING.value,
                OutboxEvent.next_retry_at <= now
            )
        ).order_by(
            OutboxEvent.created_at
        ).limit(limit)

        orm_models = db.session.execute(stmt).scalars().all()

        return [self._to_entity(model) for model in orm_models]

    def update_status(self, event_id: int, status: OutboxStatus) -> None:
        """
        更新事件状态

        Args:
            event_id: 事件 ID
            status: 新状态
        """
        stmt = select(OutboxEvent).where(OutboxEvent.id == event_id)

        orm_model = db.session.execute(stmt).scalar_one()
        orm_model.status = status.value

        if status == OutboxStatus.PUBLISHED:
            orm_model.published_at = datetime.now()

        db.session.commit()

    def _to_entity(self, orm_model: OutboxEvent) -> OutboxEventEntity:
        """
        转换为领域实体

        Args:
            orm_model: ORM 模型

        Returns:
            OutboxEventEntity: 领域实体
        """
        entity = OutboxEventEntity(
            event_type=orm_model.event_type,
            payload=orm_model.payload
        )
        entity.id = orm_model.id
        entity.status = OutboxStatus(orm_model.status)
        entity.retry_count = orm_model.retry_count
        entity.created_at = orm_model.created_at
        entity.published_at = orm_model.published_at
        entity.next_retry_at = orm_model.next_retry_at
        return entity
