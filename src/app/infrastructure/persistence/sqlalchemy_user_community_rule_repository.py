"""
用户社区规则映射仓储 SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select
from database.flask_models import db, UserCommunityRule
from app.domain.repositories.user_community_rule_repository import UserCommunityRuleRepository


class SQLAlchemyUserCommunityRuleRepository(UserCommunityRuleRepository):
    """用户社区规则映射仓储 SQLAlchemy 实现"""

    def find_by_id(self, mapping_id: int) -> Optional[UserCommunityRule]:
        """
        根据ID查找映射

        Args:
            mapping_id: 映射ID

        Returns:
            用户社区规则映射对象，如果不存在则返回 None
        """
        return db.session.get(UserCommunityRule, mapping_id)

    def find_by_user_id(self, user_id: int, include_inactive: bool = False) -> List[UserCommunityRule]:
        """
        根据用户ID查找所有映射

        Args:
            user_id: 用户ID
            include_inactive: 是否包含未激活的映射

        Returns:
            用户社区规则映射列表
        """
        query = select(UserCommunityRule).where(
            UserCommunityRule.user_id == user_id
        )

        if not include_inactive:
            query = query.where(UserCommunityRule.is_active == True)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_community_rule_id(self, community_rule_id: int, include_inactive: bool = False) -> List[UserCommunityRule]:
        """
        根据社区规则ID查找所有映射

        Args:
            community_rule_id: 社区规则ID
            include_inactive: 是否包含未激活的映射

        Returns:
            用户社区规则映射列表
        """
        query = select(UserCommunityRule).where(
            UserCommunityRule.community_rule_id == community_rule_id
        )

        if not include_inactive:
            query = query.where(UserCommunityRule.is_active == True)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_user_and_rule(self, user_id: int, community_rule_id: int) -> Optional[UserCommunityRule]:
        """
        根据用户ID和社区规则ID查找映射

        Args:
            user_id: 用户ID
            community_rule_id: 社区规则ID

        Returns:
            用户社区规则映射对象，如果不存在则返回 None
        """
        query = select(UserCommunityRule).where(
            UserCommunityRule.user_id == user_id,
            UserCommunityRule.community_rule_id == community_rule_id
        )

        result = db.session.execute(query)
        return result.scalar_one_or_none()

    def save(self, mapping: UserCommunityRule) -> UserCommunityRule:
        """
        保存用户社区规则映射

        Args:
            mapping: 用户社区规则映射对象

        Returns:
            保存后的用户社区规则映射对象
        """
        db.session.add(mapping)
        db.session.flush()
        return mapping

    def delete(self, mapping_id: int) -> bool:
        """
        删除用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否删除成功
        """
        mapping = self.find_by_id(mapping_id)
        if mapping:
            db.session.delete(mapping)
            db.session.flush()
            return True
        return False

    def activate(self, mapping_id: int) -> bool:
        """
        激活用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否激活成功
        """
        mapping = self.find_by_id(mapping_id)
        if mapping:
            mapping.is_active = True
            db.session.flush()
            return True
        return False

    def deactivate(self, mapping_id: int) -> bool:
        """
        停用用户社区规则映射

        Args:
            mapping_id: 映射ID

        Returns:
            是否停用成功
        """
        mapping = self.find_by_id(mapping_id)
        if mapping:
            mapping.is_active = False
            db.session.flush()
            return True
        return False

    def count_by_user_id(self, user_id: int, include_inactive: bool = False) -> int:
        """
        统计用户的社区规则映射数量

        Args:
            user_id: 用户ID
            include_inactive: 是否包含未激活的映射

        Returns:
            映射数量
        """
        from sqlalchemy import func

        query = select(func.count(UserCommunityRule.mapping_id)).where(
            UserCommunityRule.user_id == user_id
        )

        if not include_inactive:
            query = query.where(UserCommunityRule.is_active == True)

        result = db.session.execute(query)
        return result.scalar() or 0

    def count_by_community_rule_id(self, community_rule_id: int, include_inactive: bool = False) -> int:
        """
        统计社区规则的映射数量

        Args:
            community_rule_id: 社区规则ID
            include_inactive: 是否包含未激活的映射

        Returns:
            映射数量
        """
        from sqlalchemy import func

        query = select(func.count(UserCommunityRule.mapping_id)).where(
            UserCommunityRule.community_rule_id == community_rule_id
        )

        if not include_inactive:
            query = query.where(UserCommunityRule.is_active == True)

        result = db.session.execute(query)
        return result.scalar() or 0