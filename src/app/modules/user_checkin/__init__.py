"""
用户打卡模块蓝图定义
"""
from flask import Blueprint

# 定义用户打卡蓝图
user_checkin_bp = Blueprint(
    name='user_checkin',
    import_name=__name__,
    url_prefix='/user_checkin'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes