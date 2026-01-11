"""
计数器仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import Counters


class CountersRepository(ABC):
    """计数器仓储接口"""

    @abstractmethod
    def find_by_id(self, counter_id: int) -> Optional[Counters]:
        """
        根据ID查找计数器

        Args:
            counter_id: 计数器ID

        Returns:
            计数器对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Counters]:
        """
        查找所有计数器

        Returns:
            计数器列表
        """
        pass

    @abstractmethod
    def save(self, counter: Counters) -> Counters:
        """
        保存计数器

        Args:
            counter: 计数器对象

        Returns:
            保存后的计数器对象
        """
        pass

    @abstractmethod
    def increment(self, counter_id: int) -> Optional[Counters]:
        """
        增加计数器的值

        Args:
            counter_id: 计数器ID

        Returns:
            更新后的计数器对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def reset(self, counter_id: int) -> Optional[Counters]:
        """
        重置计数器的值

        Args:
            counter_id: 计数器ID

        Returns:
            更新后的计数器对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def delete(self, counter_id: int) -> bool:
        """
        删除计数器

        Args:
            counter_id: 计数器ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def delete_all(self) -> int:
        """
        删除所有计数器

        Returns:
            删除的计数器数量
        """
        pass

    @abstractmethod
    def create_or_get(self, counter_id: int) -> Counters:
        """
        创建或获取计数器

        Args:
            counter_id: 计数器ID

        Returns:
            计数器对象
        """
        pass