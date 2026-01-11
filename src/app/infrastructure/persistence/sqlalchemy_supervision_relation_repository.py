"""
监督关系仓储 - SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select, delete

from database.flask_models import db, SupervisionRuleRelation
from app.domain.repositories.supervision_relation_repository import SupervisionRelationRepository


class SQLAlchemySupervisionRelationRepository(SupervisionRelationRepository):
    """监督关系仓储 - SQLAlchemy 实现"""

    def find_by_id(self, relation_id: int) -> Optional[SupervisionRuleRelation]:
        """
        根据ID查找监督关系

        Args:
            relation_id: 监督关系ID

        Returns:
            Optional[SupervisionRuleRelation]: 监督关系对象，不存在时返回None
        """
        return db.session.get(SupervisionRuleRelation, relation_id)

    def find_by_supervisor_id(self, supervisor_id: int) -> List[SupervisionRuleRelation]:
        """
        根据监督者ID查找监督关系列表

        Args:
            supervisor_id: 监督者用户ID

        Returns:
            List[SupervisionRuleRelation]: 监督关系列表
        """
        stmt = select(SupervisionRuleRelation).filter_by(supervisor_user_id=supervisor_id)
        return db.session.execute(stmt).scalars().all()

    def find_by_solo_user_id(self, solo_user_id: int) -> List[SupervisionRuleRelation]:
        """
        根据被监督者ID查找监督关系列表

        Args:
            solo_user_id: 被监督者用户ID

        Returns:
            List[SupervisionRuleRelation]: 监督关系列表
        """
        stmt = select(SupervisionRuleRelation).filter_by(solo_user_id=solo_user_id)
        return db.session.execute(stmt).scalars().all()

    def find_by_users_and_rule(self, supervisor_id: int, solo_user_id: int, rule_id: int) -> Optional[SupervisionRuleRelation]:
        """
        根据监督者、被监督者和规则ID查找监督关系

        Args:
            supervisor_id: 监督者用户ID
            solo_user_id: 被监督者用户ID
            rule_id: 规则ID

        Returns:
            Optional[SupervisionRuleRelation]: 监督关系对象，不存在时返回None
        """
        stmt = select(SupervisionRuleRelation).filter_by(
            supervisor_user_id=supervisor_id,
            solo_user_id=solo_user_id,
            rule_id=rule_id
        )
        return db.session.execute(stmt).scalar_one_or_none()

    def save(self, entity: SupervisionRuleRelation) -> SupervisionRuleRelation:
        """
        保存监督关系

        Args:
            entity: 监督关系对象

        Returns:
            SupervisionRuleRelation: 保存后的监督关系对象
        """
        db.session.add(entity)
        db.session.flush()
        db.session.commit()
        return entity

    def update(self, entity: SupervisionRuleRelation) -> SupervisionRuleRelation:
        """
        更新监督关系

        Args:
            entity: 监督关系对象

        Returns:
            SupervisionRuleRelation: 更新后的监督关系对象
        """
        db.session.merge(entity)
        db.session.flush()
        db.session.commit()
        return entity

    def delete(self, relation_id: int) -> bool:
        """
        删除监督关系

        Args:
            relation_id: 监督关系ID

        Returns:
            bool: 删除是否成功
        """
        stmt = delete(SupervisionRuleRelation).where(SupervisionRuleRelation.relation_id == relation_id)
        result = db.session.execute(stmt)
        db.session.commit()
        return result.rowcount > 0
