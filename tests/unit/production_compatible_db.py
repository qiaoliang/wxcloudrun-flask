"""
生产兼容的轻量级测试数据库初始化器
使用与生产相同的Alembic机制，最小化Flask依赖
"""
import os
import sys
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


class ProductionCompatibleDB:
    """
    生产兼容的数据库初始化器
    直接使用Alembic的metadata，避免Flask应用初始化
    """
    
    def __init__(self, db_uri="sqlite:///:memory:"):
        self.db_uri = db_uri
        self.engine = None
        self.session_factory = None
        self.metadata = None
        
    def _get_metadata_from_alembic(self):
        """
        从Alembic获取模型元数据，与生产环境完全相同
        """
        # 模拟Alembic的环境配置
        from alembic.config import Config
        from alembic import context
        
        # 创建Alembic配置
        alembic_cfg = Config()
        alembic_cfg.set_main_option("sqlalchemy.url", self.db_uri)
        
        # 临时设置环境变量
        original_env = os.environ.get('ENV_TYPE')
        os.environ['ENV_TYPE'] = 'unit'  # 确保使用测试配置
        
        try:
            # 导入配置管理器
            from config_manager import load_environment_config, get_database_config
            load_environment_config()
            
            # 更新数据库配置
            db_config = get_database_config()
            alembic_cfg.set_main_option("sqlalchemy.url", db_config['SQLALCHEMY_DATABASE_URI'])
            
            # 获取模型元数据（关键：使用与生产相同的方式）
            # 这里我们直接创建一个最小化的Flask应用来获取metadata
            # 但不触发完整的应用初始化
            from flask import Flask
            from flask_sqlalchemy import SQLAlchemy
            
            # 创建最小化Flask应用
            app = Flask(__name__)
            app.config['SQLALCHEMY_DATABASE_URI'] = db_config['SQLALCHEMY_DATABASE_URI']
            app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
            
            # 禁用Flask的日志和其他功能
            app.logger.disabled = True
            
            # 创建SQLAlchemy实例
            db = SQLAlchemy(app)
            
            # 导入模型（这是关键步骤）
            # 模型会使用我们创建的db对象
            import wxcloudrun.model
            import wxcloudrun.model_community_extensions
            
            # 获取metadata（与生产环境完全相同）
            metadata = db.metadata
            
            return metadata
            
        finally:
            # 恢复原始环境变量
            if original_env:
                os.environ['ENV_TYPE'] = original_env
            else:
                os.environ.pop('ENV_TYPE', None)
    
    def initialize(self):
        """初始化数据库"""
        # 获取与生产环境相同的metadata
        self.metadata = self._get_metadata_from_alembic()
        
        # 创建数据库引擎
        self.engine = create_engine(
            self.db_uri,
            connect_args={'check_same_thread': False} if 'sqlite' in self.db_uri else {}
        )
        
        # 使用与生产相同的metadata创建表
        self.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        
        return self.engine, self.session_factory
    
    @contextmanager
    def get_session(self):
        """获取数据库会话的上下文管理器"""
        if not self.session_factory:
            self.initialize()
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_production_like_data(self, session):
        """
        创建与生产环境相似的初始数据
        模拟生产环境的初始化过程
        """
        from wxcloudrun.model import Community, User
        from datetime import datetime
        
        # 创建默认社区（与生产环境相同）
        default_community = Community(
            name="安卡大家庭",
            description="默认社区",
            is_default=True,
            status=1,
            created_at=datetime.now()
        )
        session.add(default_community)
        
        # 创建超级管理员（与生产环境相似）
        super_admin = User(
            wechat_openid="test_super_admin",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1,
            created_at=datetime.now()
        )
        session.add(super_admin)
        
        session.commit()
        
        return default_community, super_admin


# 全局实例
_production_db = None


def get_production_compatible_db():
    """获取生产兼容的数据库实例（单例）"""
    global _production_db
    if _production_db is None:
        _production_db = ProductionCompatibleDB()
    return _production_db