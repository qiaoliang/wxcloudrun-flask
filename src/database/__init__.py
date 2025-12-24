"""
数据库模块
提供Flask-SQLAlchemy数据库功能
"""

from . import flask_models as models
from .initialization import create_super_admin_and_default_community

# 导出的公共接口
__all__ = [
    'models',
    'create_super_admin_and_default_community'
]