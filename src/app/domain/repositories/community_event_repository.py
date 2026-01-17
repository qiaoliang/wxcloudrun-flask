"""
社区事件仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, date

from database.flask_models import CommunityEvent


class CommunityEventRepository(ABC):
    """社区事件仓储接口"""

    @abstractmethod
    def find_by_id(self, event_id: int) -> Optional[CommunityEvent]:
        """根据ID查找社区事件"""
        pass

    @abstractmethod
    def find_by_community_id(
        self, 
        community_id: int, 
        status: Optional[int] = None,
        event_type: Optional[str] = None
    ) -> List[CommunityEvent]:
        """根据社区ID查找事件"""
        pass

    @abstractmethod
    def find_by_target_user_id(
        self, 
        target_user_id: int, 
        status: Optional[int] = None
    ) -> List[CommunityEvent]:
        """根据目标用户ID查找事件"""
        pass

    @abstractmethod
    def find_by_creator_id(
        self, 
        creator_id: int, 
        status: Optional[int] = None
    ) -> List[CommunityEvent]:
        """根据创建者ID查找事件"""
        pass

    @abstractmethod
    def find_pending_events(self, community_id: int) -> List[CommunityEvent]:
        """查找社区未处理的事件"""
        pass

    @abstractmethod
    def find_ongoing_events(self, community_id: int) -> List[CommunityEvent]:
        """查找社区进行中的事件"""
        pass

    @abstractmethod
    def find_events_by_date_range(
        self, 
        community_id: int, 
        start_date: date, 
        end_date: date
    ) -> List[CommunityEvent]:
        """查找指定日期范围内的事件"""
        pass

    @abstractmethod
    def save(self, event: CommunityEvent) -> CommunityEvent:
        """保存社区事件"""
        pass

    @abstractmethod
    def update(self, event: CommunityEvent) -> CommunityEvent:
        """更新社区事件"""
        pass

    @abstractmethod
    def delete(self, event_id: int) -> bool:
        """删除社区事件"""
        pass

    @abstractmethod
    def close_event(
        self, 
        event_id: int, 
        closed_by: int, 
        closure_type: int, 
        closure_reason: Optional[str] = None
    ) -> bool:
        """关闭事件"""
        pass

    @abstractmethod
    def count_by_community_id(self, community_id: int, status: Optional[int] = None) -> int:
        """统计社区事件数量"""
        pass

    @abstractmethod
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
        pass