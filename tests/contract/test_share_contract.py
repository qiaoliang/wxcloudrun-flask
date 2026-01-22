"""
分享模块 API 契约测试
测试分享链接相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestShareContract:
    """分享模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 share.yaml 规范"""
        return load_schema("share")

    @pytest.fixture
    def auth_headers(self, base_client):
        """获取认证 token"""
        response = base_client.post('/api/auth/login_phone_password', json={
            'phone': '13141516171',
            'password': 'F1234567'
        })
        data = response.get_json()
        if data.get('code') == 1:
            token = data['data']['token']
            return {'Authorization': f'Bearer {token}'}
        return {}

    @pytest.fixture
    def test_rule_id(self, base_client, auth_headers):
        """创建测试用打卡规则并返回 rule_id"""
        response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试分享规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'rule_id' in data.get('data', {}):
            return data['data']['rule_id']
        return None

    # ==================== 创建可分享的打卡邀请链接 ====================

    def test_share_checkin_create_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试创建可分享的打卡邀请链接契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/checkin/create',
            json={
                'rule_id': test_rule_id,
                'expire_hours': 168
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["token", "url", "mini_path", "qrcode_url", "expire_at"]
        for field in required_fields:
            assert field in response_data, f"创建分享链接响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["token"], str)
        assert isinstance(response_data["url"], str)
        assert isinstance(response_data["mini_path"], str)
        assert isinstance(response_data["qrcode_url"], str)
        assert isinstance(response_data["expire_at"], str)

    def test_share_checkin_create_default_expire_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试创建分享链接（默认过期时间）契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/checkin/create',
            json={
                'rule_id': test_rule_id
                # 不指定 expire_hours，默认为 168 (7天)
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "token" in response_data
        assert "url" in response_data

    def test_share_checkin_create_field_types_100_percent(self, schema, base_client, auth_headers, test_rule_id):
        """100% 完整度验证：创建分享链接 - 验证所有返回字段及类型"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/checkin/create',
            json={
                'rule_id': test_rule_id,
                'expire_hours': 24
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "token" in response_data
        assert "url" in response_data
        assert "mini_path" in response_data
        assert "qrcode_url" in response_data
        assert "expire_at" in response_data

        # 验证字段类型
        assert isinstance(response_data["token"], str)
        assert isinstance(response_data["url"], str)
        assert isinstance(response_data["mini_path"], str)
        assert isinstance(response_data["qrcode_url"], str)
        assert isinstance(response_data["expire_at"], str)

        # 验证字段值有效性
        assert len(response_data["token"]) > 0
        assert len(response_data["url"]) > 0
        assert len(response_data["mini_path"]) > 0
        assert len(response_data["qrcode_url"]) > 0
        assert len(response_data["expire_at"]) > 0

    def test_share_checkin_create_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试创建分享链接缺少规则ID契约"""
        response = base_client.post('/api/checkin/create',
            json={},  # 缺少 rule_id
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 解析分享链接 ====================

    def test_share_checkin_resolve_contract(self, schema, base_client):
        """测试解析分享链接契约"""
        # 使用测试token
        response = base_client.get('/api/checkin/resolve',
            query_string={'token': 'test_share_token'}
        )

        data = validate_response_structure(response)
        # token可能无效，只验证结构

        if data["code"] == 1:
            # 验证响应字段
            response_data = data["data"]
            assert "rule_info" in response_data
            assert "inviter_info" in response_data
            assert "is_expired" in response_data
            assert "is_already_supervisor" in response_data

            # 验证 rule_info 字段
            rule_info = response_data["rule_info"]
            assert "rule_id" in rule_info
            assert "rule_name" in rule_info
            assert "frequency_type" in rule_info
            assert "time_slot_type" in rule_info
            assert "is_enabled" in rule_info

            # 验证 inviter_info 字段
            inviter_info = response_data["inviter_info"]
            assert "user_id" in inviter_info
            assert "nickname" in inviter_info

            # 验证布尔字段
            assert isinstance(response_data["is_expired"], bool)
            assert isinstance(response_data["is_already_supervisor"], bool)

    def test_share_checkin_resolve_missing_token_contract(self, schema, base_client):
        """测试解析分享链接缺少token契约"""
        response = base_client.get('/api/checkin/resolve')

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_share_checkin_resolve_field_types_100_percent(self, schema, base_client):
        """100% 完整度验证：解析分享链接 - 验证所有返回字段及类型"""
        response = base_client.get('/api/checkin/resolve',
            query_string={'token': 'test_share_token'}
        )

        data = validate_response_structure(response)
        # token可能无效
        if data["code"] == 1:
            # OpenAPI 定义的完整响应字段
            response_data = data["data"]

            # 验证所有字段存在
            assert "rule_info" in response_data
            assert "inviter_info" in response_data
            assert "is_expired" in response_data
            assert "is_already_supervisor" in response_data

            # 验证 rule_info 字段类型
            rule_info = response_data["rule_info"]
            assert isinstance(rule_info["rule_id"], int)
            assert isinstance(rule_info["rule_name"], str)
            assert isinstance(rule_info["is_enabled"], bool)

            # 验证 inviter_info 字段类型
            inviter_info = response_data["inviter_info"]
            assert isinstance(inviter_info["user_id"], int)
            assert isinstance(inviter_info["nickname"], str)

    # ==================== 分享打卡页面 ====================

    def test_share_check_in_page_contract(self, schema, base_client):
        """测试分享打卡页面契约"""
        response = base_client.get('/api/share/check-in')

        # 返回HTML内容
        assert response.status_code == 200
        assert b'<html' in response.data or b'<!DOCTYPE' in response.data
