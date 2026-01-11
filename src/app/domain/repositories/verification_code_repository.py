"""
验证码仓储接口
"""
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime

from database.flask_models import VerificationCode


class VerificationCodeRepository(ABC):
    """验证码仓储接口"""

    @abstractmethod
    def find_by_id(self, code_id: int) -> Optional[VerificationCode]:
        """
        根据ID查找验证码

        Args:
            code_id: 验证码ID

        Returns:
            验证码对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_by_phone_and_purpose(self, phone_number: str, purpose: str) -> Optional[VerificationCode]:
        """
        根据手机号和用途查找验证码

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            验证码对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_valid_by_phone_and_purpose(self, phone_number: str, purpose: str) -> Optional[VerificationCode]:
        """
        根据手机号和用途查找有效验证码（未过期且未使用）

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            验证码对象，如果不存在则返回 None
        """
        pass

    @abstractmethod
    def find_expired_codes(self, before: datetime) -> List[VerificationCode]:
        """
        查找过期的验证码

        Args:
            before: 过期时间点

        Returns:
            验证码列表
        """
        pass

    @abstractmethod
    def save(self, code: VerificationCode) -> VerificationCode:
        """
        保存验证码

        Args:
            code: 验证码对象

        Returns:
            保存后的验证码对象
        """
        pass

    @abstractmethod
    def update_last_sent_time(self, code: VerificationCode, sent_time: datetime) -> VerificationCode:
        """
        更新验证码的最后发送时间

        Args:
            code: 验证码对象
            sent_time: 发送时间

        Returns:
            更新后的验证码对象
        """
        pass

    @abstractmethod
    def mark_as_used(self, code: VerificationCode) -> VerificationCode:
        """
        标记验证码为已使用

        Args:
            code: 验证码对象

        Returns:
            更新后的验证码对象
        """
        pass

    @abstractmethod
    def delete(self, code_id: int) -> bool:
        """
        删除验证码

        Args:
            code_id: 验证码ID

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def delete_by_phone_and_purpose(self, phone_number: str, purpose: str) -> bool:
        """
        根据手机号和用途删除验证码

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            是否删除成功
        """
        pass

    @abstractmethod
    def delete_expired_codes(self, before: datetime) -> int:
        """
        删除过期的验证码

        Args:
            before: 过期时间点

        Returns:
            删除的验证码数量
        """
        pass

    @abstractmethod
    def count_recent_sent(self, phone_number: str, purpose: str, minutes: int = 1) -> int:
        """
        统计最近N分钟内发送的验证码数量

        Args:
            phone_number: 手机号
            purpose: 用途
            minutes: 分钟数

        Returns:
            验证码数量
        """
        pass