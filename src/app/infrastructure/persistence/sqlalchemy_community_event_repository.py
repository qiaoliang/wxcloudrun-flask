"""
社区事件仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from database.flask_models import db, CommunityEvent
from app.domain.repositories.community_event_repository import CommunityEventRepository


class SQLAlchemyCommunityEventRepository(CommunityEventRepository):
    """社区事件仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, event_id: int) -> Optional[CommunityEvent]:
        """根据ID查找社区事件"""
        return self.session.get(CommunityEvent, event_id)

    def find_by_community_id(
        self, 
        community_id: int, 
        status: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> List[CommunityEvent]:
        """根据社区ID查找事件"""
        stmt = select(CommunityEvent).where(CommunityEvent.community_id == community_id)
        
        if status is not None:
            stmt = stmt.where(CommunityEvent.status == status)
        
        if event_type is not None:
            stmt = stmt.where(CommunityEvent.event_type == event_type)
        
        stmt = stmt.order_by(CommunityEvent.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_target_user_id(
        self, 
        target_user_id: int, 
        status: Optional[int] = None
    ) -> List[CommunityEvent]:
        """根据目标用户ID查找事件"""
        stmt = select(CommunityEvent).where(CommunityEvent.target_user_id == target_user_id)
        
        if status is not None:
            stmt = stmt.where(CommunityEvent.status == status)
        
        stmt = stmt.order_by(CommunityEvent.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_creator_id(
        self, 
        creator_id: int, 
        status: Optional[int] = None
    ) -> List[CommunityEvent]:
        """根据创建者ID查找事件"""
        stmt = select(CommunityEvent).where(CommunityEvent.created_by == creator_id)
        
        if status is not None:
            stmt = stmt.where(CommunityEvent.status == status)
        
        stmt = stmt.order_by(CommunityEvent.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_pending_events(self, community_id: int) -> List[CommunityEvent]:
        """查找社区未处理的事件"""
        return self.find_by_community_id(community_id, status=1)  # 1=进行中

    def find_ongoing_events(self, community_id: int) -> List[CommunityEvent]:
        """查找社区进行中的事件"""
        return self.find_by_community_id(community_id, status=1)  # 1=进行中

    def find_events_by_date_range(
        self, 
        community_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[CommunityEvent]:
        """查找指定日期范围内的事件"""
        stmt = select(CommunityEvent).where(
            and_(
                CommunityEvent.community_id == community_id,
                CommunityEvent.created_at >= datetime.combine(start_date, datetime.min.time()),
                CommunityEvent.created_at <= datetime.combine(end_date, datetime.max.time())
            )
        )
        stmt = stmt.order_by(CommunityEvent.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def save(self, event: CommunityEvent) -> CommunityEvent:
        """保存社区事件"""
        self.session.add(event)
        self.session.flush()
        return event

    def update(self, event: CommunityEvent) -> CommunityEvent:
        """更新社区事件"""
        self.session.merge(event)
        self.session.flush()
        return event

    def delete(self, event_id: int) -> bool:
        """删除社区事件"""
        event = self.find_by_id(event_id)
        if event:
            self.session.delete(event)
            self.session.flush()
            return True
        return False

    def close_event(
        self, 
        event_id: int, 
        closed_by: int, 
        closure_type: int, 
        closure_reason: Optional[str] = None
    ) -> bool:
        """关闭事件"""
        event = self.find_by_id(event_id)
        if event:
            event.status = 2  # 2=已完成
            event.closed_by = closed_by
            event.closed_at = datetime.now()
            event.closure_type = closure_type
            event.closure_reason = closure_reason
            self.session.flush()
            return True
        return False

    def count_by_community_id(self, community_id: int, status: Optional[int] = None) -> int:
        """统计社区事件数量"""
        stmt = select(CommunityEvent).where(CommunityEvent.community_id == community_id)
        
        if status is not None:
            stmt = stmt.where(CommunityEvent.status == status)
        
        return len(list(self.session.execute(stmt).scalars().all()))

    def batch_transfer_events(
        self,
        source_community_id: int,
        target_community_id: int,
        user_ids: List[int],
        status: Optional[int] = None
    ) -> int:
        """
        批量转移事件到目标社区

        Args:
            source_community_id: 源社区ID
            target_community_id: 目标社区ID
            user_ids: 用户ID列表
            status: 事件状态（可选，默认只转移进行中的事件）

        Returns:
            int: 转移的事件数量
        """
        from sqlalchemy import update

        stmt = update(CommunityEvent).where(
            CommunityEvent.community_id == source_community_id,
            CommunityEvent.target_user_id.in_(user_ids)
        )

        if status is not None:
            stmt = stmt.where(CommunityEvent.status == status)

        stmt = stmt.values(
            {'community_id': target_community_id}
        )

        result = self.session.execute(stmt)
        return result.rowcount