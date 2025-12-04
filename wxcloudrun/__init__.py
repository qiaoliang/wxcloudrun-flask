import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import config
from config_manager import get_database_config

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)

# 获取数据库配置
db_config = get_database_config()
app.config['DEBUG'] = config.DEBUG

# 根据环境配置设置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = db_config['SQLALCHEMY_DATABASE_URI']
app.config['TESTING'] = db_config['TESTING']

# 禁用SQLAlchemy的修改跟踪以避免警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载配置
app.config.from_object('config')

# 加载控制器
from wxcloudrun import views

from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord
try:
    with app.app_context():
        # 先尝试建立连接，再执行create_all
        # 这样可以确保连接可用后再执行数据库操作
        try:
            with db.engine.connect() as connection:
                pass  # 简单测试连接是否可用
        except Exception as connect_error:
            app.logger.warning(f"数据库连接测试失败: {str(connect_error)}")
            # 不要阻止应用启动，只是记录错误
            app.logger.error("无法连接到数据库，应用可能无法正常工作。")
        else:
            db.create_all()
            app.logger.info("数据库连接成功！")
            # 检查 Counters 表是否已创建
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            app.logger.info(f"数据库中已存在的表: {tables}")
            if 'Counters' not in tables:
                app.logger.warning("警告: Counters 表不存在")
            else:
                app.logger.info("Counters 表已存在")
except Exception as e:
    app.logger.error(f"数据库初始化失败: {str(e)}")
    app.logger.error("应用将继续启动，但数据库功能可能无法使用。")
