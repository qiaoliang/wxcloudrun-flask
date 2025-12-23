import pytest
import os
import sys
from unittest.mock import patch

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

def create_app_for_testing():
    """为测试创建Flask应用的辅助函数"""
    os.environ['ENV_TYPE'] = 'unit'  # 使用unit环境，这样会使用内存数据库
    
    from src.main import create_app
    from src.database.core import get_database
    from src.database.initialization import create_super_admin_and_default_community
    
    application = create_app()
    
    # 在应用上下文中初始化数据库
    with application.app_context():
        # 使用测试模式的数据库
        db_core = get_database('test')
        db_core.initialize()
        application.db_core = db_core
        
        # 创建所有表
        db_core.create_tables()
        
        # 创建初始数据
        create_super_admin_and_default_community(db_core)
    
    return application


@pytest.fixture(scope="session")
def app():
    """创建一次性的Flask应用实例用于所有集成测试"""
    # 设置环境为单元测试（使用内存数据库）
    os.environ['ENV_TYPE'] = 'unit'
    
    application = create_app_for_testing()
    
    yield application
    
    # 清理
    with application.app_context():
        db_core = application.db_core
        # 重置数据库实例
        from src.database.core import reset_all
        reset_all()


@pytest.fixture
def client(app):
    """为每个测试提供HTTP客户端"""
    return app.test_client()


@pytest.fixture
def db_session(app):
    """为每个测试提供数据库会话，支持自动回滚"""
    with app.app_context():
        db_core = app.db_core
        with db_core.get_session() as session:
            # 在会话中开始事务
            transaction = session.begin()
            try:
                yield session
            finally:
                # 自动回滚事务，确保数据隔离
                transaction.rollback()