"""
分享模块 API 契约测试
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure


class TestShareContract:
    """分享模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 share.yaml 规范"""
        return load_schema("share")

    @pytest.fixture
    def auth_headers(self, base_client):
        """获取认证 token"""
        # TODO: 实现认证获取逻辑
        return {}

    # ==================== 创建分享链接 ====================

    def test_share_link_create_contract(self, schema, base_client, auth_headers):
        """TODO: 测试创建分享链接契约"""
        # Endpoint: POST /api/share/create
        # 验证返回 share_link、expire_time 等字段
        pytest.skip("待实现：需要准备测试数据（事件、社区等）")

    # ==================== 获取分享内容 ====================

    def test_share_content_get_contract(self, schema, base_client):
        """TODO: 测试通过分享链接获取内容契约"""
        # Endpoint: GET /api/share/{share_id}
        # 验证返回分享的内容（无需认证）
        pytest.skip("待实现：需要准备测试数据（分享链接）")

    # ==================== 分享链接管理 ====================

    def test_share_links_list_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取我的分享链接列表契约"""
        # Endpoint: GET /api/share/list
        # 验证返回分页的分享链接列表
        pytest.skip("待实现：需要准备测试数据")

    def test_share_link_revoke_contract(self, schema, base_client, auth_headers):
        """TODO: 测试撤销分享链接契约"""
        # Endpoint: DELETE /api/share/{share_id}
        # 验证撤销成功
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 访问分享 ====================

    def test_share_access_contract(self, schema, base_client):
        """TODO: 测试访问分享内容契约"""
        # Endpoint: POST /api/share/{share_id}/access
        # 验证可以访问分享内容
        pytest.skip("待实现：需要准备测试数据")
