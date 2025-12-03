import pytest
from unittest.mock import MagicMock

# ----------------------------------------------------------------------
# 单元测试专用 Fixture (通常是 Mock 或简单辅助数据)
# ----------------------------------------------------------------------

@pytest.fixture
def mock_wechat_api():
    """
    Mock 微信 API 客户端，避免真实的网络请求。
    例如，用于测试用户登录逻辑。
    """
    mock = MagicMock()
    mock.get_user_info.return_value = {
        'openid': 'mock_openid_123',
        'session_key': 'mock_key'
    }
    return mock

@pytest.fixture
def sample_counter_data():
    """
    用于不需要数据库的 DAO/Service 层测试的简单数据结构。
    """
    return {'id': 1, 'count': 50}

# 注意：这个文件中的 Fixture 默认只能在 tests/unit/ 目录下使用。