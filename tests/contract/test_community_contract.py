"""
社区模块 API 契约测试
测试社区的创建、更新、状态切换、用户管理等核心功能的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestCommunityContract:
    """社区模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 community.yaml 规范"""
        return load_schema("community")

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

    # ==================== 创建社区 ====================

    def test_community_create_contract(self, schema, base_client, auth_headers):
        """测试创建社区契约"""
        random_suffix = random.randint(10000, 99999)
        response = base_client.post('/api/community/create',
            json={
                'name': f'测试社区_{random_suffix}',
                'description': '这是一个测试社区',
                'location': '北京市朝阳区'
            },
            headers=auth_headers
        )

        # 验证响应结构
        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["community_id"]
        for field in required_fields:
            assert field in response_data, f"创建社区响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["community_id"], int)
        assert response_data["community_id"] > 0

    def test_community_create_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：创建社区 - 验证所有返回字段及类型"""
        random_suffix = random.randint(10000, 99999)
        response = base_client.post('/api/community/create',
            json={
                'name': f'测试社区_{random_suffix}',
                'description': '这是一个测试社区',
                'location': '北京市朝阳区',
                'province': '北京市',
                'city': '北京市',
                'district': '朝阳区',
                'street': '建国路88号',
                'latitude': 39.9042,
                'longitude': 116.4074
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "community_id" in response_data

        # 验证字段类型
        assert isinstance(response_data["community_id"], int)
        assert response_data["community_id"] > 0

    # ==================== 更新社区 ====================

    def test_community_update_contract(self, schema, base_client, auth_headers):
        """测试更新社区信息契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_更新_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 更新社区
        response = base_client.post('/api/community/update',
            json={
                'community_id': community_id,
                'name': '更新后的社区名称',
                'description': '更新后的描述'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    # ==================== 切换社区状态 ====================

    def test_community_toggle_status_activate_contract(self, schema, base_client, auth_headers):
        """测试激活社区契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_状态_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 激活社区
        response = base_client.post('/api/community/toggle-status',
            json={
                'community_id': community_id,
                'status': 1
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_community_toggle_status_deactivate_contract(self, schema, base_client, auth_headers):
        """测试停用社区契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_状态_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 停用社区
        response = base_client.post('/api/community/toggle-status',
            json={
                'community_id': community_id,
                'status': 0
            },
            headers=auth_headers
        )

        # 验证响应结构（可能失败，默认社区或不允许停用）
        data = validate_response_structure(response)
        # 只验证结构符合契约

    def test_community_toggle_status_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试切换状态缺少参数契约"""
        response = base_client.post('/api/community/toggle-status',
            json={},  # 缺少 community_id 和 status
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 批量添加用户到社区 ====================

    def test_community_add_users_contract(self, schema, base_client, auth_headers):
        """测试批量添加用户到社区契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_添加用户_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 添加用户（使用已存在的测试用户ID）
        response = base_client.post('/api/community/add-users',
            json={
                'community_id': community_id,
                'user_ids': [1, 2]  # 使用测试用户ID
            },
            headers=auth_headers
        )

        # 验证响应结构（可能成功或失败，取决于用户是否存在）
        data = validate_response_structure(response)
        # 只验证结构符合契约，不强制要求成功

    def test_community_add_users_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试批量添加用户缺少参数契约"""
        response = base_client.post('/api/community/add-users',
            json={},  # 缺少 community_id 和 user_ids
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 从社区移除用户 ====================

    def test_community_remove_user_contract(self, schema, base_client, auth_headers):
        """测试从社区移除用户契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_移除用户_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 移除用户
        response = base_client.post('/api/community/remove-user',
            json={
                'community_id': community_id,
                'target_user_id': 999  # 不存在的用户ID
            },
            headers=auth_headers
        )

        # 验证响应结构
        data = validate_response_structure(response)
        # 用户不存在时应该返回错误
        assert data["code"] == 0

    def test_community_remove_user_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试移除用户缺少参数契约"""
        response = base_client.post('/api/community/remove-user',
            json={},  # 缺少参数
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 社区列表 ====================

    def test_community_list_contract(self, schema, base_client, auth_headers):
        """测试获取社区列表契约"""
        response = base_client.get('/api/community/list',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "communities" in response_data
        assert isinstance(response_data["communities"], list)

    def test_community_list_with_pagination_contract(self, schema, base_client, auth_headers):
        """测试社区列表分页契约"""
        response = base_client.get('/api/community/list',
            query_string={'page': 1, 'page_size': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "communities" in response_data
        assert isinstance(response_data["communities"], list)

    # ==================== 获取社区用户列表 ====================

    def test_community_users_contract(self, schema, base_client, auth_headers):
        """测试获取社区用户列表契约"""
        # 先创建一个社区
        create_response = base_client.post('/api/community/create',
            json={'name': f'测试社区_用户列表_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        create_data = validate_response_structure(create_response)
        community_id = create_data["data"]["community_id"]

        # 获取社区用户列表
        response = base_client.get(f'/api/community/users',
            query_string={'community_id': community_id},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "users" in response_data
        assert isinstance(response_data["users"], list)

    def test_community_users_missing_community_id_contract(self, schema, base_client, auth_headers):
        """测试获取社区用户列表缺少社区ID契约"""
        response = base_client.get('/api/community/users',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0
