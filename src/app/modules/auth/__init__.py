"""
认证模块蓝图定义
"""
from flask import Blueprint

# 定义认证蓝图
auth_bp = Blueprint(
    name='auth',
    import_name=__name__,
    url_prefix='/auth'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes