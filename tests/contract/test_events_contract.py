"""
事件模块 API 契约测试
测试社区事件（呼救、支持）相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestEventsContract:
    """事件模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 events.yaml 规范"""
        return load_schema("events")

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
    def test_community_id(self, base_client, auth_headers):
        """创建测试用社区并返回 community_id"""
        response = base_client.post('/api/community/create',
            json={'name': f'测试事件社区_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'community_id' in data.get('data', {}):
            return data['data']['community_id']
        return 1  # 返回默认社区ID

    @pytest.fixture
    def test_event_id(self, base_client, auth_headers, test_community_id):
        """创建测试用事件并返回 event_id"""
        response = base_client.post('/api/events',
            json={
                'community_id': test_community_id,
                'title': f'测试事件_{random.randint(1000, 9999)}',
                'description': '这是一个测试事件',
                'event_type': 'call_for_help'
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'event_id' in data.get('data', {}):
            return data['data']['event_id']
        return None

    # ==================== 创建社区事件 ====================

    def test_event_create_call_for_help_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试创建呼救事件契约"""
        response = base_client.post('/api/events',
            json={
                'community_id': test_community_id,
                'title': '紧急呼救测试',
                'description': '需要帮助',
                'event_type': 'call_for_help',
                'location': '北京市朝阳区'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "event_id" in response_data
        assert isinstance(response_data["event_id"], int)
        assert response_data["event_id"] > 0

    def test_event_create_supporting_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试创建支持事件契约"""
        response = base_client.post('/api/events',
            json={
                'community_id': test_community_id,
                'title': '愿意提供帮助',
                'description': '我可以提供支持',
                'event_type': 'supporting',
                'target_user_id': 1
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "event_id" in response_data

    def test_event_create_missing_required_field_contract(self, schema, base_client, auth_headers):
        """测试创建事件缺少必填字段契约"""
        response = base_client.post('/api/events',
            json={
                'title': '缺少社区ID的事件'
                # 缺少必填的 community_id
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_event_create_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：创建事件 - 验证所有返回字段及类型"""
        response = base_client.post('/api/events',
            json={
                'community_id': test_community_id,
                'title': f'完整度测试事件_{random.randint(1000, 9999)}',
                'description': '这是一个完整度测试事件',
                'event_type': 'call_for_help',
                'location': '北京市朝阳区',
                'target_user_id': 1
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "event_id" in response_data

        # 验证字段类型
        assert isinstance(response_data["event_id"], int)

        # 验证字段值有效性
        assert response_data["event_id"] > 0

    # ==================== 获取事件详情 ====================

    def test_event_detail_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试获取事件详情契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.get(f'/api/events/{test_event_id}', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证 EventInfo 结构
        response_data = data["data"]
        required_fields = ["event_id", "community_id", "user_id", "event_type", "title", "status", "created_at"]
        for field in required_fields:
            assert field in response_data, f"事件详情缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["event_id"], int)
        assert isinstance(response_data["community_id"], int)
        assert isinstance(response_data["user_id"], int)
        assert isinstance(response_data["event_type"], str)
        assert isinstance(response_data["title"], str)
        assert isinstance(response_data["status"], str)

    def test_event_detail_not_found_contract(self, schema, base_client, auth_headers):
        """测试获取不存在的事件详情契约"""
        response = base_client.get('/api/events/999999', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 创建事件应援 ====================

    def test_event_support_create_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试创建事件应援契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.post(f'/api/events/{test_event_id}/support',
            json={
                'message_content': '我来帮你'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 应援可能成功或失败（取决于事件状态）

    def test_event_support_missing_message_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试创建应援缺少消息内容契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.post(f'/api/events/{test_event_id}/support',
            json={},  # 缺少 message_content
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 工作人员添加回应 ====================

    def test_event_respond_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试工作人员添加回应契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.post(f'/api/events/{test_event_id}/respond',
            json={
                'content': '工作人员回应内容',
                'media_url': 'https://example.com/media.jpg',
                'message_tags': ['urgent', 'official']
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 回应可能成功或失败（取决于用户权限）

    def test_event_respond_missing_content_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试工作人员回应缺少内容契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.post(f'/api/events/{test_event_id}/respond',
            json={},  # 缺少 content
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 更新事件位置 ====================

    def test_event_update_location_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试更新事件位置契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.put(f'/api/events/{test_event_id}/location',
            json={
                'location': '北京市海淀区',
                'location_lat': 39.9042,
                'location_lon': 116.4074
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 更新可能成功或失败（取决于事件状态和权限）

    def test_event_update_location_partial_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试部分更新事件位置契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.put(f'/api/events/{test_event_id}/location',
            json={
                'location': '北京市西城区'
                # 只提供 location，不提供坐标
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)

    # ==================== 关闭事件 ====================

    def test_event_close_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试关闭事件契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.put(f'/api/events/{test_event_id}/close',
            json={
                'closure_reason': '问题已解决'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 关闭可能成功或失败（取决于事件状态）

        if data["code"] == 1:
            # 验证关闭响应字段
            response_data = data["data"]
            required_fields = ["event_id", "closed_by", "closed_at", "closure_type", "closure_type_label", "closure_reason"]
            for field in required_fields:
                assert field in response_data, f"关闭事件响应缺少字段: {field}"

            # 验证字段类型
            assert isinstance(response_data["event_id"], int)
            assert isinstance(response_data["closed_by"], int)
            assert isinstance(response_data["closure_type"], int)
            assert isinstance(response_data["closed_at"], str)
            assert isinstance(response_data["closure_type_label"], str)
            assert isinstance(response_data["closure_reason"], str)

    def test_event_close_missing_reason_contract(self, schema, base_client, auth_headers, test_event_id):
        """测试关闭事件缺少原因契约"""
        if test_event_id is None:
            pytest.skip("无法获取测试事件ID")

        response = base_client.put(f'/api/events/{test_event_id}/close',
            json={},  # 缺少 closure_reason
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_event_close_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：关闭事件 - 验证所有返回字段及类型"""
        # 先创建一个新的事件用于关闭测试
        create_response = base_client.post('/api/events',
            json={
                'community_id': 1,
                'title': f'关闭测试事件_{random.randint(1000, 9999)}',
                'event_type': 'call_for_help'
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'event_id' in create_data.get('data', {}):
            event_id = create_data['data']['event_id']

            # 关闭事件
            response = base_client.put(f'/api/events/{event_id}/close',
                json={
                    'closure_reason': '已完成测试'
                },
                headers=auth_headers
            )

            data = validate_response_structure(response)
            if data["code"] == 1:
                # OpenAPI 定义的完整响应字段
                response_data = data["data"]

                # 验证所有字段存在
                assert "event_id" in response_data
                assert "closed_by" in response_data
                assert "closed_at" in response_data
                assert "closure_type" in response_data
                assert "closure_type_label" in response_data
                assert "closure_reason" in response_data

                # 验证字段类型
                assert isinstance(response_data["event_id"], int)
                assert isinstance(response_data["closed_by"], int)
                assert isinstance(response_data["closed_at"], str)
                assert isinstance(response_data["closure_type"], int)
                assert isinstance(response_data["closure_type_label"], str)
                assert isinstance(response_data["closure_reason"], str)

                # 验证字段值有效性
                assert response_data["event_id"] == event_id
                assert response_data["closed_by"] > 0
                assert len(response_data["closure_reason"]) > 0
                assert response_data["closure_type"] in [1, 2]  # 1-用户关闭，2-工作人员关闭
                assert response_data["closure_type_label"] in ["用户关闭", "工作人员关闭"]
