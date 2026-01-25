"""
社区打卡模块 API 契约测试
测试社区打卡规则、记录、统计相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestCommunityCheckinContract:
    """社区打卡模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 community-checkin.yaml 规范"""
        return load_schema("community-checkin")

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
            json={'name': f'测试社区打卡_{random.randint(1000, 9999)}'},
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'community_id' in data.get('data', {}):
            return data['data']['community_id']
        return 1  # 返回默认社区ID

    @pytest.fixture
    def test_rule_id(self, base_client, auth_headers, test_community_id):
        """创建测试用社区打卡规则并返回 rule_id"""
        response = base_client.post('/api/community_checkin/rules',
            json={
                'community_id': test_community_id,
                'title': f'测试社区规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'rule_id' in data.get('data', {}):
            return data['data']['rule_id']
        return None

    # ==================== 获取社区打卡规则列表 ====================

    def test_community_checkin_rules_list_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区打卡规则列表契约"""
        response = base_client.get('/api/community_checkin/rules',
            query_string={
                'community_id': test_community_id,
                'page': 1,
                'per_page': 20
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "rules" in response_data
        assert "total" in response_data
        assert isinstance(response_data["rules"], list)
        assert isinstance(response_data["total"], int)

        # 验证规则字段
        for rule in response_data["rules"]:
            assert "community_rule_id" in rule
            assert "rule_name" in rule
            assert "icon_url" in rule
            assert "description" in rule
            assert "checkin_time" in rule
            assert "repeat_days" in rule
            assert "is_enabled" in rule
            assert "created_by_name" in rule

            assert isinstance(rule["community_rule_id"], int)
            assert isinstance(rule["rule_name"], str)
            assert isinstance(rule["icon_url"], str)
            assert rule["icon_url"], "icon_url 不能为空"
            assert isinstance(rule["repeat_days"], list)
            assert isinstance(rule["is_enabled"], bool)

    def test_community_checkin_rules_list_with_status_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区打卡规则列表（带状态筛选）契约"""
        response = base_client.get('/api/community_checkin/rules',
            query_string={
                'community_id': test_community_id,
                'status': 'enabled',
                'page': 1,
                'per_page': 10
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        for rule in response_data["rules"]:
            # 筛选enabled时应该只返回启用的规则
            if rule.get("is_enabled") is not None:
                assert rule["is_enabled"] is True

    def test_community_checkin_rules_list_missing_community_id_contract(self, schema, base_client, auth_headers):
        """测试获取社区打卡规则列表缺少社区ID契约"""
        response = base_client.get('/api/community_checkin/rules',
            query_string={'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 创建社区打卡规则 ====================

    def test_community_checkin_rule_create_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试创建社区打卡规则契约"""
        response = base_client.post('/api/community_checkin/rules',
            json={
                'community_id': test_community_id,
                'title': f'测试社区打卡规则_{random.randint(1000, 9999)}',
                'description': '这是一个测试规则',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "rule_id" in response_data
        assert "message" in response_data
        assert isinstance(response_data["rule_id"], int)
        assert response_data["rule_id"] > 0

    def test_community_checkin_rule_create_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：创建社区打卡规则 - 验证所有返回字段及类型"""
        response = base_client.post('/api/community_checkin/rules',
            json={
                'community_id': test_community_id,
                'title': f'完整度测试规则_{random.randint(1000, 9999)}',
                'description': '这是一个完整度测试规则',
                'checkin_time': '09:00',
                'repeat_days': [1, 3, 5]
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "rule_id" in response_data
        assert "message" in response_data

        # 验证字段类型
        assert isinstance(response_data["rule_id"], int)
        assert isinstance(response_data["message"], str)

        # 验证字段值有效性
        assert response_data["rule_id"] > 0

    def test_community_checkin_rule_create_missing_required_field_contract(self, schema, base_client, auth_headers):
        """测试创建社区打卡规则缺少必填字段契约"""
        response = base_client.post('/api/community_checkin/rules',
            json={
                'title': '缺少社区ID的规则'
                # 缺少必填的 community_id, checkin_time, repeat_days
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 获取社区打卡规则详情 ====================

    def test_community_checkin_rule_detail_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试获取社区打卡规则详情契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.get(f'/api/community_checkin/rules/{test_rule_id}',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证规则详情字段
        response_data = data["data"]
        required_fields = ["community_rule_id", "rule_name", "description", "checkin_time",
                          "repeat_days", "is_enabled", "created_by_name", "created_at", "updated_at"]
        for field in required_fields:
            assert field in response_data, f"规则详情响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["community_rule_id"], int)
        assert isinstance(response_data["rule_name"], str)
        assert isinstance(response_data["repeat_days"], list)
        assert isinstance(response_data["is_enabled"], bool)

    def test_community_checkin_rule_detail_not_found_contract(self, schema, base_client, auth_headers):
        """测试获取不存在的社区打卡规则详情契约"""
        response = base_client.get('/api/community_checkin/rules/999999',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 更新社区打卡规则 ====================

    def test_community_checkin_rule_update_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试更新社区打卡规则契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.put(f'/api/community_checkin/rules/{test_rule_id}',
            json={
                'title': '更新后的规则名称',
                'description': '更新后的描述',
                'checkin_time': '10:00',
                'repeat_days': [2, 4, 6]
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "rule_id" in response_data
        assert "message" in response_data

    # ==================== 删除社区打卡规则 ====================

    def test_community_checkin_rule_delete_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试删除社区打卡规则契约"""
        # 先创建一个规则用于删除
        create_response = base_client.post('/api/community_checkin/rules',
            json={
                'community_id': test_community_id,
                'title': f'测试删除规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 删除规则
            response = base_client.delete(f'/api/community_checkin/rules/{rule_id}',
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

            response_data = data["data"]
            assert "rule_id" in response_data
            assert "message" in response_data

    # ==================== 启用/禁用社区打卡规则 ====================

    def test_community_checkin_rule_enable_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试启用社区打卡规则契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post(f'/api/community_checkin/rules/{test_rule_id}/enable',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "rule_id" in response_data
        assert "message" in response_data

    def test_community_checkin_rule_disable_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试禁用社区打卡规则契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post(f'/api/community_checkin/rules/{test_rule_id}/disable',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "rule_id" in response_data
        assert "message" in response_data

    # ==================== 获取社区每日打卡统计 ====================

    def test_community_checkin_daily_stats_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区每日打卡统计契约"""
        response = base_client.get(f'/api/community_checkin/stats/{test_community_id}/daily-stats',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["user_count", "total_rules", "total_checkins",
                          "completed_checkins", "missed_checkins", "checkin_rate", "unchecked_user_count"]
        for field in required_fields:
            assert field in response_data, f"社区每日打卡统计响应缺少字段: {field}"

        # 验证字段类型
        assert isinstance(response_data["user_count"], int)
        assert isinstance(response_data["total_rules"], int)
        assert isinstance(response_data["total_checkins"], int)
        assert isinstance(response_data["completed_checkins"], int)
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))
        assert isinstance(response_data["unchecked_user_count"], int)

    def test_community_checkin_daily_stats_field_types_100_percent(self, schema, base_client, auth_headers, test_community_id):
        """100% 完整度验证：获取社区每日打卡统计 - 验证所有返回字段及类型"""
        response = base_client.get(f'/api/community_checkin/stats/{test_community_id}/daily-stats',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "user_count" in response_data
        assert "total_rules" in response_data
        assert "total_checkins" in response_data
        assert "completed_checkins" in response_data
        assert "missed_checkins" in response_data
        assert "checkin_rate" in response_data
        assert "unchecked_user_count" in response_data

        # 验证字段类型
        assert isinstance(response_data["user_count"], int)
        assert isinstance(response_data["total_rules"], int)
        assert isinstance(response_data["total_checkins"], int)
        assert isinstance(response_data["completed_checkins"], int)
        assert isinstance(response_data["missed_checkins"], int)
        assert isinstance(response_data["checkin_rate"], (int, float))
        assert isinstance(response_data["unchecked_user_count"], int)

        # 验证字段值有效性
        assert response_data["user_count"] >= 0
        assert response_data["total_rules"] >= 0
        assert response_data["checkin_rate"] >= 0
        assert response_data["checkin_rate"] <= 100

    # ==================== 获取社区打卡统计信息 ====================

    def test_community_checkin_checkin_stats_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区打卡统计信息契约"""
        response = base_client.get(f'/api/community_checkin/stats/{test_community_id}/checkin-stats',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "stats" in response_data
        assert "total_rules" in response_data
        assert isinstance(response_data["stats"], list)
        assert isinstance(response_data["total_rules"], int)

        # 验证统计项字段
        for stat in response_data["stats"]:
            assert "rule_id" in stat
            assert "rule_name" in stat
            assert "rule_icon" in stat
            assert "total_missed" in stat
            assert "daily_missed" in stat
            assert "dates" in stat

            assert isinstance(stat["rule_id"], int)
            assert isinstance(stat["rule_name"], str)
            assert isinstance(stat["total_missed"], int)
            assert isinstance(stat["daily_missed"], list)
            assert isinstance(stat["dates"], list)

    def test_community_checkin_checkin_stats_with_days_contract(self, schema, base_client, auth_headers, test_community_id):
        """测试获取社区打卡统计信息（指定天数）契约"""
        response = base_client.get(f'/api/community_checkin/stats/{test_community_id}/checkin-stats',
            query_string={'days': 14},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        for stat in response_data["stats"]:
            # 验证每日数据长度与天数匹配
            assert len(stat["daily_missed"]) == 14
            assert len(stat["dates"]) == 14
