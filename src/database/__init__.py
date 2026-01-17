"""
数据库模块
提供Flask-SQLAlchemy数据库功能
"""

from . import flask_models as models

# 导出的公共接口
__all__ = [
    'models',
]

def get_initialization():
    """延迟导入初始化模块，避免循环导入"""
    from .initialization import create_superadmin_and_default_community
    return create_superadmin_and_default_community

# 为了向后兼容，添加一个属性
create_superadmin_and_default_community = property(lambda self: get_initialization())