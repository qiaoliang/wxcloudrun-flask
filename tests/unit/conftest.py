import pytest
from unittest.mock import MagicMock
from tests.unit.fixtures.counter_fixture import sample_counter_data
from tests.unit.fixtures.wx_fixture import mock_wechat_api

# ----------------------------------------------------------------------
# 单元测试专用 Fixture (导入所有其他测试用fixture)
# ----------------------------------------------------------------------

# 注意：这个文件中的 Fixture 默认只能在 tests/unit/ 目录下使用。