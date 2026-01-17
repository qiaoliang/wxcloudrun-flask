"""
打卡规则仓储 SQLAlchemy 实现

负责 ORM 模型与领域实体之间的转换
"""
from typing import List, Optional
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRule
from app.domain.repositories.checkin_rule_repository import CheckinRuleRepository
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity


class SQLAlchemyCheckinRuleRepository(CheckinRuleRepository):
    """打卡规则仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话,如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        """根据ID查找打卡规则"""
        orm_model = self.session.get(CheckinRule, rule_id)
        if not orm_model:
            return None
        return self._to_entity(orm_model)

    def find_by_user_id(self, user_id: int, include_disabled: bool = False) -> List[CheckinRuleEntity]:
        """根据用户ID查找打卡规则"""
        stmt = select(CheckinRule).where(CheckinRule.user_id == user_id)

        if not include_disabled:
            stmt = stmt.where(CheckinRule.status == 1)

        stmt = stmt.order_by(CheckinRule.created_at.desc())
        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_active_by_user_id(self, user_id: int) -> List[CheckinRuleEntity]:
        """根据用户ID查找启用的打卡规则"""
        return self.find_by_user_id(user_id, include_disabled=False)

    def save_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        保存打卡规则实体

        将领域实体转换为 ORM 模型并保存
        """
        # 转换 custom_time: 字符串 -> time 对象
        custom_time_obj = None
        if entity.custom_time:
            if isinstance(entity.custom_time, str):
                from datetime import time as time_class
                try:
                    custom_time_obj = time_class.fromisoformat(entity.custom_time)
                except ValueError:
                    pass
            elif isinstance(entity.custom_time, time):
                custom_time_obj = entity.custom_time

        # 转换 week_days: 字符串 -> 整数位掩码
        week_days_int = entity.week_days
        if entity.week_days and isinstance(entity.week_days, str):
            # 检查是逗号分隔格式还是已经是数字字符串
            if ',' in entity.week_days:
                # 字符串 "1,3,5" 转换为位掩码整数
                try:
                    days = [int(d.strip()) for d in entity.week_days.split(',')]
                    week_days_int = sum(1 << (day - 1) for day in days)
                except (ValueError, AttributeError):
                    week_days_int = 127  # 默认所有天
            else:
                # 已经是数字字符串,直接转换为整数
                try:
                    week_days_int = int(entity.week_days)
                except ValueError:
                    week_days_int = 127

        orm_model = CheckinRule(
            rule_id=entity.rule_id if entity.rule_id != 0 else None,
            user_id=entity.user_id,
            rule_name=entity.rule_name,
            frequency_type=entity.frequency_type,
            time_slot_type=entity.time_slot_type,
            status=entity.status,
            community_id=entity.community_id,
            icon_url=entity.icon_url,
            custom_time=custom_time_obj,
            week_days=week_days_int,
            custom_start_date=entity.custom_start_date,
            custom_end_date=entity.custom_end_date,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        self.session.add(orm_model)
        self.session.flush()

        # 返回更新后的实体
        return self._to_entity(orm_model)

    def update_entity(self, entity: CheckinRuleEntity) -> CheckinRuleEntity:
        """
        更新打卡规则实体

        将领域实体转换为 ORM 模型并更新
        """
        orm_model = self.session.get(CheckinRule, entity.rule_id)
        if not orm_model:
            raise ValueError(f"CheckinRule with id {entity.rule_id} not found")

        # 更新 ORM 模型属性
        orm_model.rule_name = entity.rule_name
        orm_model.frequency_type = entity.frequency_type
        orm_model.time_slot_type = entity.time_slot_type
        orm_model.status = entity.status
        orm_model.community_id = entity.community_id
        orm_model.icon_url = entity.icon_url

        # 转换 custom_time: 字符串 -> time 对象
        if entity.custom_time:
            if isinstance(entity.custom_time, str):
                from datetime import time as time_class
                try:
                    orm_model.custom_time = time_class.fromisoformat(entity.custom_time)
                except ValueError:
                    orm_model.custom_time = None
            elif isinstance(entity.custom_time, time):
                orm_model.custom_time = entity.custom_time
        else:
            orm_model.custom_time = None

        # 转换 week_days: 字符串 -> 整数位掩码
        if entity.week_days and isinstance(entity.week_days, str):
            # 检查是逗号分隔格式还是已经是数字字符串
            if ',' in entity.week_days:
                # 字符串 "1,3,5" 转换为位掩码整数
                try:
                    days = [int(d.strip()) for d in entity.week_days.split(',')]
                    orm_model.week_days = sum(1 << (day - 1) for day in days)
                except (ValueError, AttributeError):
                    orm_model.week_days = 127
            else:
                # 已经是数字字符串,直接转换为整数
                try:
                    orm_model.week_days = int(entity.week_days)
                except ValueError:
                    orm_model.week_days = 127
        elif entity.week_days:
            orm_model.week_days = entity.week_days

        orm_model.custom_start_date = entity.custom_start_date
        orm_model.custom_end_date = entity.custom_end_date
        orm_model.updated_at = entity.updated_at

        self.session.flush()

        return self._to_entity(orm_model)

    def delete(self, rule_id: int) -> bool:
        """删除打卡规则"""
        orm_model = self.session.get(CheckinRule, rule_id)
        if orm_model:
            self.session.delete(orm_model)
            self.session.flush()
            return True
        return False

    def soft_delete(self, rule_id: int) -> bool:
        """软删除打卡规则"""
        entity = self.find_by_id(rule_id)
        if entity:
            entity.soft_delete()
            return self.update_entity(entity) is not None
        return False

    def find_active_rules(self) -> List[CheckinRuleEntity]:
        """查找所有启用的打卡规则"""
        from sqlalchemy import and_

        stmt = select(CheckinRule).where(
            and_(
                CheckinRule.status != 2  # 排除已删除的规则
            )
        )

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_all_day_rules(self) -> List[CheckinRuleEntity]:
        """查找所有启用的全天打卡规则"""
        from sqlalchemy import and_

        stmt = select(CheckinRule).where(
            and_(
                CheckinRule.status == 1,  # 已启用
                CheckinRule.time_slot_type == 5  # 全天规则
            )
        )

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_by_ids(self, rule_ids: List[int]) -> List[CheckinRuleEntity]:
        """根据ID列表查找打卡规则"""
        if not rule_ids:
            return []

        stmt = select(CheckinRule).where(CheckinRule.rule_id.in_(rule_ids))
        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def _to_entity(self, orm_model: CheckinRule) -> CheckinRuleEntity:
        """
        将 ORM 模型转换为领域实体

        Args:
            orm_model: SQLAlchemy CheckinRule 模型

        Returns:
            CheckinRuleEntity: 领域实体
        """
        # 转换 custom_time: time 对象 -> 字符串
        custom_time_str = None
        if orm_model.custom_time:
            custom_time_str = orm_model.custom_time.strftime('%H:%M:%S')

        # 转换 week_days: 整数位掩码 -> 字符串
        week_days_str = str(orm_model.week_days) if orm_model.week_days is not None else None

        return CheckinRuleEntity(
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            rule_name=orm_model.rule_name,
            frequency_type=orm_model.frequency_type,
            time_slot_type=orm_model.time_slot_type,
            status=orm_model.status,
            community_id=orm_model.community_id,
            icon_url=orm_model.icon_url,
            custom_time=custom_time_str,
            week_days=week_days_str,
            custom_start_date=orm_model.custom_start_date,
            custom_end_date=orm_model.custom_end_date,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )
