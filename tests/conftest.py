"""
测试基类
封装Flask-SQLAlchemy的测试上下文管理，提供统一的测试基础设施
"""

import pytest
import os
import sys
from unittest.mock import patch

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)


class TestBase:
    """测试基类，封装Flask-SQLAlchemy测试上下文管理"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置，创建应用实例"""
        # 设置测试环境
        os.environ['ENV_TYPE'] = 'unit'
        os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
        
        # 导入并创建Flask应用
        from app import create_app
        from app.extensions import db
        
        cls.app = create_app()
        cls.db = db
        
        # 在应用上下文中初始化数据库
        with cls.app.app_context():
            # 创建所有表
            cls.db.create_all()
            
            # 创建初始数据
            cls._create_initial_data()
    
    @classmethod
    def teardown_class(cls):
        """类级别的清理"""
        with cls.app.app_context():
            # 删除所有表
            cls.db.drop_all()
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        # 在应用上下文中开始事务
        with self.app.app_context():
            self.db.session.begin_nested()
    
    def teardown_method(self, method):
        """每个测试方法后的清理"""
        # 回滚事务，确保测试隔离
        with self.app.app_context():
            self.db.session.rollback()
    
    @classmethod
    def _create_initial_data(cls):
        """创建测试所需的初始数据"""
        from database.flask_models import User, Community
        
        # 创建测试用户
        test_user = User(
            wechat_openid='test_openid_123',
            phone_hash='test_phone_hash',
            nickname='测试用户',
            avatar_url='https://example.com/avatar.jpg',
            role=1  # 普通用户角色
        )
        cls.db.session.add(test_user)
        
        # 创建测试社区
        test_community = Community(
            name='测试社区',
            description='用于测试的社区',
            creator_id=test_user.user_id
        )
        cls.db.session.add(test_community)
        
        cls.db.session.commit()
        
        # 保存测试数据供子类使用
        cls.test_user = test_user
        cls.test_community = test_community
    
    def get_test_client(self):
        """获取测试客户端"""
        return self.app.test_client()
    
    def get_db_session(self):
        """获取数据库会话"""
        return self.db.session
    
    def create_test_user(self, **kwargs):
        """创建测试用户的辅助方法"""
        from database.flask_models import User
        
        default_data = {
            'wechat_openid': f'test_openid_{kwargs.get("suffix", "default")}',
            'phone_hash': f'test_phone_hash_{kwargs.get("suffix", "default")}',
            'nickname': '测试用户',
            'avatar_url': 'https://example.com/avatar.jpg',
            'role': 1  # 普通用户角色
        }
        default_data.update(kwargs)
        
        user = User(**default_data)
        self.db.session.add(user)
        self.db.session.commit()
        return user
    
    def create_test_community(self, **kwargs):
        """创建测试社区的辅助方法"""
        from database.flask_models import Community
        
        default_data = {
            'name': '测试社区',
            'description': '用于测试的社区',
            'creator_id': self.test_user.user_id
        }
        default_data.update(kwargs)
        
        community = Community(**default_data)
        self.db.session.add(community)
        self.db.session.commit()
        return community


@pytest.fixture(scope="class")
def test_base():
    """提供TestBase实例的fixture"""
    return TestBase


@pytest.fixture(scope="class")
def app():
    """创建Flask应用实例的fixture"""
    os.environ['ENV_TYPE'] = 'unit'
    
    from app import create_app
    from app.extensions import db
    
    application = create_app()
    
    with application.app_context():
        db.create_all()
        yield application
        db.drop_all()


@pytest.fixture
def client(app):
    """为每个测试提供HTTP客户端"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """为每个测试提供数据库会话，支持自动回滚"""
    with app.app_context():
        from app.extensions import db
        
        # 开始嵌套事务
        savepoint = db.session.begin_nested()
        try:
            yield db.session
        finally:
            # 回滚到保存点，确保测试隔离
            savepoint.rollback()