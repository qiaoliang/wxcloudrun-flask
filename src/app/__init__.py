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

from config import init_config, get_database_config
from .extensions import db  # 从扩展模块导入

# 事件总线相关导入
from app.infrastructure.events.enhanced_event_bus import EnhancedEventBus
from app.infrastructure.events.outbox_processor import OutboxProcessor
from app.infrastructure.persistence.repository_factory import RepositoryFactory

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
    # 1. 初始化配置（必须在创建Flask应用之前）
    global app_config
    app_config = init_config()
    
    # 2. 创建Flask应用实例
    app = Flask(__name__, instance_relative_config=True, template_folder='templates')
    
    # 2. 配置日志
    configure_logging(app)
    
    # 3. 加载配置
    app.config['DEBUG'] = app_config.debug
    app.config['SQLALCHEMY_DATABASE_URI'] = app_config.database.uri
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'echo': os.getenv('SQL_DEBUG', 'False').lower() == 'true'
    }
    
    # 获取数据库配置（用于日志记录）
    db_config = get_database_config()
    app.config['DATABASE_CONFIG'] = db_config
    
    # 配置session支持
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev_secret_key')
    
    
# 4. 初始化扩展
    db.init_app(app)

    # 4.1 初始化事件总线
    outbox_repository = RepositoryFactory.get_outbox_repository()
    app.event_bus = EnhancedEventBus(outbox_repository)

    # 4.2 初始化 Outbox 处理器
    app.outbox_processor = OutboxProcessor(
        outbox_repository=outbox_repository,
        event_bus=app.event_bus,
        interval_seconds=5
    )

    # 4.3 启动后台处理线程
    @app.before_request
    def start_outbox_processor():
        if not hasattr(app, '_outbox_processor_started'):
            if not app.outbox_processor._running:
                app.outbox_processor.start()
            app._outbox_processor_started = True

    # 4.4 创建所有数据库表（包括 outbox_events）
    with app.app_context():
        db.create_all()
        app.logger.info("数据库表创建完成：包括 outbox_events 表")

    # 4.4 注册应用关闭时的清理
    import atexit
    atexit.register(app.outbox_processor.stop)

    # 4.5 初始化速率限制扩展
    from .extensions import limiter
    from config import EnvironmentHelper
    
    # 根据环境配置存储后端
    if EnvironmentHelper.is_production():
        # 生产环境使用 Redis 存储
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        limiter.storage_uri = redis_url
        limiter.storage_options = {"socket_connect_timeout": 30}
    elif EnvironmentHelper.is_unit() or EnvironmentHelper.is_function():
        # 测试环境和功能测试环境禁用速率限制
        limiter.enabled = False
        app.logger.info(f"速率限制已禁用 (ENV_TYPE={EnvironmentHelper.get_env_type()})")
    else:
        # 开发环境使用内存存储
        limiter.storage_uri = "memory://"
    
    limiter.init_app(app)
    app.logger.info("Flask-Limiter 速率限制扩展已初始化")
    
    # 4.6 初始化CORS（支持跨域请求）
    from flask_cors import CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # 5. 导入Flask-SQLAlchemy模型（确保在db.init_app之后）
    # 注意：模型导入必须在db.init_app之后，但在注册蓝图之前
    from database.flask_models import (
        User, Community, CheckinRule, CheckinRecord,
        UserAuditLog, Counters, OutboxEvent
    )

    # 创建所有数据库表（包括 outbox_events）
    with app.app_context():
        db.create_all()
        app.logger.info("数据库表创建完成：包括 outbox_events 表")

    # 6. 注册蓝图
    register_blueprints(app)
    
    # 7. 注册错误处理器
    register_error_handlers(app)
    
    # 8. 注册会话清理
    register_session_cleanup(app)

    # 9. 在 unit 环境下初始化默认数据
    from config import EnvironmentHelper
    if EnvironmentHelper.is_unit():
        with app.app_context():
            app.logger.info("默认社区初始化已在数据库迁移完成后自动执行")

    # 10. 注册领域事件处理器
    register_event_handlers(app)

    # 注意：定时任务将在数据库迁移完成后启动（在 run.py 中调用）
    # 这样可以确保数据库表已经创建完成，避免定时任务查询失败

    return app


def register_blueprints(app):
    """注册所有蓝图到Flask应用"""
    # 注册根路径路由，直接返回 index.html
    @app.route('/')
    def index():
        """根路径返回首页"""
        from flask import send_from_directory
        import os
        # 获取 templates 目录的绝对路径
        templates_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
        return send_from_directory(templates_dir, 'index.html')

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
    from config import EnvironmentHelper
    if not EnvironmentHelper.is_unit():
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


def register_event_handlers(app):
    """注册领域事件处理器"""
    try:
        from app.domain.handlers import register_all_event_handlers

        # 注册所有事件处理器到事件总线
        register_all_event_handlers()

        # 获取并记录已注册的处理器数量
        from app.domain.handlers import get_event_handler_count
        handler_counts = get_event_handler_count()

        # 计算总处理器数量
        total_handlers = sum(
            len(event_counts) for event_counts in handler_counts.values()
        )

        app.logger.info(f"✓ 领域事件处理器注册完成，共 {total_handlers} 个处理器")

        # 记录各类事件的处理器数量
        for event_type, event_counts in handler_counts.items():
            app.logger.debug(f"  - {event_type}: {len(event_counts)} 个事件类型")

    except Exception as e:
        app.logger.error(f"注册领域事件处理器失败: {str(e)}", exc_info=True)
        # 事件处理器注册失败不应阻止应用启动，但需要记录错误





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
        from app.infrastructure.persistence.repository_factory import RepositoryFactory

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

        def run_check_expired_invitations():
            """检查并更新过期邀请"""
            with app.app_context():
                try:
                    scheduler_logger.info("开始执行邀请过期检查任务")
                    supervision_relation_repo = RepositoryFactory.get_supervision_relation_repository()

                    # 查找所有已过期的邀请
                    expired_invitations = supervision_relation_repo.find_expired_invitations()

                    if expired_invitations:
                        # 提取所有过期邀请的ID
                        expired_ids = [inv.relation_id for inv in expired_invitations]

                        # 批量更新状态为已过期（status=4）
                        updated_count = supervision_relation_repo.batch_update_status(expired_ids, 4)

                        scheduler_logger.info(f"邀请过期检查完成: 更新了 {updated_count} 个过期邀请")
                    else:
                        scheduler_logger.info("邀请过期检查完成: 没有找到过期的邀请")

                except Exception as e:
                    scheduler_logger.error(f"邀请过期检查任务执行失败: {str(e)}", exc_info=True)

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

        # 任务 4: 邀请过期检查（每天凌晨执行一次）
        @scheduler.task('cron', id='check_expired_invitations', hour=0, minute=30)
        def scheduled_check_expired_invitations():
            """每天凌晨执行邀请过期检查"""
            run_check_expired_invitations()

        # 启动调度器
        scheduler.start()

        scheduler_logger.info("定时任务调度器已启动（4个任务：异常值计算、全天规则检查、缺失打卡检查、邀请过期检查）")

        # 启动时立即执行所有任务（除了邀请过期检查，避免启动时重复执行）
        scheduler_logger.info("启动时立即执行所有定时任务...")
        run_abnormality_calculation()
        run_daily_check()
        run_missing_check()
        scheduler_logger.info("启动时任务执行完成")

    except Exception as e:
        scheduler_logger.error(f"启动定时任务调度器失败: {str(e)}", exc_info=True)