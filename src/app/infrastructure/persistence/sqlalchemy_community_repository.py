"""
SQLAlchemy 社区仓储实现

使用 SQLAlchemy 实现社区仓储接口。
"""
from typing import List, Optional

from sqlalchemy import select

from app.domain.repositories.community_repository import CommunityRepository
from database.flask_models import db, Community


class SQLAlchemyCommunityRepository(CommunityRepository):
    """SQLAlchemy 社区仓储实现"""

    def save(self, entity: Community) -> Community:
        """
        保存社区

        Args:
            entity: 要保存的社区

        Returns:
            Community: 保存后的社区
        """
        db.session.add(entity)
        db.session.flush()
        return entity

    def delete(self, entity: Community) -> None:
        """
        删除社区

        Args:
            entity: 要删除的社区
        """
        db.session.delete(entity)

    def find_by_id(self, entity_id: int) -> Optional[Community]:
        """
        根据ID查找社区

        Args:
            entity_id: 社区ID

        Returns:
            Optional[Community]: 社区对象，如果不存在则返回 None
        """
        return db.session.get(Community, entity_id)

    def find_all(self) -> List[Community]:
        """
        查找所有社区

        Returns:
            List[Community]: 社区列表
        """
        stmt = select(Community)
        return db.session.execute(stmt).scalars().all()

    def exists(self, entity_id: int) -> bool:
        """
        检查社区是否存在

        Args:
            entity_id: 社区ID

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        return self.find_by_id(entity_id) is not None

    def find_by_name(self, name: str) -> Optional[Community]:
        """
        根据社区名称查找社区

        Args:
            name: 社区名称

        Returns:
            Optional[Community]: 社区对象，如果不存在则返回 None
        """
        stmt = select(Community).where(Community.name == name)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_by_creator_id(self, creator_id: int) -> List[Community]:
        """
        根据创建者ID查找社区列表

        Args:
            creator_id: 创建者ID

        Returns:
            List[Community]: 社区列表
        """
        stmt = select(Community).where(Community.creator_id == creator_id)
        return db.session.execute(stmt).scalars().all()

    def find_by_manager_id(self, manager_id: int) -> List[Community]:
        """
        根据主管ID查找社区列表

        Args:
            manager_id: 主管ID

        Returns:
            List[Community]: 社区列表
        """
        stmt = select(Community).where(Community.manager_id == manager_id)
        return db.session.execute(stmt).scalars().all()

    def find_default_community(self) -> Optional[Community]:
        """
        查找默认社区

        Returns:
            Optional[Community]: 默认社区对象，如果不存在则返回 None
        """
        stmt = select(Community).where(Community.is_default == True)
        return db.session.execute(stmt).scalar_one_or_none()

    def find_active_communities(self) -> List[Community]:
        """
        查找所有活跃的社区

        Returns:
            List[Community]: 活跃社区列表
        """
        stmt = select(Community).where(Community.status == 1)
        return db.session.execute(stmt).scalars().all()

    def exists_by_name(self, name: str) -> bool:
        """
        检查社区名称是否存在

        Args:
            name: 社区名称

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        return self.find_by_name(name) is not None