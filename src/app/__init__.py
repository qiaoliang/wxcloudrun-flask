"""
Flask应用工厂模块
创建可配置的Flask应用实例，支持多环境和Blueprint模块化架构
"""

import os
import sys
import logging
from flask import Flask

# 添加父目录到路径，以便导入config模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from config_manager import get_database_config
from .extensions import db  # 从扩展模块导入

# 配置日志
def configure_logging(app):
    """配置应用日志"""
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

def create_app(config_name=None):
    """
    创建Flask应用实例（工厂函数）
    
    Args:
        config_name: 配置名称，如 'development', 'testing', 'production'
                    如果为None，则根据ENV_TYPE自动确定
    
    Returns:
        Flask应用实例
    """
    # 1. 创建Flask应用实例
    app = Flask(__name__, instance_relative_config=True)
    
    # 2. 配置日志
    configure_logging(app)
    
    # 3. 加载配置
    app.config.from_object('config')
    
    # 配置调试模式
    app.config['DEBUG'] = config.DEBUG
    
    # 获取数据库配置（用于日志记录）
    db_config = get_database_config()
    app.config['DATABASE_CONFIG'] = db_config
    
    # 4. 初始化扩展
    db.init_app(app)
    
    # 5. 导入Flask-SQLAlchemy模型（确保在db.init_app之后）
    # 注意：模型导入必须在db.init_app之后，但在注册蓝图之前
    from database.flask_models import (
        User, Community, CheckinRule, CheckinRecord,
        UserAuditLog, Counters
    )
    
    # 6. 注册蓝图
    register_blueprints(app)
    
    # 7. 注册错误处理器
    register_error_handlers(app)
    
    # 8. 启动后台任务（非unit环境）
    start_background_tasks(app)
    
    # 9. 在 unit 环境下初始化默认数据
    import config_manager
    if config_manager.is_unit_environment():
        with app.app_context():
            app.logger.info("默认社区初始化已在数据库迁移完成后自动执行")
    
    return app


def register_blueprints(app):
    """注册所有蓝图到Flask应用"""
    # 导入所有蓝图
    from .modules.auth import auth_bp
    from .modules.user import user_bp
    from .modules.community import community_bp
    from .modules.checkin import checkin_bp
    from .modules.supervision import supervision_bp
    from .modules.sms import sms_bp
    from .modules.share import share_bp
    from .modules.events import events_bp
    from .modules.community_checkin import community_checkin_bp
    from .modules.user_checkin import user_checkin_bp
    from .modules.misc import misc_bp
    
    # 注册蓝图，统一添加/api前缀
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(community_bp, url_prefix='/api')
    app.register_blueprint(checkin_bp, url_prefix='/api')
    app.register_blueprint(supervision_bp, url_prefix='/api')
    app.register_blueprint(sms_bp, url_prefix='/api')
    app.register_blueprint(share_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(community_checkin_bp, url_prefix='/api')
    app.register_blueprint(user_checkin_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')
    
    app.logger.info("所有蓝图已成功注册")


def register_error_handlers(app):
    """注册全局错误处理器"""
    from app.shared.response import make_err_response
    
    @app.errorhandler(404)
    def page_not_found(e):
        return make_err_response({}, '接口不存在'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f'服务器内部错误: {str(e)}')
        return make_err_response({}, '服务器内部错误'), 500
    
    @app.errorhandler(401)
    def unauthorized(e):
        return make_err_response({}, '未授权访问'), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return make_err_response({}, '禁止访问'), 403


def start_background_tasks(app):
    """启动后台任务"""
    import config_manager
    if not config_manager.is_unit_environment():
        app.logger.info(f"app.debug={app.debug}")
        try:
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
                app.logger.info(f"# 启动后台的打卡扫描检测服务")
                # 导入并启动后台任务
                from wxcloudrun.background_tasks import start_missing_check_service
                start_missing_check_service()
        except Exception as e:
            app.logger.error(f"启动后台missing服务失败: {str(e)}")
    else:
        app.logger.info("unit 环境下不启动后台服务")