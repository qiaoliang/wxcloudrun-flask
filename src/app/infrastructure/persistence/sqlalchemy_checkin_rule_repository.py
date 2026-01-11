"""
打卡规则仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRule
from app.domain.repositories.checkin_rule_repository import CheckinRuleRepository


class SQLAlchemyCheckinRuleRepository(CheckinRuleRepository):
    """打卡规则仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, rule_id: int) -> Optional[CheckinRule]:
        """根据ID查找打卡规则"""
        return self.session.get(CheckinRule, rule_id)

    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRule]:
        """根据用户ID查找打卡规则"""
        stmt = select(CheckinRule).where(CheckinRule.user_id == user_id)
        
        if not include_disabled:
            stmt = stmt.where(CheckinRule.status == 1)
        
        stmt = stmt.order_by(CheckinRule.created_at.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_active_by_user_id(self, user_id: int) -> List[CheckinRule]:
        """根据用户ID查找启用的打卡规则"""
        return self.find_by_user_id(user_id, include_disabled=False)

    def save(self, rule: CheckinRule) -> CheckinRule:
        """保存打卡规则"""
        self.session.add(rule)
        self.session.flush()
        return rule

    def update(self, rule: CheckinRule) -> CheckinRule:
        """更新打卡规则"""
        self.session.merge(rule)
        self.session.flush()
        return rule

    def delete(self, rule_id: int) -> bool:
        """删除打卡规则"""
        rule = self.find_by_id(rule_id)
        if rule:
            self.session.delete(rule)
            self.session.flush()
            return True
        return False

    def soft_delete(self, rule_id: int) -> bool:
        """软删除打卡规则"""
        rule = self.find_by_id(rule_id)
        if rule:
            rule.status = 2  # 2=删除
            self.session.flush()
            return True
        return False