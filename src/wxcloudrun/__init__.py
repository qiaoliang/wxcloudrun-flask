import os
import sys
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
# Flask-Migrate 已移除，使用独立的 Alembic 迁移系统

# 添加父目录到路径，以便导入 config 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from config_manager import get_database_config

# 配置日志
# 确保日志目录存在
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(logs_dir, 'migration.log')),
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

# Flask-Migrate 已移除，现在使用独立的 Alembic 迁移系统
# 迁移脚本位于 src/alembic/ 目录

# 现在再导入模型和视图，避免循环依赖
from .model import Counters, User, CheckinRule, CheckinRecord, Community, CommunityAdmin, CommunityApplication  # noqa: F401
from .model_community_extensions import CommunityStaff, CommunityMember  # noqa: F401
# 导入各个视图模块以注册路由
from .views import misc, sms, auth, user, checkin, supervision, share, community  # noqa: F401
from .background_tasks import start_missing_check_service  # noqa: F401

# 在 unit 环境下，为内存数据库创建表
import config_manager
if config_manager.is_unit_environment():
    with app.app_context():
        db.create_all()
        app.logger.info("在内存数据库中创建了所有表")
        
        # 初始化默认社区
        try:
            from .community_service import CommunityService
            default_community = CommunityService.get_or_create_default_community()
            app.logger.info(f"默认社区初始化完成: {default_community.name} (ID: {default_community.community_id})")
        except Exception as e:
            app.logger.error(f"初始化默认社区失败: {str(e)}", exc_info=True)

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
