"""
打卡记录仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import datetime, date

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from database.flask_models import db, CheckinRecord
from app.domain.repositories.checkin_record_repository import CheckinRecordRepository


class SQLAlchemyCheckinRecordRepository(CheckinRecordRepository):
    """打卡记录仓储 SQLAlchemy 实现"""

    def __init__(self, session: Optional[Session] = None):
        """初始化仓储

        Args:
            session: 数据库会话，如果为 None 则使用全局 db.session
        """
        self.session = session or db.session

    def find_by_id(self, record_id: int) -> Optional[CheckinRecord]:
        """根据ID查找打卡记录"""
        return self.session.get(CheckinRecord, record_id)

    def find_by_user_id(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """根据用户ID查找打卡记录"""
        stmt = select(CheckinRecord).where(CheckinRecord.user_id == user_id)
        
        if start_date:
            stmt = stmt.where(CheckinRecord.planned_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            stmt = stmt.where(CheckinRecord.planned_time <= datetime.combine(end_date, datetime.max.time()))
        
        stmt = stmt.order_by(CheckinRecord.planned_time.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_by_rule_id(
        self, 
        rule_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """根据规则ID查找打卡记录"""
        stmt = select(CheckinRecord).where(CheckinRecord.rule_id == rule_id)
        
        if start_date:
            stmt = stmt.where(CheckinRecord.planned_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            stmt = stmt.where(CheckinRecord.planned_time <= datetime.combine(end_date, datetime.max.time()))
        
        stmt = stmt.order_by(CheckinRecord.planned_time.desc())
        return list(self.session.execute(stmt).scalars().all())

    def find_today_records(self, user_id: int) -> List[CheckinRecord]:
        """查找用户今日的打卡记录"""
        today = date.today()
        return self.find_by_user_id(user_id, start_date=today, end_date=today)

    def find_missed_records(
        self, 
        user_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> List[CheckinRecord]:
        """查找用户漏打卡记录"""
        stmt = select(CheckinRecord).where(
            and_(
                CheckinRecord.user_id == user_id,
                CheckinRecord.status == 0  # 0=未打卡
            )
        )
        
        if start_date:
            stmt = stmt.where(CheckinRecord.planned_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            stmt = stmt.where(CheckinRecord.planned_time <= datetime.combine(end_date, datetime.max.time()))
        
        stmt = stmt.order_by(CheckinRecord.planned_time.desc())
        return list(self.session.execute(stmt).scalars().all())

    def save(self, record: CheckinRecord) -> CheckinRecord:
        """保存打卡记录"""
        self.session.add(record)
        self.session.flush()
        return record

    def update(self, record: CheckinRecord) -> CheckinRecord:
        """更新打卡记录"""
        self.session.merge(record)
        self.session.flush()
        return record

    def delete(self, record_id: int) -> bool:
        """删除打卡记录"""
        record = self.find_by_id(record_id)
        if record:
            self.session.delete(record)
            self.session.flush()
            return True
        return False

    def cancel(self, record_id: int) -> bool:
        """取消打卡记录"""
        record = self.find_by_id(record_id)
        if record:
            record.status = 2  # 2=已撤销
            self.session.flush()
            return True
        return False

    def count_by_user_id(self, user_id: int, start_date: Optional[date] = None, end_date: Optional[date] = None) -> int:
        """统计用户打卡记录数量"""
        stmt = select(CheckinRecord).where(CheckinRecord.user_id == user_id)
        
        if start_date:
            stmt = stmt.where(CheckinRecord.planned_time >= datetime.combine(start_date, datetime.min.time()))
        if end_date:
            stmt = stmt.where(CheckinRecord.planned_time <= datetime.combine(end_date, datetime.max.time()))
        
        return len(list(self.session.execute(stmt).scalars().all()))

    def find_by_rule_and_date(self, rule_id: int, check_date: date, rule_source: str = 'personal') -> List[CheckinRecord]:
        """根据规则ID和日期查询打卡记录"""
        from sqlalchemy import func
        
        if rule_source == 'community':
            stmt = select(CheckinRecord).where(
                and_(
                    CheckinRecord.community_rule_id == rule_id,
                    func.date(CheckinRecord.planned_time) == check_date
                )
            )
        else:
            stmt = select(CheckinRecord).where(
                and_(
                    CheckinRecord.rule_id == rule_id,
                    func.date(CheckinRecord.planned_time) == check_date
                )
            )
        
        return list(self.session.execute(stmt).scalars().all())

    def find_by_community_rule_and_users(
        self,
        community_rule_id: int,
        user_ids: List[int],
        planned_time: datetime
    ) -> List[CheckinRecord]:
        """根据社区规则ID和用户列表查询打卡记录"""
        stmt = select(CheckinRecord).where(
            and_(
                CheckinRecord.community_rule_id == community_rule_id,
                CheckinRecord.user_id.in_(user_ids),
                CheckinRecord.planned_time >= planned_time,
                CheckinRecord.planned_time < planned_time + timedelta(days=1)
            )
        )
        
        return list(self.session.execute(stmt).scalars().all())

    def create(
        self,
        rule_id: int,
        user_id: int,
        checkin_time: Optional[datetime],
        planned_time: datetime,
        status: int,
        rule_source: str = 'personal'
    ) -> CheckinRecord:
        """创建打卡记录"""
        if rule_source == 'community':
            record = CheckinRecord(
                community_rule_id=rule_id,
                user_id=user_id,
                solo_user_id=user_id,
                checkin_time=checkin_time,
                status=status,
                planned_time=planned_time
            )
        else:
            record = CheckinRecord(
                rule_id=rule_id,
                user_id=user_id,
                checkin_time=checkin_time,
                status=status,
                planned_time=planned_time
            )
        
        self.session.add(record)
        self.session.flush()
        return record