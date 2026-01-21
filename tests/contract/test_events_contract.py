"""
事件模块 API 契约测试
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure


class TestEventsContract:
    """事件模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 events.yaml 规范"""
        return load_schema("events")

    @pytest.fixture
    def auth_headers(self, base_client):
        """获取认证 token"""
        # TODO: 实现认证获取逻辑
        return {}

    # ==================== 呼救事件 ====================

    def test_event_help_create_contract(self, schema, base_client, auth_headers):
        """TODO: 测试创建呼救事件契约"""
        # Endpoint: POST /api/events/help
        # 验证返回 event_id、status、created_at 等字段
        pytest.skip("待实现：需要准备测试数据（用户、社区）")

    def test_event_help_list_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取呼救事件列表契约"""
        # Endpoint: GET /api/events/help
        # 验证返回分页的事件列表
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 支持事件 ====================

    def test_event_support_create_contract(self, schema, base_client, auth_headers):
        """TODO: 测试创建支持事件契约"""
        # Endpoint: POST /api/events/support
        # 验证返回事件信息
        pytest.skip("待实现：需要准备测试数据")

    def test_event_support_list_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取支持事件列表契约"""
        # Endpoint: GET /api/events/support
        # 验证返回分页的事件列表
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 事件详情 ====================

    def test_event_detail_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取事件详情契约"""
        # Endpoint: GET /api/events/{event_id}
        # 验证返回完整事件信息（类型、描述、状态等）
        pytest.skip("待实现：需要准备测试数据（事件）")

    # ==================== 事件操作 ====================

    def test_event_close_contract(self, schema, base_client, auth_headers):
        """TODO: 测试关闭事件契约"""
        # Endpoint: POST /api/events/{event_id}/close
        # 验证关闭成功
        pytest.skip("待实现：需要准备测试数据")

    def test_event_messages_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取事件消息契约"""
        # Endpoint: GET /api/events/{event_id}/messages
        # 验证返回消息列表
        pytest.skip("待实现：需要准备测试数据")

    def test_event_add_message_contract(self, schema, base_client, auth_headers):
        """TODO: 测试添加事件消息契约"""
        # Endpoint: POST /api/events/{event_id}/messages
        # 验证消息添加成功
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 我的事件 ====================

    def test_my_events_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取我的事件列表契约"""
        # Endpoint: GET /api/events/my
        # 验证返回当前用户相关的事件
        pytest.skip("待实现：需要准备测试数据")
