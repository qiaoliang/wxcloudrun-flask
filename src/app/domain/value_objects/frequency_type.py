"""
频率类型值对象
"""
from dataclasses import dataclass
from enum import Enum


class FrequencyType(Enum):
    """频率类型枚举"""
    DAILY = 0    # 每天
    WEEKLY = 1   # 每周
    MONTHLY = 2  # 每月

    @property
    def name(self) -> str:
        """获取频率类型名称"""
        return {
            FrequencyType.DAILY: "每天",
            FrequencyType.WEEKLY: "每周",
            FrequencyType.MONTHLY: "每月"
        }.get(self, "未知频率")


@dataclass(frozen=True)
class Frequency:
    """频率值对象"""
    value: FrequencyType

    @classmethod
    def from_int(cls, value: int) -> 'Frequency':
        """从整数值创建频率"""
        try:
            return cls(FrequencyType(value))
        except ValueError:
            raise ValueError(f"无效的频率值: {value}")

    @property
    def frequency_id(self) -> int:
        """获取频率ID"""
        return self.value.value

    @property
    def frequency_name(self) -> str:
        """获取频率名称"""
        return self.value.name

    def __str__(self) -> str:
        return self.frequency_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Frequency):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)