"""
社区打卡规则仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from database.flask_models import db, CommunityCheckinRule
from app.domain.repositories.community_checkin_rule_repository import CommunityCheckinRuleRepository


class SQLAlchemyCommunityCheckinRuleRepository(CommunityCheckinRuleRepository):
    """社区打卡规则仓储 SQLAlchemy 实现"""

    def find_by_id(self, rule_id: int) -> Optional[CommunityCheckinRule]:
        """
        根据ID查找社区打卡规则

        Args:
            rule_id: 规则ID

        Returns:
            社区打卡规则对象，如果不存在则返回 None
        """
        return db.session.get(CommunityCheckinRule, rule_id)

    def find_by_community_id(self, community_id: int, include_deleted: bool = False) -> List[CommunityCheckinRule]:
        """
        根据社区ID查找所有打卡规则

        Args:
            community_id: 社区ID
            include_deleted: 是否包含已删除的规则

        Returns:
            社区打卡规则列表
        """
        query = select(CommunityCheckinRule).where(
            CommunityCheckinRule.community_id == community_id
        )

        if not include_deleted:
            query = query.where(CommunityCheckinRule.status != 2)

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_community_id_and_status(self, community_id: int, status: int) -> List[CommunityCheckinRule]:
        """
        根据社区ID和状态查找打卡规则

        Args:
            community_id: 社区ID
            status: 规则状态（0=停用, 1=启用, 2=删除）

        Returns:
            社区打卡规则列表
        """
        query = select(CommunityCheckinRule).where(
            CommunityCheckinRule.community_id == community_id,
            CommunityCheckinRule.status == status
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_by_created_by(self, created_by: int) -> List[CommunityCheckinRule]:
        """
        根据创建者ID查找打卡规则

        Args:
            created_by: 创建者ID

        Returns:
            社区打卡规则列表
        """
        query = select(CommunityCheckinRule).where(
            CommunityCheckinRule.created_by == created_by
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def save(self, rule: CommunityCheckinRule) -> CommunityCheckinRule:
        """
        保存社区打卡规则

        Args:
            rule: 社区打卡规则对象

        Returns:
            保存后的社区打卡规则对象
        """
        db.session.add(rule)
        db.session.flush()
        return rule

    def delete(self, rule_id: int) -> bool:
        """
        删除社区打卡规则（软删除）

        Args:
            rule_id: 规则ID

        Returns:
            是否删除成功
        """
        rule = self.find_by_id(rule_id)
        if rule:
            rule.status = 2  # 标记为已删除
            db.session.flush()
            return True
        return False

    def count_by_community_id(self, community_id: int, include_deleted: bool = False) -> int:
        """
        统计社区的打卡规则数量

        Args:
            community_id: 社区ID
            include_deleted: 是否包含已删除的规则

        Returns:
            规则数量
        """
        from sqlalchemy import func

        query = select(func.count(CommunityCheckinRule.community_rule_id)).where(
            CommunityCheckinRule.community_id == community_id
        )

        if not include_deleted:
            query = query.where(CommunityCheckinRule.status != 2)

        result = db.session.execute(query)
        return result.scalar() or 0

    def get_all_enabled_by_community_id(self, community_id: int) -> List[CommunityCheckinRule]:
        """
        获取社区所有启用的打卡规则

        Args:
            community_id: 社区ID

        Returns:
            启用的社区打卡规则列表
        """
        return self.find_by_community_id_and_status(community_id, 1)

    def get_all_grouped_by_status(self, community_id: int) -> dict:
        """
        获取社区所有打卡规则，按状态分组

        Args:
            community_id: 社区ID

        Returns:
            按状态分组的规则字典 {'enabled': [], 'disabled': [], 'deleted': []}
        """
        all_rules = self.find_by_community_id(community_id, include_deleted=True)

        result = {
            'enabled': [],
            'disabled': [],
            'deleted': []
        }

        for rule in all_rules:
            if rule.status == 1:
                result['enabled'].append(rule)
            elif rule.status == 0:
                result['disabled'].append(rule)
            elif rule.status == 2:
                result['deleted'].append(rule)

        return result

    def find_active_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的社区打卡规则"""
        query = select(CommunityCheckinRule).where(
            CommunityCheckinRule.status == 1
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_all_day_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的全天社区打卡规则"""
        query = select(CommunityCheckinRule).where(
            CommunityCheckinRule.status == 1,  # 已启用
            CommunityCheckinRule.time_slot_type == 5  # 全天规则
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def find_all_day_rules(self) -> List[CommunityCheckinRule]:
        """查找所有启用的全天社区打卡规则"""
        from sqlalchemy import and_

        query = select(CommunityCheckinRule).where(
            and_(
                CommunityCheckinRule.status == 1,
                CommunityCheckinRule.time_slot_type == 5
            )
        )

        result = db.session.execute(query)
        return list(result.scalars().all())