"""
共享组件模块
重新导出所有共享组件，便于模块导入
"""

# 重新导出响应模块
from .response import (
    make_succ_empty_response,
    make_succ_response,
    make_err_response
)

# 重新导出装饰器模块
from .decorators import (
    login_required,
    require_token,
    require_community_staff_member,
    require_community_membership
)

# 重新导出工具函数
from .utils.auth import (
    verify_token,
    require_role,
    require_community_admin,
    require_community_staff,
    require_community_manager,
    require_super_admin,
    check_community_permission,
    get_current_user,
    generate_jwt_token,
    generate_refresh_token
)