"""
打卡记录仓储 SQLAlchemy 实现

负责 ORM 模型与领域实体之间的转换
"""
from typing import List, Optional
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRecord
from app.domain.repositories.checkin_record_repository import CheckinRecordRepository
from app.domain.entities.checkin_record_entity import CheckinRecordEntity


class SQLAlchemyCheckinRecordRepository(CheckinRecordRepository):
    """打卡记录仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话,如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, record_id: int) -> Optional[CheckinRecordEntity]:
        """根据ID查找打卡记录"""
        orm_model = self.session.get(CheckinRecord, record_id)
        if not orm_model:
            return None
        return self._to_entity(orm_model)

    def find_by_rule_id(self, rule_id: int) -> List[CheckinRecordEntity]:
        """根据规则ID查找打卡记录"""
        stmt = select(CheckinRecord).where(
            CheckinRecord.rule_id == rule_id
        ).order_by(CheckinRecord.created_at.desc())

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_by_user_id(self, user_id: int, limit: int = 100) -> List[CheckinRecordEntity]:
        """根据用户ID查找打卡记录"""
        stmt = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id
        ).order_by(CheckinRecord.created_at.desc()).limit(limit)

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def find_today_records(self, user_id: int, rule_id: int) -> List[CheckinRecordEntity]:
        """查找用户今天对某个规则的打卡记录"""
        today = datetime.now().date()

        stmt = select(CheckinRecord).where(
            CheckinRecord.user_id == user_id,
            CheckinRecord.rule_id == rule_id,
            db.func.date(CheckinRecord.created_at) == today
        ).order_by(CheckinRecord.created_at.desc())

        orm_models = list(self.session.execute(stmt).scalars().all())
        return [self._to_entity(model) for model in orm_models]

    def save_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        保存打卡记录实体

        将领域实体转换为 ORM 模型并保存
        """
        orm_model = CheckinRecord(
            record_id=entity.record_id,
            rule_id=entity.rule_id,
            user_id=entity.user_id,
            community_rule_id=entity.community_rule_id,
            solo_user_id=entity.solo_user_id,
            planned_checkin_time=entity.planned_checkin_time,
            checkin_status=entity.checkin_status,
            checkin_time=entity.checkin_time,
            created_at=entity.created_at,
            updated_at=entity.updated_at
        )

        self.session.add(orm_model)
        self.session.flush()

        return self._to_entity(orm_model)

    def update_entity(self, entity: CheckinRecordEntity) -> CheckinRecordEntity:
        """
        更新打卡记录实体

        将领域实体转换为 ORM 模型并更新
        """
        orm_model = self.session.get(CheckinRecord, entity.record_id)
        if not orm_model:
            raise ValueError(f"CheckinRecord with id {entity.record_id} not found")

        # 更新 ORM 模型属性
        orm_model.checkin_status = entity.checkin_status
        orm_model.checkin_time = entity.checkin_time
        orm_model.updated_at = entity.updated_at

        self.session.flush()

        return self._to_entity(orm_model)

    def delete(self, record_id: int) -> bool:
        """删除打卡记录"""
        orm_model = self.session.get(CheckinRecord, record_id)
        if orm_model:
            self.session.delete(orm_model)
            self.session.flush()
            return True
        return False

    def _to_entity(self, orm_model: CheckinRecord) -> CheckinRecordEntity:
        """
        将 ORM 模型转换为领域实体

        Args:
            orm_model: SQLAlchemy CheckinRecord 模型

        Returns:
            CheckinRecordEntity: 领域实体
        """
        return CheckinRecordEntity(
            record_id=orm_model.record_id,
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            planned_checkin_time=orm_model.planned_checkin_time,
            community_rule_id=orm_model.community_rule_id,
            solo_user_id=orm_model.solo_user_id,
            checkin_status=orm_model.checkin_status,
            checkin_time=orm_model.checkin_time,
            created_at=orm_model.created_at,
            updated_at=orm_model.updated_at
        )
