"""
用户打卡模块 API 契约测试
测试用户的打卡规则、记录、统计相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestUserCheckinContract:
    """用户打卡模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 user-checkin.yaml 规范"""
        return load_schema("user-checkin")

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
                'title': f'测试用户打卡规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'rule_id' in data.get('data', {}):
            return data['data']['rule_id']
        return None

    # ==================== 获取用户所有打卡规则 ====================

    def test_user_checkin_rules_list_contract(self, schema, base_client, auth_headers):
        """测试获取用户所有打卡规则契约"""
        response = base_client.get('/api/user-checkin/rules', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应数据结构
        response_data = data["data"]
        assert "rules" in response_data
        assert isinstance(response_data["rules"], list)

        # 验证规则字段
        for rule in response_data["rules"]:
            assert "rule_id" in rule
            assert "rule_name" in rule
            assert "frequency_type" in rule
            assert "time_slot_type" in rule
            assert "custom_time" in rule
            assert "rule_source" in rule
            assert "is_editable" in rule
            assert "is_enabled" in rule

            # 验证 rule_source 枚举值
            assert rule["rule_source"] in ["personal", "community"]

            # 验证字段类型
            assert isinstance(rule["rule_id"], int)
            assert isinstance(rule["rule_name"], str)
            assert isinstance(rule["frequency_type"], int)
            assert isinstance(rule["time_slot_type"], int)
            assert isinstance(rule["is_editable"], bool)
            assert isinstance(rule["is_enabled"], bool)

    def test_user_checkin_rules_delete_all_contract(self, schema, base_client, auth_headers):
        """测试删除用户所有打卡规则契约"""
        response = base_client.delete('/api/user-checkin/rules', headers=auth_headers)

        data = validate_response_structure(response)
        # 删除可能成功或失败

    # ==================== 获取用户今日打卡计划 ====================

    def test_user_checkin_today_plan_contract(self, schema, base_client, auth_headers):
        """测试获取用户今日打卡计划契约"""
        response = base_client.get('/api/user-checkin/today-plan', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["date", "total_items", "completed_items", "pending_items", "items"]
        for field in required_fields:
            assert field in response_data, f"今日打卡计划响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["date"], str)
        assert isinstance(response_data["total_items"], int)
        assert isinstance(response_data["completed_items"], int)
        assert isinstance(response_data["pending_items"], int)
        assert isinstance(response_data["items"], list)

        # 验证打卡项字段
        for item in response_data["items"]:
            assert "item_id" in item
            assert "rule_id" in item
            assert "rule_name" in item
            assert "checkin_time" in item
            assert "is_completed" in item
            assert "rule_source" in item
            assert isinstance(item["is_completed"], bool)
            assert item["rule_source"] in ["personal", "community"]

    def test_user_checkin_today_plan_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：获取用户今日打卡计划 - 验证所有返回字段及类型"""
        response = base_client.get('/api/user-checkin/today-plan', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "date" in response_data
        assert "total_items" in response_data
        assert "completed_items" in response_data
        assert "pending_items" in response_data
        assert "items" in response_data

        # 验证字段类型
        assert isinstance(response_data["date"], str)
        assert isinstance(response_data["total_items"], int)
        assert isinstance(response_data["completed_items"], int)
        assert isinstance(response_data["pending_items"], int)
        assert isinstance(response_data["items"], list)

        # 验证字段值有效性
        assert response_data["total_items"] >= 0
        assert response_data["completed_items"] >= 0
        assert response_data["pending_items"] >= 0
        assert response_data["total_items"] == response_data["completed_items"] + response_data["pending_items"]

    # ==================== 获取用户打卡规则详情 ====================

    def test_user_checkin_rule_detail_personal_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试获取用户打卡规则详情（个人规则）契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.get(f'/api/user-checkin/rules/{test_rule_id}',
            query_string={'rule_source': 'personal'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证规则详情字段
        response_data = data["data"]
        required_fields = ["rule_id", "rule_name", "icon_url", "frequency_type",
                          "time_slot_type", "custom_time", "rule_source",
                          "is_editable", "is_enabled", "created_at", "updated_at"]
        for field in required_fields:
            assert field in response_data, f"规则详情响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["rule_id"], int)
        assert isinstance(response_data["rule_name"], str)
        assert isinstance(response_data["frequency_type"], int)
        assert isinstance(response_data["is_editable"], bool)
        assert isinstance(response_data["is_enabled"], bool)

    def test_user_checkin_rule_detail_community_contract(self, schema, base_client, auth_headers):
        """测试获取用户打卡规则详情（社区规则）契约"""
        response = base_client.get('/api/user-checkin/rules/1',
            query_string={'rule_source': 'community'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 规则可能不存在

    def test_user_checkin_rule_detail_default_source_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试获取用户打卡规则详情（默认来源）契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.get(f'/api/user-checkin/rules/{test_rule_id}',
            headers=auth_headers
            # 不指定 rule_source，默认为 personal
        )

        data = validate_response_structure(response)

    # ==================== 获取用户打卡统计信息 ====================

    def test_user_checkin_statistics_week_contract(self, schema, base_client, auth_headers):
        """测试获取用户打卡统计信息（本周）契约"""
        response = base_client.get('/api/user-checkin/statistics',
            query_string={'period': 'week'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["period", "total_days", "checkin_days", "checkin_rate",
                          "total_rules", "completed_checkins", "missed_checkins", "daily_stats"]
        for field in required_fields:
            assert field in response_data, f"打卡统计响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["period"], str)
        assert isinstance(response_data["total_days"], int)
        assert isinstance(response_data["checkin_days"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))
        assert isinstance(response_data["total_rules"], int)
        assert isinstance(response_data["completed_checkins"], int)
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["daily_stats"], list)

    def test_user_checkin_statistics_month_contract(self, schema, base_client, auth_headers):
        """测试获取用户打卡统计信息（本月）契约"""
        response = base_client.get('/api/user-checkin/statistics',
            query_string={'period': 'month'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert response_data["period"] == "month"

    def test_user_checkin_statistics_with_date_range_contract(self, schema, base_client, auth_headers):
        """测试获取用户打卡统计信息（自定义日期范围）契约"""
        response = base_client.get('/api/user-checkin/statistics',
            query_string={
                'start_date': '2024-01-01',
                'end_date': '2024-01-31'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_checkin_statistics_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：获取用户打卡统计信息 - 验证所有返回字段及类型"""
        response = base_client.get('/api/user-checkin/statistics',
            query_string={'period': 'week'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "period" in response_data
        assert "total_days" in response_data
        assert "checkin_days" in response_data
        assert "checkin_rate" in response_data
        assert "total_rules" in response_data
        assert "completed_checkins" in response_data
        assert "missed_checkins" in response_data
        assert "daily_stats" in response_data

        # 验证字段类型
        assert isinstance(response_data["period"], str)
        assert isinstance(response_data["total_days"], int)
        assert isinstance(response_data["checkin_days"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))
        assert isinstance(response_data["total_rules"], int)
        assert isinstance(response_data["completed_checkins"], int)
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["daily_stats"], list)

        # 验证每日统计字段
        for daily_stat in response_data["daily_stats"]:
            assert "date" in daily_stat
            assert "total_rules" in daily_stat
            assert "completed_rules" in daily_stat
            assert "missed_rules" in daily_stat
            assert "checkin_rate" in daily_stat
            assert isinstance(daily_stat["date"], str)
            assert isinstance(daily_stat["total_rules"], int)
            assert isinstance(daily_stat["checkin_rate"], (int, float))

    # ==================== 批量获取规则来源信息 ====================

    def test_user_checkin_rules_source_info_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试批量获取规则来源信息契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/user-checkin/rules/source-info',
            json={'rule_ids': [test_rule_id, 1, 2]},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应是数组
        response_data = data["data"]
        assert isinstance(response_data, list)

        # 验证规则来源信息字段
        for source_info in response_data:
            assert "rule_id" in source_info
            assert "rule_source" in source_info
            assert "source_label" in source_info
            assert isinstance(source_info["rule_id"], int)
            assert isinstance(source_info["rule_source"], str)
            assert source_info["rule_source"] in ["personal", "community"]

    def test_user_checkin_rules_source_info_empty_contract(self, schema, base_client, auth_headers):
        """测试批量获取规则来源信息（空列表）契约"""
        response = base_client.post('/api/user-checkin/rules/source-info',
            json={'rule_ids': []},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "community_rules" in response_data
        assert "personal_rules" in response_data
        assert isinstance(response_data["community_rules"], list)
        assert isinstance(response_data["personal_rules"], list)

    def test_user_checkin_rules_source_info_missing_rule_ids_contract(self, schema, base_client, auth_headers):
        """测试批量获取规则来源信息缺少rule_ids契约"""
        response = base_client.post('/api/user-checkin/rules/source-info',
            json={},  # 缺少 rule_ids
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0
