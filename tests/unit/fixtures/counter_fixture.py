import pytest

@pytest.fixture
def sample_counter_data():
    """
    用于不需要数据库的 DAO/Service 层测试的简单数据结构。
    """
    return {'id': 1, 'count': 50}