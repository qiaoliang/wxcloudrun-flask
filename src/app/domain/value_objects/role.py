"""
角色值对象
"""
from dataclasses import dataclass
from enum import Enum


class RoleType(Enum):
    """角色类型枚举"""
    UNSET = 0
    SOLO = 1
    STAFF = 2
    MANAGER = 3
    SUPER_ADMIN = 4

    @property
    def name(self) -> str:
        """获取角色名称"""
        return {
            RoleType.UNSET: "未设置",
            RoleType.SOLO: "普通用户",
            RoleType.STAFF: "社区专员",
            RoleType.MANAGER: "社区主管",
            RoleType.SUPER_ADMIN: "超级系统管理员"
        }.get(self, "未知角色")


@dataclass(frozen=True)
class Role:
    """角色值对象"""
    value: RoleType

    @classmethod
    def from_int(cls, value: int) -> 'Role':
        """从整数值创建角色"""
        try:
            return cls(RoleType(value))
        except ValueError:
            raise ValueError(f"无效的角色值: {value}")

    @property
    def role_id(self) -> int:
        """获取角色ID"""
        return self.value.value

    @property
    def role_name(self) -> str:
        """获取角色名称"""
        return self.value.name

    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.value in [RoleType.MANAGER, RoleType.SUPER_ADMIN]

    def is_super_admin(self) -> bool:
        """是否为超级管理员"""
        return self.value == RoleType.SUPER_ADMIN

    def is_staff(self) -> bool:
        """是否为工作人员"""
        return self.value in [RoleType.STAFF, RoleType.MANAGER, RoleType.SUPER_ADMIN]

    def can_manage_community(self) -> bool:
        """是否可以管理社区"""
        return self.value in [RoleType.MANAGER, RoleType.SUPER_ADMIN]

    def __str__(self) -> str:
        return self.role_name

    def __eq__(self, other) -> bool:
        if not isinstance(other, Role):
            return False
        return self.value == other.value

    def __hash__(self) -> int:
        return hash(self.value)