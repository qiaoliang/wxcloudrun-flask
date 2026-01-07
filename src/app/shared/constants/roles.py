"""
角色常量定义 - 前后端保持一致
role_id 用于判断，role_name 仅用于显示
"""


class Role:
    """角色 ID 常量 - 用于代码判断"""

    UNSET = 0  # 未设置
    SOLO = 1  # 普通用户 (独居者)
    STAFF = 2  # 社区专员
    MANAGER = 3  # 社区主管
    SUPER_ADMIN = 4  # 超级系统管理员


class RoleName:
    """角色名称常量 - 用于显示"""

    UNSET = "未设置"
    SOLO = "普通用户"
    STAFF = "社区专员"
    MANAGER = "社区主管"
    SUPER_ADMIN = "超级系统管理员"


# role_id 到 role_name 的映射（用于显示）
ROLE_ID_TO_NAME = {
    Role.UNSET: RoleName.UNSET,
    Role.SOLO: RoleName.SOLO,
    Role.STAFF: RoleName.STAFF,
    Role.MANAGER: RoleName.MANAGER,
    Role.SUPER_ADMIN: RoleName.SUPER_ADMIN,
}

# role_name 到 role_id 的映射（用于 API 参数解析，如果有需要）
ROLE_NAME_TO_ID = {v: k for k, v in ROLE_ID_TO_NAME.items()}

# 社区工作人员角色列表（用于权限判断）
COMMUNITY_STAFF_ROLES = [Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN]

# 管理员角色列表（社区主管 + 超级管理员）
ADMIN_ROLES = [Role.MANAGER, Role.SUPER_ADMIN]

# 所有有效角色列表
ALL_VALID_ROLES = [Role.SOLO, Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN]

# 数据库约束使用的角色值列表（用于 CheckConstraint）
DB_ROLE_CONSTRAINT_VALUES = [Role.UNSET, Role.SOLO, Role.STAFF, Role.MANAGER, Role.SUPER_ADMIN]

# CommunityStaff 表的 role 字段值（字符串类型）
STAFF_ROLE_MANAGER = "manager"  # 社区主管
STAFF_ROLE_STAFF = "staff"  # 社区专员

# CommunityStaff role 到 User role 的映射
STAFF_ROLE_TO_USER_ROLE = {STAFF_ROLE_MANAGER: Role.MANAGER, STAFF_ROLE_STAFF: Role.STAFF}
