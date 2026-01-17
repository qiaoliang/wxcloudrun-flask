"""
社区申请仓储接口
"""
from typing import List, Optional
from abc import ABC, abstractmethod

from database.flask_models import CommunityApplication


class CommunityApplicationRepository(ABC):
    """社区申请仓储接口"""

    @abstractmethod
    def save(self, application: CommunityApplication) -> CommunityApplication:
        """
        保存社区申请

        Args:
            application: 社区申请实体

        Returns:
            CommunityApplication: 保存后的社区申请
        """
        pass

    @abstractmethod
    def find_by_id(self, application_id: int) -> Optional[CommunityApplication]:
        """
        根据ID查找社区申请

        Args:
            application_id: 申请ID

        Returns:
            Optional[CommunityApplication]: 社区申请，不存在返回 None
        """
        pass

    @abstractmethod
    def find_pending_by_user_and_community(
        self, user_id: int, community_id: int
    ) -> Optional[CommunityApplication]:
        """
        查找用户对社区的待审核申请

        Args:
            user_id: 用户ID
            community_id: 社区ID

        Returns:
            Optional[CommunityApplication]: 待审核申请，不存在返回 None
        """
        pass

    @abstractmethod
    def find_by_community(self, community_id: int, status: Optional[int] = None) -> List[CommunityApplication]:
        """
        查找社区的所有申请

        Args:
            community_id: 社区ID
            status: 申请状态（可选）

        Returns:
            List[CommunityApplication]: 申请列表
        """
        pass

    @abstractmethod
    def update_status(
        self,
        application_id: int,
        status: int,
        processor_id: int,
        rejection_reason: Optional[str] = None
    ) -> Optional[CommunityApplication]:
        """
        更新申请状态

        Args:
            application_id: 申请ID
            status: 新状态
            processor_id: 处理者ID
            rejection_reason: 拒绝理由（可选）

        Returns:
            Optional[CommunityApplication]: 更新后的申请，不存在返回 None
        """
        pass