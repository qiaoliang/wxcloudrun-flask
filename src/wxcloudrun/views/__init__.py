"""
视图模块初始化文件
导入所有视图模块，以便在主应用中注册
"""

# 导入所有视图模块以注册路由
from . import auth
from . import user
from . import checkin
from . import supervision
from . import share
from . import sms
from . import misc

# 确保所有模块的装饰器被导入
from ..decorators import login_required

__all__ = ['auth', 'user', 'checkin', 'supervision', 'share', 'sms', 'misc']