"""
社区打卡模块蓝图定义
"""
from flask import Blueprint

# 定义社区打卡蓝图
community_checkin_bp = Blueprint(
    name='community_checkin',
    import_name=__name__,
    url_prefix='/community_checkin'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes