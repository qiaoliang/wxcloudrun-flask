import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
from config_manager import get_database_config

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

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

# 创建数据库表（仅在非测试环境或明确需要时创建）
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord
if not db_config['TESTING']:
    # 添加数据库连接重试机制
    max_retries = 60  # 最多等待60次（120秒）
    retry_count = 0
    db_connected = False
    
    while not db_connected and retry_count < max_retries:
        try:
            with app.app_context():
                # 先尝试建立连接，再执行create_all
                # 这样可以确保连接可用后再执行数据库操作
                with db.engine.connect() as connection:
                    pass  # 简单测试连接是否可用
                
                db.create_all()
                
                
                
            db_connected = True
            app.logger.info("数据库连接成功！")
            # 检查 Counters 表是否已创建
            from sqlalchemy import inspect
            with app.app_context():
                inspector = inspect(db.engine)
                tables = inspector.get_table_names()
            app.logger.info(f"数据库中已存在的表: {tables}")
            if 'Counters' not in tables:
                app.logger.warning("警告: Counters 表不存在")
            else:
                app.logger.info("Counters 表已存在")
        except Exception as e:
            retry_count += 1
            app.logger.error(f"数据库连接失败，正在重试 ({retry_count}/{max_retries}): {str(e)}")
            time.sleep(2)  # 等待2秒后重试，给数据库更多时间处理
    
    if not db_connected:
        app.logger.error("无法连接到数据库，应用可能无法正常工作。")
