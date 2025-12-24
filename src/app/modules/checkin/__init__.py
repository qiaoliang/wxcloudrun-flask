"""
打卡功能模块蓝图定义
"""
from flask import Blueprint

# 定义打卡功能蓝图
checkin_bp = Blueprint(
    name='checkin',
    import_name=__name__,
    url_prefix='/checkin'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes