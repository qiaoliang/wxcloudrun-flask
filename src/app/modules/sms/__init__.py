"""
短信服务模块蓝图定义
"""
from flask import Blueprint

# 定义短信服务蓝图
sms_bp = Blueprint(
    name='sms',
    import_name=__name__
)

# 延迟导入路由避免循环依赖
from . import routes