import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import config
from config_manager import get_database_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler()
    ]
)

# 初始化 Flask web 应用
app = Flask(__name__, instance_relative_config=True)

# 这是 Flask 的调试模式配置 和 测试模式标志, 影响某些 Flask 扩展的行为（如错误处理）
app.config['DEBUG'] = config.DEBUG

# 获取数据库配置
db_config = get_database_config()
# 根据环境配置设置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = db_config['SQLALCHEMY_DATABASE_URI']
# 禁用SQLAlchemy的修改跟踪以避免警告
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化DB操作对象
db = SQLAlchemy(app)

# 初始化 Flask-Migrate
migrate = Migrate(app, db)

# 现在再导入模型和视图，避免循环依赖
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord  # noqa: F401
from wxcloudrun import views  # noqa: F401
from wxcloudrun.background_tasks import start_missing_check_service  # noqa: F401

# 加载配置
app.config.from_object('config')

# 启动后台missing标记服务
try:
    import os as _os
    # 仅在主进程中启动，避免debug模式下重复启动
    if _os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_missing_check_service()
except Exception as e:
    app.logger.error(f"启动后台missing服务失败: {str(e)}")
