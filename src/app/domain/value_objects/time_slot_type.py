"""
时间段类型值对象
"""
from dataclasses import dataclass
from enum import Enum
from datetime import time


class TimeSlotType(Enum):
    """时间段类型枚举"""
    MORNING = 0    # 早晨 (8:00)
    NOON = 1      # 中午 (12:00)
    EVENING = 2   # 傍晚 (18:00)
    NIGHT = 3     # 晚上 (21:00)
    CUSTOM = 4    # 自定义

    @property
    def name(self) -> str:
        """获取时间段类型名称"""
        return {
            TimeSlotType.MORNING: "早晨",
            TimeSlotType.NOON: "中午",
            TimeSlotType.EVENING: "傍晚",
            TimeSlotType.NIGHT: "晚上",
            TimeSlotType.CUSTOM: "自定义"
        }.get(self, "未知时间段")

    @property
    def default_time(self) -> time:
        """获取默认时间"""
        return {
            TimeSlotType.MORNING: time(8, 0),
            TimeSlotType.NOON: time(12, 0),
            TimeSlotType.EVENING: time(18, 0),
            TimeSlotType.NIGHT: time(21, 0),
            TimeSlotType.CUSTOM: None
        }.get(self)


@dataclass(frozen=True)
class TimeSlot:
    """时间段值对象"""
    value: TimeSlotType
    custom_time: str = None

    @classmethod
    def from_int(cls, value: int, custom_time: str = None) -> 'TimeSlot':
        """从整数值创建时间段"""
        try:
            return cls(TimeSlotType(value), custom_time)
        except ValueError:
            raise ValueError(f"无效的时间段值: {value}")

    @property
    def time_slot_id(self) -> int:
        """获取时间段ID"""
        return self.value.value

    @property
    def time_slot_name(self) -> str:
        """获取时间段名称"""
        return self.value.name

    @property
    def is_custom(self) -> bool:
        """是否为自定义时间段"""
        return self.value == TimeSlotType.CUSTOM

    def get_checkin_time(self) -> time:
        """
        获取打卡时间

        Returns:
            打卡时间，如果是自定义时间段则返回自定义时间
        """
        if self.value == TimeSlotType.CUSTOM and self.custom_time:
            try:
                return time.fromisoformat(self.custom_time)
            except ValueError:
                pass
        return self.value.default_time

    def __str__(self) -> str:
        if self.is_custom and self.custom_time:
            return f"自定义 ({self.custom_time})"
        return self.time_slot_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeSlot):
            return False
        return self.value == other.value and self.custom_time == other.custom_time

    def __hash__(self) -> int:
        return hash((self.value, self.custom_time))