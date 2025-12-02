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

# 检查是否为测试环境，如果是则使用SQLite，否则使用MySQL
# 在模块级别检查，以确保在导入时就设置正确的数据库连接
is_unit_testing = os.environ.get('USE_SQLITE_FOR_TESTING', '').lower() == 'true'
is_testing = is_unit_testing or os.environ.get('FLASK_ENV') == 'testing' or 'PYTEST_CURRENT_TEST' in os.environ
if is_testing:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 测试时使用SQLite内存数据库
    app.config['TESTING'] = True
else:
    # 设定数据库链接，添加字符集设置
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://{}:{}@{}/flask_demo?charset=utf8mb4'.format(config.username, config.password,
                                                                                 config.db_address)

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
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord
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

# 根据环境变量决定是否自动创建表
# 单元测试使用SQLite内存数据库，不需要创建表
# 功能测试和生产环境使用MySQL，需要创建表
# 注意：在Docker环境中，表创建通过init_database.py脚本处理，不需要在应用启动时运行
if not is_unit_testing and os.environ.get('AUTO_CREATE_TABLES', 'false').lower() != 'false' and os.environ.get('DOCKER_ENV') != 'true':
    # 延迟执行表创建，确保应用完全启动后再运行
    import threading
    import time
    
    def delayed_table_creation():
        # 等待一段时间确保数据库完全就绪
        time.sleep(5)
        create_tables_if_needed()
    
    # 在后台线程中运行表创建
    table_thread = threading.Thread(target=delayed_table_creation)
    table_thread.daemon = True
    table_thread.start()
