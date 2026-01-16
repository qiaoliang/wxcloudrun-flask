"""
事件消息领域实体

封装事件消息相关的业务逻辑。
"""
from typing import Optional, List
from datetime import datetime

from database.flask_models import EventMessage


class EventMessageEntity:
    """事件消息领域实体"""

    def __init__(self, message: EventMessage):
        """
        初始化事件消息领域实体

        Args:
            message: SQLAlchemy EventMessage 模型实例
        """
        self._message = message

    @property
    def message(self) -> EventMessage:
        """获取底层的 SQLAlchemy EventMessage 模型"""
        return self._message

    @property
    def message_id(self) -> int:
        """获取消息ID"""
        return self._message.message_id

    @property
    def event_id(self) -> int:
        """获取事件ID"""
        return self._message.event_id

    @property
    def sender_id(self) -> int:
        """获取发送者ID"""
        return self._message.sender_id

    @property
    def message_content(self) -> Optional[str]:
        """获取消息内容"""
        return self._message.message_content

    @property
    def status(self) -> int:
        """获取消息状态"""
        return self._message.status

    @property
    def message_type(self) -> str:
        """获取消息类型"""
        return self._message.message_type

    @property
    def media_url(self) -> Optional[str]:
        """获取媒体URL"""
        return self._message.media_url

    @property
    def media_duration(self) -> Optional[int]:
        """获取媒体时长"""
        return self._message.media_duration

    @property
    def message_tags(self) -> Optional[List]:
        """获取消息标签"""
        return self._message.message_tags

    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        return self._message.created_at

    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        return self._message.updated_at

    def is_valid(self) -> bool:
        """
        检查消息是否有效

        Returns:
            bool: 是否有效
        """
        return self._message.status == 1

    def is_cancelled(self) -> bool:
        """
        检查消息是否已取消

        Returns:
            bool: 是否已取消
        """
        return self._message.status == 2

    def cancel(self) -> None:
        """取消消息"""
        self._message.status = 2
        self._message.updated_at = datetime.now()

    def is_text_message(self) -> bool:
        """
        是否为文字消息

        Returns:
            bool: 是否为文字消息
        """
        return self._message.message_type == 'text'

    def is_voice_message(self) -> bool:
        """
        是否为语音消息

        Returns:
            bool: 是否为语音消息
        """
        return self._message.message_type == 'voice'

    def is_image_message(self) -> bool:
        """
        是否为图片消息

        Returns:
            bool: 是否为图片消息
        """
        return self._message.message_type == 'image'

    def has_media(self) -> bool:
        """
        是否包含媒体

        Returns:
            bool: 是否包含媒体
        """
        return self._message.media_url is not None

    def get_tags(self) -> List[str]:
        """
        获取消息标签列表

        Returns:
            标签列表
        """
        return self._message.message_tags if self._message.message_tags else []

    def add_tag(self, tag: str) -> None:
        """
        添加标签

        Args:
            tag: 标签内容
        """
        if self._message.message_tags is None:
            self._message.message_tags = []
        if tag not in self._message.message_tags:
            self._message.message_tags.append(tag)
            self._message.updated_at = datetime.now()

    def remove_tag(self, tag: str) -> None:
        """
        移除标签

        Args:
            tag: 标签内容
        """
        if self._message.message_tags and tag in self._message.message_tags:
            self._message.message_tags.remove(tag)
            self._message.updated_at = datetime.now()

    def __eq__(self, other) -> bool:
        if not isinstance(other, EventMessageEntity):
            return False
        return self._message.message_id == other._message.message_id

    def __hash__(self) -> int:
        return hash(self._message.message_id)