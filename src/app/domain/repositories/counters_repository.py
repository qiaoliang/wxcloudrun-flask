"""
计数器仓储接口

定义计数器相关的数据访问操作。
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import Counters


class CountersRepository(ABC):
    """计数器仓储接口"""

    @abstractmethod
    def find_by_id(self, counter_id: str) -> Optional[Counters]:
        """
        根据ID查找计数器

        Args:
            counter_id: 计数器ID

        Returns:
            Optional[Counters]: 计数器对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[Counters]:
        """
        查找所有计数器

        Returns:
            List[Counters]: 计数器列表
        """
        pass

    @abstractmethod
    def save(self, counter: Counters) -> Counters:
        """
        保存计数器

        Args:
            counter: 计数器对象

        Returns:
            Counters: 保存后的计数器对象
        """
        pass

    @abstractmethod
    def delete_all(self) -> bool:
        """
        删除所有计数器

        Returns:
            bool: 是否成功删除
        """
        pass
