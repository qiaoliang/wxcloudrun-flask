"""
短信模块 API 契约测试
测试短信验证码相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestSmsContract:
    """短信模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 sms.yaml 规范"""
        return load_schema("sms")

    # ==================== 发送验证码 ====================

    def test_sms_send_code_register_contract(self, schema, base_client):
        """测试发送注册验证码契约"""
        random_phone = f"138{random.randint(10000000, 99999999)}"
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': random_phone,
                'purpose': 'register'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "message" in response_data
        # 测试环境可能返回验证码
        if "code" in response_data:
            assert isinstance(response_data["code"], str)

    def test_sms_send_code_login_contract(self, schema, base_client):
        """测试发送登录验证码契约"""
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': '13141516171',
                'purpose': 'login'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "message" in response_data

    def test_sms_send_code_bind_phone_contract(self, schema, base_client):
        """测试发送绑定手机验证码契约"""
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': '13900000000',
                'purpose': 'bind_phone'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_sms_send_code_default_purpose_contract(self, schema, base_client):
        """测试发送验证码（默认用途）契约"""
        random_phone = f"137{random.randint(10000000, 99999999)}"
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': random_phone
                # 不指定 purpose，默认为 register
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_sms_send_code_field_types_100_percent(self, schema, base_client):
        """100% 完整度验证：发送验证码 - 验证所有返回字段及类型"""
        random_phone = f"136{random.randint(10000000, 99999999)}"
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': random_phone,
                'purpose': 'register'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "message" in response_data

        # 验证字段类型
        assert isinstance(response_data["message"], str)

        # 验证字段值有效性
        assert len(response_data["message"]) > 0

    def test_sms_send_code_missing_phone_contract(self, schema, base_client):
        """测试发送验证码缺少手机号契约"""
        response = base_client.post('/api/sms/send_code',
            json={}  # 缺少 phone
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_sms_send_code_invalid_phone_contract(self, schema, base_client):
        """测试发送验证码无效手机号契约"""
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': 'invalid_phone'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_sms_send_code_invalid_purpose_contract(self, schema, base_client):
        """测试发送验证码无效用途契约"""
        response = base_client.post('/api/sms/send_code',
            json={
                'phone': '13800000000',
                'purpose': 'invalid_purpose'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 0
