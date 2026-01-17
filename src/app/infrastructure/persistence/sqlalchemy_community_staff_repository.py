"""
社区工作人员仓储 SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from database.flask_models import db, CommunityStaff
from app.domain.repositories.community_staff_repository import CommunityStaffRepository


class SQLAlchemyCommunityStaffRepository(CommunityStaffRepository):
    """社区工作人员仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, staff_id: int) -> Optional[CommunityStaff]:
        """根据ID查找工作人员"""
        return self.session.get(CommunityStaff, staff_id)

    def find_by_community_id(self, community_id: int, include_removed: bool = False) -> List[CommunityStaff]:
        """根据社区ID查找工作人员"""
        stmt = select(CommunityStaff).where(CommunityStaff.community_id == community_id)
        
        if not include_removed:
            stmt = stmt.where(CommunityStaff.removed_at.is_(None))
        
        stmt = stmt.order_by(CommunityStaff.added_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_user_id(self, user_id: int, include_removed: bool = False) -> List[CommunityStaff]:
        """根据用户ID查找工作人员"""
        stmt = select(CommunityStaff).where(CommunityStaff.user_id == user_id)
        
        if not include_removed:
            stmt = stmt.where(CommunityStaff.removed_at.is_(None))
        
        stmt = stmt.order_by(CommunityStaff.added_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_community_and_user(self, community_id: int, user_id: int) -> Optional[CommunityStaff]:
        """根据社区ID和用户ID查找工作人员"""
        stmt = select(CommunityStaff).where(
            and_(
                CommunityStaff.community_id == community_id,
                CommunityStaff.user_id == user_id,
                CommunityStaff.removed_at.is_(None)
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def find_by_community_and_role(
        self, 
        community_id: int, 
        role: str, 
        include_removed: bool = False
    ) -> List[CommunityStaff]:
        """根据社区ID和角色查找工作人员"""
        stmt = select(CommunityStaff).where(
            and_(
                CommunityStaff.community_id == community_id,
                CommunityStaff.role == role
            )
        )
        
        if not include_removed:
            stmt = stmt.where(CommunityStaff.removed_at.is_(None))
        
        stmt = stmt.order_by(CommunityStaff.added_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_managers(self, community_id: int) -> List[CommunityStaff]:
        """查找社区主管"""
        return self.find_by_community_and_role(community_id, 'manager')

    def find_staff(self, community_id: int) -> List[CommunityStaff]:
        """查找社区专员"""
        return self.find_by_community_and_role(community_id, 'staff')

    def save(self, staff: CommunityStaff) -> CommunityStaff:
        """保存工作人员"""
        self.session.add(staff)
        self.session.flush()
        return staff

    def update(self, staff: CommunityStaff) -> CommunityStaff:
        """更新工作人员"""
        self.session.merge(staff)
        self.session.flush()
        return staff

    def delete(self, staff_id: int) -> bool:
        """删除工作人员"""
        staff = self.find_by_id(staff_id)
        if staff:
            self.session.delete(staff)
            self.session.flush()
            return True
        return False

    def soft_delete(self, staff_id: int) -> bool:
        """软删除工作人员"""
        from datetime import datetime
        staff = self.find_by_id(staff_id)
        if staff:
            staff.removed_at = datetime.now()
            self.session.flush()
            return True
        return False

    def exists(self, community_id: int, user_id: int) -> bool:
        """检查用户是否是社区工作人员"""
        return self.find_by_community_and_user(community_id, user_id) is not None

    def count_by_community_id(self, community_id: int, role: Optional[str] = None) -> int:
        """统计社区工作人员数量"""
        stmt = select(CommunityStaff).where(
            and_(
                CommunityStaff.community_id == community_id,
                CommunityStaff.removed_at.is_(None)
            )
        )

        if role is not None:
            stmt = stmt.where(CommunityStaff.role == role)

        return len(list(self.session.execute(stmt).scalars().all()))

    def find_active_by_community_and_user(
        self,
        community_id: int,
        user_id: int
    ) -> Optional[CommunityStaff]:
        """
        查找社区和用户的活跃工作人员记录（未软删除）

        这是 find_by_community_and_user 的别名，确保接口一致性
        """
        return self.find_by_community_and_user(community_id, user_id)

    def find_active_by_community_and_role(
        self,
        community_id: int,
        role: str
    ) -> List[CommunityStaff]:
        """
        查找社区中特定角色的活跃工作人员列表（未软删除）

        这是 find_by_community_and_role 的别名，确保接口一致性
        """
        return self.find_by_community_and_role(community_id, role, include_removed=False)