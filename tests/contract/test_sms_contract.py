"""
短信模块 API 契约测试
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure


class TestSmsContract:
    """短信模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 sms.yaml 规范"""
        return load_schema("sms")

    @pytest.fixture
    def auth_headers(self, base_client):
        """获取认证 token"""
        # TODO: 实现认证获取逻辑
        return {}

    # ==================== 发送验证码 ====================

    def test_sms_send_code_contract(self, schema, base_client):
        """TODO: 测试发送短信验证码契约"""
        # Endpoint: POST /api/sms/send-code
        # 验证返回发送成功状态
        # 注意：测试环境使用 mock SMS provider
        pytest.skip("待实现：需要配置 mock SMS")

    # ==================== 验证验证码 ====================

    def test_sms_verify_code_contract(self, schema, base_client):
        """TODO: 测试验证短信验证码契约"""
        # Endpoint: POST /api/sms/verify-code
        # 验证返回验证结果
        pytest.skip("待实现：需要准备测试数据和 mock 验证码")

    # ==================== 获取验证码状态 ====================

    def test_sms_code_status_contract(self, schema, base_client, auth_headers):
        """TODO: 测试获取验证码状态契约"""
        # Endpoint: GET /api/sms/code-status
        # 验证返回验证码状态（是否已使用、过期时间等）
        pytest.skip("待实现：需要准备测试数据")
