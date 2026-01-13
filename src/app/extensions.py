"""
Flask扩展初始化模块
集中管理所有Flask扩展，避免循环导入问题
"""

from flask_sqlalchemy import SQLAlchemy
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 数据库扩展
db = SQLAlchemy()

# 速率限制扩展
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",  # 使用内存存储（测试环境）
    strategy="fixed-window"  # 固定窗口策略
)

# 其他扩展可以在这里初始化
# 例如：from flask_migrate import Migrate
# migrate = Migrate()

# 注意：扩展实例在这里创建，但需要在应用工厂中初始化