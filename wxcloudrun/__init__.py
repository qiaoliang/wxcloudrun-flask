import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# from flask_migrate import Migrate  # 不再使用迁移功能
from flask_cors import CORS
import pymysql
import config

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 配置CORS以支持跨域请求
CORS(app)

# 检查是否为测试环境
is_testing = config.ENV_TYPE in ['unit', 'function']
is_unit_testing = config.ENV_TYPE == 'unit'

# 检查是否为测试环境，如果是则使用SQLite，否则使用MySQL
# 在模块级别检查，以确保在导入时就设置正确的数据库连接
app.config['DB_CONNECTION_URI'] = config.DB_CONNECTION_URI

# 设置SQLAlchemy所需的数据库URI配置
app.config['SQLALCHEMY_DATABASE_URI'] = config.DB_CONNECTION_URI

# 禁用SQLAlchemy的修改跟踪以避免警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 注释掉Flask-Migrate，不再使用迁移功能
# migrate = Migrate(app, db)

# 加载配置
app.config.from_object('config')

# 加载控制器
from wxcloudrun import views

# 创建数据库表（仅在非测试环境或明确需要时创建）
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord, PhoneAuth
# 在Docker环境中，数据库初始化由init_database.py处理，这里跳过连接检查
if not is_testing and os.environ.get('DOCKER_ENV') != 'true':
    # 添加数据库连接重试机制
    max_retries = 30  # 最多等待30次（30秒）
    retry_count = 0
    db_connected = False

    while not db_connected and retry_count < max_retries:
        try:
            with app.app_context():
                # 为确保数据库表结构是最新的，可以在这里应用挂起的迁移
                # 但这通常应在部署脚本中完成，而不是在应用启动时
                # db.create_all() 调用将被Flask-Migrate接管
                db_connected = True
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
            retry_count += 1
            app.logger.error(f"数据库连接失败，正在重试 ({retry_count}/{max_retries}): {str(e)}")
            time.sleep(1)  # 等待1秒后重试

    if not db_connected:
        app.logger.error("无法连接到数据库，应用可能无法正常工作。")

# 在应用启动时检查并创建表（如果需要）
def create_tables_if_needed():
    """创建数据库表（如果不存在）"""
    try:
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()

        # 如果没有任何表，则创建所有表
        if not tables:
            db.create_all()
            app.logger.info("数据库表创建成功")
        else:
            app.logger.info(f"数据库表已存在: {tables}")
    except Exception as e:
        app.logger.error(f"创建表失败: {str(e)}")
        # 不再抛出异常，允许应用继续启动

# 注意：所有环境的数据库初始化现在都由init_database.py脚本统一处理
# 应用启动时不再自动创建表，无论是Docker环境还是非Docker环境
# 这样可以确保所有环境使用一致的初始化流程
app.logger.info("数据库初始化由init_database.py脚本统一处理，应用启动时不执行表创建")
