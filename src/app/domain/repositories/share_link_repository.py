"""
分享链接仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import ShareLink


class ShareLinkRepository(ABC):
    """分享链接仓储接口"""

    @abstractmethod
    def find_by_id(self, link_id: int) -> Optional[ShareLink]:
        """
        根据ID查找分享链接

        Args:
            link_id: 分享链接ID

        Returns:
            Optional[ShareLink]: 分享链接对象，不存在时返回None
        """
        pass

    @abstractmethod
    def find_by_token(self, token: str) -> Optional[ShareLink]:
        """
        根据token查找分享链接

        Args:
            token: 分享链接token

        Returns:
            Optional[ShareLink]: 分享链接对象，不存在时返回None
        """
        pass

    @abstractmethod
    def find_by_user_id(self, user_id: int) -> List[ShareLink]:
        """
        根据用户ID查找分享链接列表

        Args:
            user_id: 用户ID

        Returns:
            List[ShareLink]: 分享链接列表
        """
        pass

    @abstractmethod
    def save(self, entity: ShareLink) -> ShareLink:
        """
        保存分享链接

        Args:
            entity: 分享链接对象

        Returns:
            ShareLink: 保存后的分享链接对象
        """
        pass

    @abstractmethod
    def update(self, entity: ShareLink) -> ShareLink:
        """
        更新分享链接

        Args:
            entity: 分享链接对象

        Returns:
            ShareLink: 更新后的分享链接对象
        """
        pass

    @abstractmethod
    def delete(self, link_id: int) -> bool:
        """
        删除分享链接

        Args:
            link_id: 分享链接ID

        Returns:
            bool: 删除是否成功
        """
        pass
