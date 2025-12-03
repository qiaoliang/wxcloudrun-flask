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