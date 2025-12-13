"""
数据库模块
提供独立的数据库功能，支持多种使用模式
"""

from .core import (
    DatabaseCore,
    get_database,
    initialize_for_test,
    initialize_for_standalone,
    bind_flask_db,
    get_session,
    reset_all
)
from . import models

# 导出的公共接口
__all__ = [
    'DatabaseCore',
    'get_database',
    'initialize_for_test',
    'initialize_for_standalone',
    'bind_flask_db',
    'get_session',
    'reset_all',
    'models'
]