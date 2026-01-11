"""
计数器仓储 SQLAlchemy 实现
"""
from typing import List, Optional

from sqlalchemy import select
from database.flask_models import db, Counters
from app.domain.repositories.counters_repository import CountersRepository


class SQLAlchemyCountersRepository(CountersRepository):
    """计数器仓储 SQLAlchemy 实现"""

    def find_by_id(self, counter_id: int) -> Optional[Counters]:
        """
        根据ID查找计数器

        Args:
            counter_id: 计数器ID

        Returns:
            计数器对象，如果不存在则返回 None
        """
        return db.session.get(Counters, counter_id)

    def find_all(self) -> List[Counters]:
        """
        查找所有计数器

        Returns:
            计数器列表
        """
        query = select(Counters).order_by(Counters.id)
        result = db.session.execute(query)
        return list(result.scalars().all())

    def save(self, counter: Counters) -> Counters:
        """
        保存计数器

        Args:
            counter: 计数器对象

        Returns:
            保存后的计数器对象
        """
        db.session.add(counter)
        db.session.flush()
        return counter

    def increment(self, counter_id: int) -> Optional[Counters]:
        """
        增加计数器的值

        Args:
            counter_id: 计数器ID

        Returns:
            更新后的计数器对象，如果不存在则返回 None
        """
        counter = self.find_by_id(counter_id)
        if counter:
            counter.count += 1
            db.session.flush()
            return counter
        return None

    def reset(self, counter_id: int) -> Optional[Counters]:
        """
        重置计数器的值

        Args:
            counter_id: 计数器ID

        Returns:
            更新后的计数器对象，如果不存在则返回 None
        """
        counter = self.find_by_id(counter_id)
        if counter:
            counter.count = 0
            db.session.flush()
            return counter
        return None

    def delete(self, counter_id: int) -> bool:
        """
        删除计数器

        Args:
            counter_id: 计数器ID

        Returns:
            是否删除成功
        """
        counter = self.find_by_id(counter_id)
        if counter:
            db.session.delete(counter)
            db.session.flush()
            return True
        return False

    def delete_all(self) -> int:
        """
        删除所有计数器

        Returns:
            删除的计数器数量
        """
        query = select(Counters)
        result = db.session.execute(query)
        counters = result.scalars().all()

        for counter in counters:
            db.session.delete(counter)

        db.session.flush()
        return len(counters)

    def create_or_get(self, counter_id: int) -> Counters:
        """
        创建或获取计数器

        Args:
            counter_id: 计数器ID

        Returns:
            计数器对象
        """
        counter = self.find_by_id(counter_id)
        if not counter:
            counter = Counters(id=counter_id, count=0)
            db.session.add(counter)
            db.session.flush()
        return counter