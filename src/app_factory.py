"""
改进的Flask应用初始化
使用数据库工厂实现依赖注入，解耦数据库和Flask
"""
import os
import sys
import logging
from flask import Flask
from database_factory import DatabaseManager
import config_manager


class ApplicationFactory:
    """
    应用工厂类
    负责创建和配置Flask应用，使用数据库工厂管理数据库实例
    """
    
    def __init__(self):
        self.db_manager = None
        self._setup_logging()
    
    def _setup_logging(self):
        """设置日志"""
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
    
    def create_app(self, config_name: str = None) -> Flask:
        """
        创建Flask应用
        :param config_name: 配置名称（function/production/test等）
        :return: 配置好的Flask应用
        """
        # 创建Flask应用实例
        app = Flask(__name__, instance_relative_config=True)
        
        # 加载配置
        self._load_config(app, config_name)
        
        # 初始化数据库
        self._init_database(app)
        
        # 注册蓝图和路由
        self._register_blueprints(app)
        
        # 启动后台服务
        self._start_background_services(app)
        
        return app
    
    def _load_config(self, app: Flask, config_name: str):
        """加载应用配置"""
        # 加载环境配置
        config_manager.load_environment_config(config_name)
        
        # 基础配置
        app.config['DEBUG'] = config_manager.DEBUG
        
        # 从配置对象加载
        app.config.from_object('config')
    
    def _init_database(self, app: Flask):
        """初始化数据库（使用数据库工厂）"""
        # 创建数据库管理器
        self.db_manager = DatabaseManager(config_manager)
        
        # 设置Flask应用的数据库
        db = self.db_manager.setup_flask_app(app)
        
        # 将db实例设置为应用属性（保持向后兼容）
        app.db = db
        
        # 导入模型（必须在数据库初始化后）
        self._import_models()
        
        # 在unit环境下创建默认数据
        if config_manager.is_unit_environment():
            self._create_default_data(app)
    
    def _import_models(self):
        """导入所有模型"""
        # 注意：所有模型都已迁移到 database.models
        # model.py 和 model_community_extensions 已被弃用
        pass
    
    def _register_blueprints(self, app: Flask):
        """注册蓝图和路由"""
        # 导入并注册视图模块
        from .views import misc, sms, auth, user, checkin, supervision, share, community
        
        # 注册蓝图（如果使用蓝图的话）
        # app.register_blueprint(auth_bp)
        # app.register_blueprint(user_bp)
        
        # 或者直接导入视图模块以注册路由
        # 视图模块会在导入时自动注册路由
    
    def _start_background_services(self, app: Flask):
        """启动后台服务"""
        try:
            # 只在主进程中启动，避免debug模式下重复启动
            if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
                from .background_tasks import start_missing_check_service
                start_missing_check_service()
        except Exception as e:
            app.logger.error(f"启动后台missing服务失败: {str(e)}")
    
    def _create_default_data(self, app: Flask):
        """创建默认数据（仅测试环境）"""
        # 默认社区初始化已在数据库迁移完成后自动执行
        app.logger.info("默认社区初始化已在数据库迁移完成后自动执行")


# 创建应用工厂实例
app_factory = ApplicationFactory()


def create_app(config_name: str = None) -> Flask:
    """
    应用创建函数
    :param config_name: 配置名称
    :return: Flask应用实例
    """
    return app_factory.create_app(config_name)


def get_database_manager() -> DatabaseManager:
    """获取数据库管理器实例"""
    return app_factory.db_manager


# 为了向后兼容，保留原有的创建方式
def create_legacy_app():
    """
    创建传统方式的Flask应用（保持向后兼容）
    """
    return create_app()