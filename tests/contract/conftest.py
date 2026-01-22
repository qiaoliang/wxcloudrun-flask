"""
契约测试配置文件
为 schemathesis 提供认证和测试环境
使用生产代码中的初始化脚本确保数据一致性
"""
import pytest
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)


@pytest.fixture(scope="module")
def app():
    """创建 Flask 测试应用 - 使用生产初始化脚本"""
    # 设置测试环境
    os.environ['ENV_TYPE'] = 'unit'
    os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
    os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'
    os.environ['PHONE_ENC_SECRET'] = 'test_secret_key_for_testing'
    os.environ['SMS_PROVIDER'] = 'mock'

    from app import create_app
    from app.extensions import db
    from database.initialization import create_superadmin_and_default_community

    app = create_app()
    app.config['TESTING'] = True

    # 在应用上下文中初始化数据库
    with app.app_context():
        db.create_all()
        # 调用生产初始化脚本（幂等）
        create_superadmin_and_default_community()

    yield app

    # 模块级别清理 - 每个测试模块运行后清理数据库
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="module")
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """获取认证 token（用于需要认证的 API）- function scope 避免数据冲突"""
    response = client.post('/api/auth/login_phone_password', json={
        'phone': '13141516171',
        'password': 'F1234567'
    })
    data = response.get_json()
    if data.get('code') == 1:
        token = data['data']['token']
        return {'Authorization': f'Bearer {token}'}
    return {}


@pytest.fixture(scope="module")
def base_client(app):
    """基础测试客户端（别名，与现有测试保持一致）"""
    return app.test_client()
