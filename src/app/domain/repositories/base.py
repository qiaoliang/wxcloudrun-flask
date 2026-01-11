"""
仓储基类

定义仓储的通用接口。
"""
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, List, Optional

T = TypeVar('T')


class BaseRepository(ABC, Generic[T]):
    """仓储基类"""

    @abstractmethod
    def save(self, entity: T) -> T:
        """
        保存实体

        Args:
            entity: 要保存的实体

        Returns:
            T: 保存后的实体
        """
        pass

    @abstractmethod
    def delete(self, entity: T) -> None:
        """
        删除实体

        Args:
            entity: 要删除的实体
        """
        pass

    @abstractmethod
    def find_by_id(self, entity_id: int) -> Optional[T]:
        """
        根据ID查找实体

        Args:
            entity_id: 实体ID

        Returns:
            Optional[T]: 实体对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_all(self) -> List[T]:
        """
        查找所有实体

        Returns:
            List[T]: 实体列表
        """
        pass

    @abstractmethod
    def exists(self, entity_id: int) -> bool:
        """
        检查实体是否存在

        Args:
            entity_id: 实体ID

        Returns:
            bool: 如果存在返回 True，否则返回 False
        """
        pass