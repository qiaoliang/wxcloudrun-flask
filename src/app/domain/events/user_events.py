"""
用户领域事件
"""
from dataclasses import dataclass
from typing import Optional

from .base import DomainEvent


@dataclass
class UserCreatedEvent(DomainEvent):
    """用户创建事件"""
    user_id: int
    openid: Optional[str] = None
    phone_number: Optional[str] = None
    nickname: str = ""

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'openid': self.openid,
            'phone_number': self.phone_number,
            'nickname': self.nickname
        })
        return data


@dataclass
class UserLoggedInEvent(DomainEvent):
    """用户登录事件"""
    user_id: int
    login_type: str = "wechat"  # wechat, phone, etc.

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'login_type': self.login_type
        })
        return data


@dataclass
class UserUpdatedEvent(DomainEvent):
    """用户更新事件"""
    user_id: int
    updated_fields: list = None

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'updated_fields': self.updated_fields or []
        })
        return data


@dataclass
class UserJoinedCommunityEvent(DomainEvent):
    """用户加入社区事件"""
    user_id: int
    community_id: int

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'community_id': self.community_id
        })
        return data


@dataclass
class UserLeftCommunityEvent(DomainEvent):
    """用户离开社区事件"""
    user_id: int
    community_id: int

    def to_dict(self) -> dict:
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'user_id': self.user_id,
            'community_id': self.community_id
        })
        return data