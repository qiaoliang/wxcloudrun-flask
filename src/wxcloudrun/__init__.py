import os
import sys
import logging
from flask import Flask

# 添加父目录到路径，以便导入 config 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from config_manager import get_database_config
from database.flask_models import db  # 导入Flask-SQLAlchemy实例

# 配置日志
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'app.log')),
        logging.StreamHandler()
    ]
)

# 初始化 Flask web 应用
app = Flask(__name__, instance_relative_config=True)

# 加载配置
app.config.from_object('config')

# 配置调试模式
app.config['DEBUG'] = config.DEBUG

# 获取数据库配置（用于日志记录）
db_config = get_database_config()
app.config['DATABASE_CONFIG'] = db_config

# 初始化Flask-SQLAlchemy
db.init_app(app)

# 导入Flask-SQLAlchemy模型
from database.flask_models import (
    User, Community, CheckinRule, CheckinRecord,
    UserAuditLog, Counters
)

# 导入视图模块以注册路由
from .views import misc, sms, auth, user, checkin, supervision, share, community, community_checkin, user_checkin, events

# 注册事件蓝图
from .views.events import register_events_blueprint
register_events_blueprint(app)
from .background_tasks import start_missing_check_service

# 在 unit 环境下初始化默认数据
import config_manager
if config_manager.is_unit_environment():
    with app.app_context():
        app.logger.info("默认社区初始化已在数据库迁移完成后自动执行")

# 加载配置
app.config.from_object('config')

# 在 unit 环境下不启动后台服务
if not config_manager.is_unit_environment():
    app.logger.info(f"app.debug={app.debug}")
    try:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            app.logger.info(f"# 启动后台的打卡扫描检测服务")
            start_missing_check_service()
    except Exception as e:
        app.logger.error(f"启动后台missing服务失败: {str(e)}")
else:
    app.logger.info("unit 环境下不启动后台服务")
