"""
分享链接访问日志仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from database.flask_models import ShareLinkAccessLog


class ShareLinkAccessLogRepository(ABC):
    """分享链接访问日志仓储接口"""

    @abstractmethod
    def save(self, entity: ShareLinkAccessLog) -> ShareLinkAccessLog:
        """
        保存分享链接访问日志

        Args:
            entity: 分享链接访问日志对象

        Returns:
            ShareLinkAccessLog: 保存后的分享链接访问日志对象
        """
        pass

    @abstractmethod
    def find_by_token(self, token: str) -> List[ShareLinkAccessLog]:
        """
        根据token查找访问日志列表

        Args:
            token: 分享链接token

        Returns:
            List[ShareLinkAccessLog]: 访问日志列表
        """
        pass
