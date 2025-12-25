"""
监督功能模块蓝图定义
"""
from flask import Blueprint

# 定义监督功能蓝图
supervision_bp = Blueprint(
    name='supervision',
    import_name=__name__
)

# 延迟导入路由避免循环依赖
from . import routes