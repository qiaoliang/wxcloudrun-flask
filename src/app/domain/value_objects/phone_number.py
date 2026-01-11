"""
手机号值对象
"""
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PhoneNumber:
    """手机号值对象"""
    value: str

    def __post_init__(self):
        """验证手机号格式"""
        if not self._is_valid_phone(self.value):
            raise ValueError(f"无效的手机号: {self.value}")

    def _is_valid_phone(self, phone: str) -> bool:
        """验证手机号格式"""
        pattern = r'^1[3-9]\d{9}$'
        return re.match(pattern, phone) is not None

    @property
    def masked(self) -> str:
        """获取脱敏手机号"""
        if len(self.value) >= 7:
            return f"{self.value[:3]}****{self.value[-4:]}"
        return self.value

    def __str__(self) -> str:
        return self.value

    def __eq__(self, other) -> bool:
        if not isinstance(other, PhoneNumber):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)