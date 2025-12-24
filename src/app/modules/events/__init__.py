"""
事件管理模块蓝图定义
"""
from flask import Blueprint

# 定义事件管理蓝图
events_bp = Blueprint(
    name='events',
    import_name=__name__,
    url_prefix='/events'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes