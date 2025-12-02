import os
import time
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
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

# 检查是否为测试环境，如果是则使用SQLite，否则使用MySQL
# 在模块级别检查，以确保在导入时就设置正确的数据库连接
is_testing = os.environ.get('FLASK_ENV') == 'testing' or 'PYTEST_CURRENT_TEST' in os.environ or os.environ.get('USE_SQLITE_FOR_TESTING', '').lower() == 'true'
if is_testing:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 测试时使用SQLite内存数据库
    app.config['TESTING'] = True
else:
    # 设定数据库链接，添加字符集设置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(config.username, config.password,
                                                                                 config.db_address)

# 禁用SQLAlchemy的修改跟踪以避免警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 初始化Flask-Migrate
migrate = Migrate(app, db)

# 加载配置
app.config.from_object('config')

# 加载控制器
from wxcloudrun import views

# 创建数据库表（仅在非测试环境或明确需要时创建）
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord
if not is_testing:
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

# 在应用启动时检查并应用挂起的迁移
def run_pending_migrations():
    """运行挂起的数据库迁移"""
    try:
        from flask_migrate import upgrade
        upgrade()
        app.logger.info("数据库迁移成功完成")
    except Exception as e:
        app.logger.error(f"数据库迁移失败: {str(e)}")
        raise

# 根据环境变量决定是否自动运行迁移
if not is_testing and os.environ.get('AUTO_RUN_MIGRATIONS', 'false').lower() != 'false':
    with app.app_context():
        run_pending_migrations()
