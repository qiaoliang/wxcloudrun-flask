"""
Flask扩展初始化模块
集中管理所有Flask扩展，避免循环导入问题
"""

from flask_sqlalchemy import SQLAlchemy

# 数据库扩展
db = SQLAlchemy()

# 其他扩展可以在这里初始化
# 例如：from flask_migrate import Migrate
# migrate = Migrate()

# 注意：扩展实例在这里创建，但需要在应用工厂中初始化