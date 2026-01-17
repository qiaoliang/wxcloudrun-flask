"""
计数器仓储实现

使用SQLAlchemy实现计数器数据访问。
"""
from typing import List, Optional
from sqlalchemy import select, delete

from app.domain.repositories.counters_repository import CountersRepository
from database.flask_models import db, Counters


class SQLAlchemyCountersRepository(CountersRepository):
    """计数器仓储SQLAlchemy实现"""

    def __init__(self):
        self._session = db.session

    def find_by_id(self, counter_id: str) -> Optional[Counters]:
        """
        根据ID查找计数器

        Args:
            counter_id: 计数器ID

        Returns:
            Optional[Counters]: 计数器对象，如果不存在则返回 None
        """
        stmt = select(Counters).where(Counters.id == counter_id)
        return self._session.execute(stmt).scalar_one_or_none()

    def find_all(self) -> List[Counters]:
        """
        查找所有计数器

        Returns:
            List[Counters]: 计数器列表
        """
        stmt = select(Counters)
        return self._session.execute(stmt).scalars().all()

    def save(self, counter: Counters) -> Counters:
        """
        保存计数器

        Args:
            counter: 计数器对象

        Returns:
            Counters: 保存后的计数器对象
        """
        self._session.add(counter)
        self._session.flush()
        self._session.refresh(counter)
        return counter

    def delete_all(self) -> bool:
        """
        删除所有计数器

        Returns:
            bool: 是否成功删除
        """
        try:
            self._session.execute(delete(Counters))
            self._session.commit()
            return True
        except Exception as e:
            self._session.rollback()
            raise e
