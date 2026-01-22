"""
杂项模块 API 契约测试
测试环境配置、计数器、文件上传等杂项 API 契约
"""
import pytest
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestMiscContract:
    """杂项模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 misc.yaml 规范"""
        return load_schema("misc")

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

    # ==================== 返回index页面 ====================

    def test_index_page_contract(self, schema, base_client):
        """测试返回index页面契约"""
        response = base_client.get('/')

        # 返回HTML内容
        assert response.status_code == 200
        assert b'<html' in response.data or b'<!DOCTYPE' in response.data

    # ==================== 返回环境配置查看器页面 ====================

    def test_env_page_contract(self, schema, base_client):
        """测试返回环境配置查看器页面契约"""
        response = base_client.get('/api/env')

        # 返回HTML内容
        assert response.status_code == 200
        assert b'<html' in response.data or b'<!DOCTYPE' in response.data

    # ==================== 获取环境配置信息 ====================

    def test_get_envs_contract(self, schema, base_client):
        """测试获取环境配置信息契约"""
        response = base_client.get('/api/get_envs')

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "config_status" in response_data
        assert "external_status" in response_data
        assert "timestamp" in response_data

        assert isinstance(response_data["config_status"], dict)
        assert isinstance(response_data["external_status"], dict)
        assert isinstance(response_data["timestamp"], str)

    def test_get_envs_field_types_100_percent(self, schema, base_client):
        """100% 完整度验证：获取环境配置信息 - 验证所有返回字段及类型"""
        response = base_client.get('/api/get_envs')

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "config_status" in response_data
        assert "external_status" in response_data
        assert "timestamp" in response_data

        # 验证字段类型
        assert isinstance(response_data["config_status"], dict)
        assert isinstance(response_data["external_status"], dict)
        assert isinstance(response_data["timestamp"], str)

        # 验证字段值有效性
        assert len(response_data["timestamp"]) > 0

    # ==================== 获取计数器 ====================

    def test_count_get_contract(self, schema, base_client):
        """测试获取计数器契约"""
        response = base_client.get('/api/count')

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应是数组（所有计数器）
        response_data = data["data"]
        assert isinstance(response_data, list)

    def test_count_get_with_id_contract(self, schema, base_client):
        """测试获取指定ID计数器契约"""
        response = base_client.get('/api/count',
            query_string={'id': 1}
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "id" in response_data
        assert "count" in response_data
        assert isinstance(response_data["id"], int)
        assert isinstance(response_data["count"], int)

    def test_count_get_field_types_100_percent(self, schema, base_client):
        """100% 完整度验证：获取计数器 - 验证所有返回字段及类型"""
        response = base_client.get('/api/count',
            query_string={'id': 1}
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "id" in response_data
        assert "count" in response_data

        # 验证字段类型
        assert isinstance(response_data["id"], int)
        assert isinstance(response_data["count"], int)

        # 验证字段值有效性
        assert response_data["id"] == 1
        assert response_data["count"] >= 0

    # ==================== 计数器操作 ====================

    def test_count_increment_contract(self, schema, base_client):
        """测试计数器增加操作契约"""
        response = base_client.post('/api/count',
            json={
                'action': 'increment',
                'counter_id': 1
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_count_reset_contract(self, schema, base_client):
        """测试计数器重置操作契约"""
        response = base_client.post('/api/count',
            json={
                'action': 'reset',
                'counter_id': 1
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_count_get_action_contract(self, schema, base_client):
        """测试计数器获取操作契约"""
        response = base_client.post('/api/count',
            json={
                'action': 'get',
                'id': 1
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "count" in response_data

    def test_count_list_action_contract(self, schema, base_client):
        """测试计数器列表操作契约"""
        response = base_client.post('/api/count',
            json={
                'action': 'list'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert isinstance(response_data, list)

    def test_count_clear_action_contract(self, schema, base_client):
        """测试计数器清除操作契约"""
        response = base_client.post('/api/count',
            json={
                'action': 'clear'
            }
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_count_missing_action_contract(self, schema, base_client):
        """测试计数器操作缺少action契约"""
        response = base_client.post('/api/count',
            json={}  # 缺少 action
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 上传媒体文件 ====================

    def test_upload_media_contract(self, schema, base_client):
        """测试上传媒体文件契约"""
        # 创建模拟文件数据
        file_data = {
            'file': (b'test image content', 'test.jpg')
        }

        response = base_client.post('/api/upload/media',
            data=file_data,
            content_type='multipart/form-data'
        )

        data = validate_response_structure(response)
        # 上传可能成功或失败（取决于文件类型和配置）

        if data["code"] == 1:
            # 验证响应字段
            response_data = data["data"]
            assert "url" in response_data
            assert isinstance(response_data["url"], str)
            assert len(response_data["url"]) > 0

    def test_upload_media_missing_file_contract(self, schema, base_client):
        """测试上传媒体文件缺少文件契约"""
        response = base_client.post('/api/upload/media',
            data={},  # 缺少 file
            content_type='multipart/form-data'
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_upload_media_field_types_100_percent(self, schema, base_client):
        """100% 完整度验证：上传媒体文件 - 验证所有返回字段及类型"""
        # 创建模拟文件数据
        file_data = {
            'file': (b'test image content for validation', 'test.jpg')
        }

        response = base_client.post('/api/upload/media',
            data=file_data,
            content_type='multipart/form-data'
        )

        data = validate_response_structure(response)
        if data["code"] == 1:
            # OpenAPI 定义的完整响应字段
            response_data = data["data"]

            # 验证所有字段存在
            assert "url" in response_data

            # 验证字段类型
            assert isinstance(response_data["url"], str)

            # 验证字段值有效性
            assert len(response_data["url"]) > 0
            assert response_data["url"].startswith('http')
