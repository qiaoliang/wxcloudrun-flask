"""
Flask应用工厂模块
创建可配置的Flask应用实例，支持多环境和Blueprint模块化架构
"""

import os
import sys
import logging
from datetime import datetime
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

    # 创建根日志配置
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(os.path.join(logs_dir, 'app.log')),
            logging.StreamHandler()
        ]
    )

    # 为不同的组件创建独立的 logger
    # 1. App 服务 logger
    app_logger = logging.getLogger('app')
    app_logger.setLevel(logging.INFO)
    app_handler = logging.FileHandler(os.path.join(logs_dir, 'app_service.log'))
    app_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    app_logger.addHandler(app_handler)
    app_logger.propagate = False  # 防止重复日志

    # 2. 定时任务 logger
    scheduler_logger = logging.getLogger('scheduler')
    scheduler_logger.setLevel(logging.INFO)
    scheduler_handler = logging.FileHandler(os.path.join(logs_dir, 'scheduler.log'))
    scheduler_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    scheduler_logger.addHandler(scheduler_handler)
    scheduler_logger.propagate = False  # 防止重复日志

    # 3. 数据库迁移 logger（在 alembic_migration.py 中配置）
    # migration_logger = logging.getLogger('migration')
    # migration_logger.setLevel(logging.INFO)
    # migration_handler = logging.FileHandler(os.path.join(logs_dir, 'migration.log'))
    # migration_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    # migration_logger.addHandler(migration_handler)
    # migration_logger.propagate = False  # 防止重复日志

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
    
    # 配置session支持
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    
    # 4. 初始化扩展
    db.init_app(app)
    
    # 4.5 初始化CORS（支持跨域请求）
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
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
    
    # 8. 注册会话清理
    register_session_cleanup(app)

    # 9. 在 unit 环境下初始化默认数据
    import config_manager
    if config_manager.is_unit_environment():
        with app.app_context():
            app.logger.info("默认社区初始化已在数据库迁移完成后自动执行")

    # 注意：定时任务将在数据库迁移完成后启动（在 run.py 中调用）
    # 这样可以确保数据库表已经创建完成，避免定时任务查询失败

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
    from .modules.community_dashboard import community_dashboard_bp

    # 注册蓝图，统一添加/api前缀
    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(community_bp, url_prefix='/api')
    app.register_blueprint(checkin_bp, url_prefix='/api')
    app.register_blueprint(supervision_bp, url_prefix='/api')
    app.register_blueprint(sms_bp, url_prefix='/api')
    app.register_blueprint(share_bp, url_prefix='/api')
    app.register_blueprint(events_bp, url_prefix='/api')
    app.register_blueprint(community_checkin_bp, url_prefix='/api/community_checkin')
    app.register_blueprint(user_checkin_bp, url_prefix='/api')
    app.register_blueprint(misc_bp, url_prefix='/api')
    app.register_blueprint(community_dashboard_bp, url_prefix='/api')
    
    # 只在主进程中记录此日志，避免 Flask 重启时重复
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
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


def register_session_cleanup(app):
    """注册会话清理处理器"""
    # 在测试环境中不注册 teardown_appcontext，以保持事务的一致性
    import config_manager
    if not config_manager.is_unit_environment():
        @app.teardown_appcontext
        def shutdown_session(exception=None):
            """请求结束后清理数据库会话
            
            Layer 4: 调试仪表 - 事务管理
            - 如果没有异常，提交事务
            - 如果有异常，回滚事务
            - 然后移除会话，释放资源
            """
            try:
                if exception is None:
                    # 没有异常，提交事务
                    db.session.commit()
                else:
                    # 有异常，回滚事务
                    db.session.rollback()
            except Exception as e:
                # 提交或回滚失败，记录错误并强制移除会话
                app.logger.error(f'会话清理失败: {str(e)}')
                try:
                    db.session.rollback()
                except:
                    pass
            finally:
                # 无论成功与否，都移除会话
                db.session.remove()





def start_all_schedulers(app):
    """启动所有定时任务（使用 APScheduler 统一管理）"""
    # 使用独立的 scheduler logger
    scheduler_logger = logging.getLogger('scheduler')
    
    try:
        from flask_apscheduler import APScheduler
        from app.shared.utils.abnormality_calculator import AbnormalityCalculator
        from wxcloudrun.background_tasks import (
            daily_check,
            _process_missed_for_today,
            _process_community_missed_for_today
        )

        # 配置 APScheduler
        app.config['SCHEDULER_API_ENABLED'] = True
        app.config['SCHEDULER_TIMEZONE'] = 'Asia/Shanghai'

        scheduler = APScheduler()
        scheduler.init_app(app)

        # 定义任务函数（供调度器和启动时调用）
        def run_abnormality_calculation():
            """执行异常值计算"""
            with app.app_context():
                try:
                    scheduler_logger.info("开始执行异常值计算任务")
                    stats = AbnormalityCalculator.calculate_all_pending_users()
                    scheduler_logger.info(f"异常值计算完成: {stats}")
                except Exception as e:
                    scheduler_logger.error(f"异常值计算任务执行失败: {str(e)}", exc_info=True)

        def run_daily_check():
            """执行全天规则检查"""
            with app.app_context():
                try:
                    scheduler_logger.info("开始执行全天规则检查任务")
                    daily_check()
                except Exception as e:
                    scheduler_logger.error(f"全天规则检查任务执行失败: {str(e)}", exc_info=True)

        def run_missing_check():
            """执行缺失打卡检查"""
            with app.app_context():
                try:
                    scheduler_logger.info("开始执行缺失打卡检查任务")
                    now = datetime.now()
                    # 常规规则检查（非全天规则）
                    _process_missed_for_today(now)
                    _process_community_missed_for_today(now)
                    scheduler_logger.info("缺失打卡检查任务完成")
                except Exception as e:
                    scheduler_logger.error(f"缺失打卡检查任务执行失败: {str(e)}", exc_info=True)

        # 任务 1: 异常值计算（每分钟执行一次）
        @scheduler.task('cron', id='update_abnormality_values', minute='*')
        def update_abnormality_values():
            """每分钟执行一次异常值计算"""
            run_abnormality_calculation()

        # 任务 2: 全天规则检查（每天凌晨执行一次）
        @scheduler.task('cron', id='daily_check', hour=0, minute=0)
        def scheduled_daily_check():
            """每天凌晨执行全天规则检查"""
            run_daily_check()

        # 任务 3: 缺失打卡检查（每 5 分钟执行一次）
        interval_minutes = int(os.getenv('MISS_CHECK_INTERVAL_MINUTES', '5'))
        @scheduler.task('interval', id='missing_check', minutes=interval_minutes)
        def scheduled_missing_check():
            """每 5 分钟执行缺失打卡检查"""
            run_missing_check()

        # 启动调度器
        scheduler.start()

        scheduler_logger.info("定时任务调度器已启动（3个任务：异常值计算、全天规则检查、缺失打卡检查）")

        # 启动时立即执行所有任务
        scheduler_logger.info("启动时立即执行所有定时任务...")
        run_abnormality_calculation()
        run_daily_check()
        run_missing_check()
        scheduler_logger.info("启动时任务执行完成")

    except Exception as e:
        scheduler_logger.error(f"启动定时任务调度器失败: {str(e)}", exc_info=True)