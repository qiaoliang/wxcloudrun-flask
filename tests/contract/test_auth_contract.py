"""
认证模块 API 契约测试
测试登录、注册等认证相关的 API 契约
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestAuthContract:
    """认证模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 auth.yaml 规范"""
        return load_schema("auth")

    # ==================== 手机号密码登录 ====================

    def test_login_phone_password_contract(self, schema, base_client):
        """测试手机号密码登录契约"""
        endpoint_def = schema["paths"]["/api/auth/login_phone_password"]["post"]

        creds = get_test_user_credentials()
        response = base_client.post('/api/auth/login_phone_password', json={
            'phone': creds['phone_number'],
            'password': creds['password']
        })

        # 验证状态码
        assert response.status_code == 200

        # 验证 StandardResponse 结构
        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应 data 字段
        response_data = data["data"]
        required_fields = ["token", "refresh_token", "user_id"]
        for field in required_fields:
            assert field in response_data, f"登录响应缺少字段: {field}"

        # 验证 token 类型
        assert isinstance(response_data["token"], str)
        assert isinstance(response_data["refresh_token"], str)
        assert isinstance(response_data["user_id"], int)

    # ==================== 错误场景 ====================

    def test_login_phone_password_wrong_password_contract(self, schema, base_client):
        """测试密码错误的登录契约"""
        response = base_client.post('/api/auth/login_phone_password', json={
            'phone': '13141516171',
            'password': 'wrong_password'
        })

        # 验证响应结构（即使失败也应该符合契约）
        data = validate_response_structure(response)
        # 密码错误时 code 应该是 0
        assert data["code"] == 0

    def test_login_phone_password_missing_field_contract(self, base_client):
        """测试缺少必填字段的登录契约"""
        response = base_client.post('/api/auth/login_phone_password', json={
            'phone': '13141516171'
            # 缺少 password
        })

        # 验证响应结构
        data = validate_response_structure(response)
        assert data["code"] == 0
