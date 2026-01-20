"""
契约测试的配置文件

提供测试所需的 fixtures 和工具函数
"""
import pytest
import os
import sys
from pathlib import Path


# 确保src目录在Python路径中
# 从 backend/tests/contract/conftest.py 向上 3 层到达 backend/，然后进入 src/
backend_root = Path(__file__).parent.parent.parent
src_path = backend_root / 'src'
sys.path.insert(0, str(src_path))


@pytest.fixture(scope='session')
def app():
    """创建并返回 Flask 应用实例"""
    # 设置测试环境
    os.environ['ENV_TYPE'] = 'function'  # 使用真实数据库
    os.environ['SECRET_KEY'] = 'test_secret_key_for_session'
    os.environ['TOKEN_SECRET'] = 'test_token_secret_for_testing'
    os.environ['SMS_PROVIDER'] = 'mock'
    os.environ['PHONE_ENCRYPTION_KEY'] = 'test_phone_encryption_key_for_contract_tests'

    # 导入并创建Flask应用
    from app import create_app

    app = create_app()
    
    # 配置测试
    app.config['TESTING'] = True
    
    yield app


@pytest.fixture(scope="session")
def project_root():
    """获取项目根目录"""
    return Path(__file__).parent.parent.parent.parent


@pytest.fixture(scope="session")
def frontend_src_dir(project_root):
    """获取前端源代码目录"""
    return project_root / "frontend" / "src"


@pytest.fixture(scope="session")
def backend_src_dir(project_root):
    """获取后端源代码目录"""
    return project_root / "backend" / "src"


@pytest.fixture(scope="session")
def api_contract_dir(backend_src_dir):
    """获取 API 契约目录"""
    return backend_src_dir.parent / "api-contract"


@pytest.fixture(scope="session")
def openapi_spec(api_contract_dir):
    """加载 OpenAPI 规范"""
    import yaml
    
    spec_file = api_contract_dir / "openapi.yaml"
    if not spec_file.exists():
        pytest.skip("OpenAPI 规范文件不存在")
    
    with open(spec_file) as f:
        return yaml.safe_load(f)


@pytest.fixture
def superadmin_token(client):
    """获取超级管理员的认证 token"""
    response = client.post('/api/auth/login_phone_password', json={
        'phone': '13141516171',
        'password': 'F1234567'
    })
    
    assert response.status_code == 200, f"登录失败: {response.json}"
    data = response.json
    return data['data']['token']


@pytest.fixture
def regular_user_token(client):
    """获取普通用户的认证 token（测试数据）"""
    # 使用测试数据生成器创建用户
    from tests.integration.testdata_generator import TestDataGenerator
    
    generator = TestDataGenerator()
    user = generator.generate_user()
    
    response = client.post('/api/auth/login_phone_password', json={
        'phone': user.phone_number,
        'password': user.password
    })
    
    assert response.status_code == 200, f"登录失败: {response.json}"
    data = response.json
    return data['data']['token']


def pytest_configure(config):
    """配置 pytest"""
    config.addinivalue_line(
        "markers", "contract: 标记契约测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记慢速测试"
    )