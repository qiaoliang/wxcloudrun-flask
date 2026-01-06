"""
社区管理模块路由
按功能领域拆分为多个子模块
"""

# 导入所有子模块，注册路由到 community_bp
# 注意：这些导入会自动将路由注册到 community_bp Blueprint

# 工具函数（需要先导入，因为其他模块依赖）
from . import utils

# 社区基础管理
from . import community_basic

# 社区操作
from . import community_operations

# 社区申请管理
from . import community_applications

# 社区工作人员管理
from . import community_staff

# 社区成员管理
from . import community_members

# 用户搜索
from . import user_search

# 用户社区操作
from . import user_community_ops

# 权限检查
from . import permissions

# 导出所有模块，确保路由被注册
__all__ = [
    'utils',
    'community_basic',
    'community_operations',
    'community_applications',
    'community_staff',
    'community_members',
    'user_search',
    'user_community_ops',
    'permissions'
]