"""
用户管理模块蓝图定义
"""
from flask import Blueprint

# 定义用户管理蓝图
user_bp = Blueprint(
    name='user',
    import_name=__name__
)

# 延迟导入路由避免循环依赖
from . import routes