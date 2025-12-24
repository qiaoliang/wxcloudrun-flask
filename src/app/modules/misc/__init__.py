"""
杂项功能模块蓝图定义
"""
from flask import Blueprint

# 定义杂项功能蓝图
misc_bp = Blueprint(
    name='misc',
    import_name=__name__,
    url_prefix='/misc'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes