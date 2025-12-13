"""
轻量级数据库初始化器
使用与生产相同的Alembic机制，但最小化Flask依赖
"""
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))


class MinimalDatabaseInitializer:
    """
    最小化Flask依赖的数据库初始化器
    使用与生产相同的模型元数据和Alembic机制
    """
    
    def __init__(self, db_uri="sqlite:///:memory:"):
        self.db_uri = db_uri
        self.engine = None
        self.session_factory = None
        
    def _create_minimal_flask_app(self):
        """
        创建最小化的Flask应用，只用于获取模型元数据
        避免完整的Flask初始化
        """
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        
        # 创建最小化Flask应用
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = self.db_uri
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 创建SQLAlchemy实例
        db = SQLAlchemy(app)
        
        # 临时替换wxcloudrun模块中的db对象
        import wxcloudrun
        original_db = wxcloudrun.db
        wxcloudrun.db = db
        
        try:
            # 导入所有模型，它们会使用我们创建的db对象
            from wxcloudrun.model import (
                User, CheckinRule, CheckinRecord, SupervisionRuleRelation,
                Community, CommunityApplication
            )
            # from src.wxcloudrun.model_community_extensions import
from database.models import CommunityStaff, CommunityMember (
                CommunityStaff, CommunityMember
            )
            
            # 获取模型元数据（与生产环境相同）
            metadata = db.metadata
            
            return metadata, db
            
        finally:
            # 恢复原始db对象
            wxcloudrun.db = original_db
    
    def initialize(self):
        """初始化数据库"""
        # 创建最小化Flask应用以获取模型元数据
        metadata, db = self._create_minimal_flask_app()
        
        # 创建独立的数据库引擎
        self.engine = create_engine(
            self.db_uri,
            connect_args={'check_same_thread': False} if 'sqlite' in self.db_uri else {}
        )
        
        # 使用与生产相同的元数据创建表
        metadata.create_all(self.engine)
        
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
    
    def create_test_data(self, session):
        """创建基础测试数据（模拟生产环境的初始化）"""
        # 创建默认社区（模拟生产环境）
        from wxcloudrun.model import Community
        
        default_community = Community(
            name="安卡大家庭",
            description="默认社区",
            is_default=True,
            status=1
        )
        session.add(default_community)
        
        # 创建超级管理员（模拟生产环境）
        from wxcloudrun.model import User
        from datetime import datetime
        
        super_admin = User(
            wechat_openid="super_admin_test",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1,
            created_at=datetime.now()
        )
        session.add(super_admin)
        
        session.commit()
        
        return default_community, super_admin


# 创建全局初始化器实例
_test_db_initializer = None


def get_test_db_initializer():
    """获取测试数据库初始化器（单例模式）"""
    global _test_db_initializer
    if _test_db_initializer is None:
        _test_db_initializer = MinimalDatabaseInitializer()
    return _test_db_initializer


def reset_test_db():
    """重置测试数据库初始化器"""
    global _test_db_initializer
    _test_db_initializer = None