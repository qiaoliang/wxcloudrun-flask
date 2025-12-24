"""
分享功能模块蓝图定义
"""
from flask import Blueprint

# 定义分享功能蓝图
share_bp = Blueprint(
    name='share',
    import_name=__name__,
    url_prefix='/share'  # 蓝图级前缀
)

# 延迟导入路由避免循环依赖
from . import routes