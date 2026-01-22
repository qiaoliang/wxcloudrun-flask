"""
社区仪表板模块 API 契约测试
测试社区统计数据、异常用户、趋势等相关 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestCommunityDashboardContract:
    """社区仪表板模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 community-dashboard.yaml 规范"""
        return load_schema("community-dashboard")

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
            json={'name': f'测试仪表板社区_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'community_id' in data.get('data', {}):
            return data['data']['community_id']
        return 1  # 返回默认社区ID

    # ==================== 获取社区统计数据 ====================

    def test_community_dashboard_stats_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区统计数据契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/stats',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["user_count", "staff_count", "active_events", "checkin_rate"]
        for field in required_fields:
            assert field in response_data, f"社区统计数据响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["user_count"], int)
        assert isinstance(response_data["staff_count"], int)
        assert isinstance(response_data["active_events"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))

    def test_community_dashboard_stats_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：获取社区统计数据 - 验证所有返回字段及类型"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/stats',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "user_count" in response_data
        assert "staff_count" in response_data
        assert "active_events" in response_data
        assert "checkin_rate" in response_data

        # 验证字段类型
        assert isinstance(response_data["user_count"], int)
        assert isinstance(response_data["staff_count"], int)
        assert isinstance(response_data["active_events"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))

        # 验证字段值有效性
        assert response_data["user_count"] >= 0
        assert response_data["staff_count"] >= 0
        assert response_data["active_events"] >= 0
        assert response_data["checkin_rate"] >= 0
        assert response_data["checkin_rate"] <= 100

    # ==================== 获取异常用户列表 ====================

    def test_community_dashboard_abnormal_users_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取异常用户列表契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/abnormal-users',
            query_string={'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "users" in response_data
        assert "total" in response_data
        assert isinstance(response_data["users"], list)
        assert isinstance(response_data["total"], int)

    def test_community_dashboard_abnormal_users_with_pagination_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取异常用户列表（带分页）契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/abnormal-users',
            query_string={'page': 2, 'per_page': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "users" in response_data
        assert "total" in response_data

    # ==================== 获取历史趋势数据 ====================

    def test_community_dashboard_trends_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取历史趋势数据契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/trends',
            query_string={'days': 7},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应是数组
        response_data = data["data"]
        assert isinstance(response_data, list)

        # 验证趋势数据字段
        for trend in response_data:
            assert "date" in trend
            assert "checkin_rate" in trend
            assert "active_events" in trend

            assert isinstance(trend["date"], str)
            assert isinstance(trend["checkin_rate"], (int, float))
            assert isinstance(trend["active_events"], int)

    def test_community_dashboard_trends_default_days_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取历史趋势数据（默认天数）契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/trends',
            headers=auth_headers
            # 不指定 days，默认为 7
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert isinstance(response_data, list)
        # 默认7天应该返回7条数据
        assert len(response_data) == 7

    # ==================== 获取未处理事件列表 ====================

    def test_community_dashboard_pending_events_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取未处理事件列表契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/pending-events',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应是数组
        response_data = data["data"]
        assert isinstance(response_data, list)

        # 验证事件字段（根据 EventInfo schema）
        for event in response_data:
            assert "event_id" in event
            assert "community_id" in event
            assert "user_id" in event
            assert "event_type" in event
            assert "title" in event
            assert "status" in event
            assert "created_at" in event

            # 验证 event_type 枚举值
            assert event["event_type"] in ["help", "support"]

            # 验证 status 枚举值
            assert event["status"] in ["active", "closed"]

    def test_community_dashboard_pending_events_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：获取未处理事件列表 - 验证所有返回字段及类型"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/pending-events',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段（EventInfo）
        response_data = data["data"]

        for event in response_data:
            # 验证所有字段存在
            assert "event_id" in event
            assert "community_id" in event
            assert "user_id" in event
            assert "event_type" in event
            assert "title" in event
            assert "status" in event
            assert "created_at" in event

            # 验证字段类型
            assert isinstance(event["event_id"], int)
            assert isinstance(event["community_id"], int)
            assert isinstance(event["user_id"], int)
            assert isinstance(event["event_type"], str)
            assert isinstance(event["title"], str)
            assert isinstance(event["status"], str)
            assert isinstance(event["created_at"], str)

            # 验证字段值有效性
            assert event["event_type"] in ["help", "support"]
            assert event["status"] in ["active", "closed"]

    # ==================== 获取用户异常值详情 ====================

    def test_community_dashboard_user_abnormality_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取用户异常值详情契约"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/user-abnormality/1',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["user_id", "abnormality_score", "missed_checkins", "last_checkin"]
        for field in required_fields:
            assert field in response_data, f"用户异常值详情响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["user_id"], int)
        assert isinstance(response_data["abnormality_score"], (int, float))
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["last_checkin"], str)

    def test_community_dashboard_user_abnormality_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：获取用户异常值详情 - 验证所有返回字段及类型"""
        response = base_client.get(f'/api/community-dashboard/{test_community_id}/user-abnormality/1',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "user_id" in response_data
        assert "abnormality_score" in response_data
        assert "missed_checkins" in response_data
        assert "last_checkin" in response_data

        # 验证字段类型
        assert isinstance(response_data["user_id"], int)
        assert isinstance(response_data["abnormality_score"], (int, float))
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["last_checkin"], str)

        # 验证字段值有效性
        assert response_data["user_id"] == 1
        assert response_data["abnormality_score"] >= 0
        assert response_data["missed_checkins"] >= 0
        assert len(response_data["last_checkin"]) > 0
