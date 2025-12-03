import pytest
import jwt
from datetime import datetime, timezone, timedelta
import os


# ----------------------------------------------------------------------
# 单元测试专用 Fixture (导入所有其他测试用fixture)
# ----------------------------------------------------------------------

# 注意：这个文件中的 Fixture 默认只能在 tests/unit/ 目录下使用。

# 导入所有其他测试用fixture
# 定义测试用户ID
@pytest.fixture
def test_user_id():
    """提供一个测试用户ID"""
    return 12345

# 使用 JWT 创建有效的 token
@pytest.fixture
def create_jwt_token(test_user_id):
    """创建一个有效的 JWT token 用于测试"""
    token = jwt.encode({
        'user_id': test_user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')


# 导入其他 fixtures
from tests.unit.fixtures.counter_fixture import sample_counter_data
