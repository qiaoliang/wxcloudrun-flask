import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# 添加父目录到路径，以便导入 config 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from config_manager import get_database_config
from database import bind_flask_db

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

# 配置调试模式
app.config['DEBUG'] = config.DEBUG

# 获取数据库配置并应用到Flask
db_config = get_database_config()
app.config['SQLALCHEMY_DATABASE_URI'] = db_config['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化 Flask-SQLAlchemy（仅用于Web服务）
db = SQLAlchemy(app)

# 绑定到新的数据库核心
db_core = bind_flask_db(db)

# 导入模型（使用新的数据库模块）
from database.models import (
    User, Community, CheckinRule, CheckinRecord, 
    SupervisionRuleRelation, CommunityStaff, CommunityMember,
    CommunityApplication, ShareLink, ShareLinkAccessLog,
    VerificationCode, UserAuditLog, Counters
)

# 导入视图模块以注册路由
from .views import misc, sms, auth, user, checkin, supervision, share, community
from .background_tasks import start_missing_check_service

# 在 unit 环境下初始化默认数据
import config_manager
if config_manager.is_unit_environment():
    with app.app_context():
        try:
            from .community_service import CommunityService
            default_community = CommunityService.get_or_create_default_community()
            app.logger.info(f"默认社区初始化完成: {default_community.name} (ID: {default_community.community_id})")
        except Exception as e:
            app.logger.error(f"初始化默认社区失败: {str(e)}", exc_info=True)

# 加载配置
app.config.from_object('config')

# 启动后台服务
try:
    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
        start_missing_check_service()
except Exception as e:
    app.logger.error(f"启动后台missing服务失败: {str(e)}")
