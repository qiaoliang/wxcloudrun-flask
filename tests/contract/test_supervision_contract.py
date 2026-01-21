"""
监护模块 API 契约测试
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure


class TestSupervisionContract:
    """监护模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 supervision.yaml 规范"""
        return load_schema("supervision")

    @pytest.fixture
    def auth_headers(self, base_client):
        """获取认证 token"""
        # TODO: 实现认证获取逻辑
        return {}

    # ==================== 创建监护关系 ====================

    def test_supervision_create_contract(self, schema, base_client, auth_headers):
        """TODO: 测试创建监护关系契约"""
        # Endpoint: POST /api/supervision/create
        # 验证返回 supervision_id、guardian_id、ward_id 等字段
        pytest.skip("待实现：需要准备测试数据（监护人、被监护人、社区）")

    # ==================== 获取监护关系 ====================

    def test_supervision_list_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取监护关系列表契约"""
        # Endpoint: GET /api/supervision/list
        # 验证返回分页的监护关系列表
        pytest.skip("待实现：需要准备测试数据")

    def test_supervision_detail_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取监护关系详情契约"""
        # Endpoint: GET /api/supervision/{supervision_id}
        # 验证返回完整的监护关系信息
        pytest.skip("待实现：需要准备测试数据（监护关系）")

    # ==================== 更新监护关系 ====================

    def test_supervision_update_contract(self, schema, base_client, auth_headers):
        """TODO: 测试更新监护关系契约"""
        # Endpoint: PUT /api/supervision/{supervision_id}
        # 验证更新成功
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 删除监护关系 ====================

    def test_supervision_delete_contract(self, schema, base_client, auth_headers):
        """TODO: 测试删除监护关系契约"""
        # Endpoint: DELETE /api/supervision/{supervision_id}
        # 验证删除成功
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 我的监护关系 ====================

    def test_my_supervisions_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取我的监护关系契约"""
        # Endpoint: GET /api/supervision/my
        # 验证返回当前用户作为监护人的关系列表
        pytest.skip("待实现：需要准备测试数据")

    def test_my_supervisors_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取我的监护人契约"""
        # Endpoint: GET /api/supervision/my-supervisors
        # 验证返回当前用户作为被监护人的关系列表
        pytest.skip("待实现：需要准备测试数据")

    # ==================== 监护邀请 ====================

    def test_supervision_invite_contract(self, schema, base_client, auth_headers):
        """TODO: 测试发送监护邀请契约"""
        # Endpoint: POST /api/supervision/invite
        # 验证邀请发送成功
        pytest.skip("待实现：需要准备测试数据")

    def test_supervision_accept_invite_contract(self, schema, base_client, auth_headers):
        """TODO: 测试接受监护邀请契约"""
        # Endpoint: POST /api/supervision/accept/{invite_id}
        # 验证接受成功
        pytest.skip("待实现：需要准备测试数据（邀请）")

    def test_supervision_reject_invite_contract(self, schema, base_client, auth_headers):
        """TODO: 测试拒绝监护邀请契约"""
        # Endpoint: POST /api/supervision/reject/{invite_id}
        # 验证拒绝成功
        pytest.skip("待实现：需要准备测试数据")
