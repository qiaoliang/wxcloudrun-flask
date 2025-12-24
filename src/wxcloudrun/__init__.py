"""
wxcloudrun 模块
提供业务服务层的访问接口，不再创建全局应用实例
"""

import os
import sys

# 添加父目录到路径，以便导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def get_app():
    """
    获取Flask应用实例（兼容性函数）
    
    Returns:
        Flask应用实例
    """
    from app import create_app
    return create_app()


# 为了向后兼容，保留app变量，但改为函数调用
# 注意：这个变量只用于兼容性，新代码应该使用get_app()函数
def _lazy_app():
    """延迟加载应用实例"""
    if not hasattr(_lazy_app, '_app'):
        _lazy_app._app = get_app()
    return _lazy_app._app

# 创建一个属性访问器，使得app变量表现得像原来的全局变量
class AppProxy:
    """应用代理类，用于向后兼容"""
    
    def __getattr__(self, name):
        app = _lazy_app()
        return getattr(app, name)
    
    def __call__(self, *args, **kwargs):
        app = _lazy_app()
        return app(*args, **kwargs)

# 创建代理实例
app = AppProxy()
