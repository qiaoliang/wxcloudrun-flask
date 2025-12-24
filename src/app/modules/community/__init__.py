"""
社区管理模块蓝图定义
"""
from flask import Blueprint

# 定义社区管理蓝图
community_bp = Blueprint(
    name='community',
    import_name=__name__
)

# 延迟导入路由避免循环依赖
from . import routes