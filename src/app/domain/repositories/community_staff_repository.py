"""
社区工作人员仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import CommunityStaff


class CommunityStaffRepository(ABC):
    """社区工作人员仓储接口"""

    @abstractmethod
    def find_by_id(self, staff_id: int) -> Optional[CommunityStaff]:
        """根据ID查找工作人员"""
        pass

    @abstractmethod
    def find_by_community_id(self, community_id: int, include_removed: bool = False) -> List[CommunityStaff]:
        """根据社区ID查找工作人员"""
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int, include_removed: bool = False) -> List[CommunityStaff]:
        """根据用户ID查找工作人员"""
        pass

    @abstractmethod
    def find_by_community_and_user(self, community_id: int, user_id: int) -> Optional[CommunityStaff]:
        """根据社区ID和用户ID查找工作人员"""
        pass

    @abstractmethod
    def find_by_community_and_role(
        self, 
        community_id: int, 
        role: str, 
        include_removed: bool = False
    ) -> List[CommunityStaff]:
        """根据社区ID和角色查找工作人员"""
        pass

    @abstractmethod
    def find_managers(self, community_id: int) -> List[CommunityStaff]:
        """查找社区主管"""
        pass

    @abstractmethod
    def find_staff(self, community_id: int) -> List[CommunityStaff]:
        """查找社区专员"""
        pass

    @abstractmethod
    def save(self, staff: CommunityStaff) -> CommunityStaff:
        """保存工作人员"""
        pass

    @abstractmethod
    def update(self, staff: CommunityStaff) -> CommunityStaff:
        """更新工作人员"""
        pass

    @abstractmethod
    def delete(self, staff_id: int) -> bool:
        """删除工作人员"""
        pass

    @abstractmethod
    def soft_delete(self, staff_id: int) -> bool:
        """软删除工作人员"""
        pass

    @abstractmethod
    def exists(self, community_id: int, user_id: int) -> bool:
        """检查用户是否是社区工作人员"""
        pass

    @abstractmethod
    def count_by_community_id(self, community_id: int, role: Optional[str] = None) -> int:
        """统计社区工作人员数量"""
        pass