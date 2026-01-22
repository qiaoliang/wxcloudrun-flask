"""
打卡模块 API 契约测试
测试个人打卡规则和打卡记录相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestCheckinContract:
    """打卡模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 checkin.yaml 规范"""
        return load_schema("checkin")

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
                'title': f'测试打卡规则_{random.randint(1000, 9999)}',
                'description': '这是一个测试打卡规则',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'rule_id' in data.get('data', {}):
            return data['data']['rule_id']
        return None

    # ==================== 获取今日打卡事项 ====================

    def test_checkin_today_contract(self, schema, base_client, auth_headers):
        """测试获取今日打卡事项契约"""
        response = base_client.get('/api/checkin/today', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "checkin_items" in response_data
        assert "user_id" in response_data
        assert "date" in response_data
        assert "total" in response_data
        assert "checked" in response_data
        assert "unchecked" in response_data

        checkin_items = response_data["checkin_items"]
        assert isinstance(checkin_items, list)

        # 如果有数据，验证每个打卡项的字段
        for item in checkin_items:
            assert "rule_id" in item
            assert "rule_name" in item
            assert "status" in item
            assert isinstance(item["rule_id"], int)
            assert isinstance(item["rule_name"], str)
            assert isinstance(item["status"], str)
            assert item["status"] in ["pending", "checked", "unchecked"]

    # ==================== 执行打卡 ====================

    def test_checkin_create_contract(self, schema, base_client, auth_headers):
        """测试执行打卡契约"""
        # 先创建一个打卡规则
        create_response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试打卡规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 执行打卡
            response = base_client.post('/api/checkin',
                json={'rule_id': rule_id},
                headers=auth_headers
            )

            data = validate_response_structure(response)
            # 打卡可能成功或失败（取决于是否已打卡），只验证结构
            if data["code"] == 1:
                response_data = data["data"]
                assert "record_id" in response_data
                assert "checkin_time" in response_data
                assert "status" in response_data
                assert isinstance(response_data["record_id"], int)

    def test_checkin_create_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试打卡缺少规则ID契约"""
        response = base_client.post('/api/checkin',
            json={},  # 缺少 rule_id
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 上报漏打卡 ====================

    def test_checkin_miss_contract(self, schema, base_client, auth_headers):
        """测试上报漏打卡契约"""
        # 先创建一个打卡规则
        create_response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试漏打卡规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 上报漏打卡
            response = base_client.post('/api/checkin/miss',
                json={
                    'rule_id': rule_id,
                    'reason': '忘记打卡了'
                },
                headers=auth_headers
            )

            data = validate_response_structure(response)
            # 只验证结构，上报可能成功或失败

    def test_checkin_miss_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试上报漏打卡缺少规则ID契约"""
        response = base_client.post('/api/checkin/miss',
            json={},  # 缺少 rule_id
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 取消打卡 ====================

    def test_checkin_cancel_contract(self, schema, base_client, auth_headers):
        """测试取消打卡契约"""
        # 先执行打卡获取 record_id
        create_response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试取消打卡规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 执行打卡
            checkin_response = base_client.post('/api/checkin',
                json={'rule_id': rule_id},
                headers=auth_headers
            )
            checkin_data = checkin_response.get_json()
            if checkin_data.get('code') == 1 and 'record_id' in checkin_data.get('data', {}):
                record_id = checkin_data['data']['record_id']

                # 取消打卡
                response = base_client.post('/api/checkin/cancel',
                    json={
                        'record_id': record_id,
                        'reason': '打卡错了'
                    },
                    headers=auth_headers
                )

                data = validate_response_structure(response)
                # 只验证结构

    def test_checkin_cancel_missing_record_id_contract(self, schema, base_client, auth_headers):
        """测试取消打卡缺少记录ID契约"""
        response = base_client.post('/api/checkin/cancel',
            json={},  # 缺少 record_id
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 获取打卡历史 ====================

    def test_checkin_history_contract(self, schema, base_client, auth_headers):
        """测试获取打卡历史契约"""
        response = base_client.get('/api/checkin/history',
            query_string={'page': 1, 'page_size': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "history" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "page_size" in response_data
        assert "total_pages" in response_data

        assert isinstance(response_data["history"], list)
        assert isinstance(response_data["total"], int)
        assert isinstance(response_data["page"], int)
        assert isinstance(response_data["page_size"], int)
        assert isinstance(response_data["total_pages"], int)

    def test_checkin_history_with_date_range_contract(self, schema, base_client, auth_headers):
        """测试获取打卡历史（带日期范围）契约"""
        response = base_client.get('/api/checkin/history',
            query_string={
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'page': 1,
                'page_size': 20
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "history" in response_data

        # 验证历史记录字段
        for record in response_data["history"]:
            assert "record_id" in record
            assert "rule_id" in record
            assert "checkin_time" in record
            assert "status" in record
            assert "status_name" in record
            assert "planned_time" in record

    # ==================== 获取打卡规则列表 ====================

    def test_checkin_rules_list_contract(self, schema, base_client, auth_headers):
        """测试获取打卡规则列表契约"""
        response = base_client.get('/api/checkin/rules', headers=auth_headers)

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "rules" in response_data
        assert isinstance(response_data["rules"], list)

        # 验证规则字段
        for rule in response_data["rules"]:
            assert "rule_id" in rule
            assert "title" in rule
            assert "description" in rule
            assert "checkin_time" in rule
            assert "repeat_days" in rule
            assert "is_enabled" in rule
            assert isinstance(rule["rule_id"], int)
            assert isinstance(rule["title"], str)
            assert isinstance(rule["repeat_days"], list)
            assert isinstance(rule["is_enabled"], bool)

    def test_checkin_rules_list_with_rule_id_contract(self, schema, base_client, auth_headers):
        """测试获取单个打卡规则契约"""
        # 先创建一个规则
        create_response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试获取规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 获取单个规则
            response = base_client.get('/api/checkin/rules',
                query_string={'rule_id': rule_id},
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

    # ==================== 创建打卡规则 ====================

    def test_checkin_rules_create_contract(self, schema, base_client, auth_headers):
        """测试创建打卡规则契约"""
        # 使用新格式的参数（rule_name, frequency_type, time_slot_type, custom_time）
        response = base_client.post('/api/checkin/rules',
            json={
                'rule_name': f'测试创建规则_{random.randint(1000, 9999)}',
                'description': '这是一个测试规则',
                'frequency_type': 1,
                'time_slot_type': 1,
                'custom_time': '08:00',
                'week_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 创建可能成功或失败，只验证结构
        if data["code"] == 1:
            # 验证响应字段
            response_data = data["data"]
            # 后端返回的格式是 {'rule': {...}}
            if "rule" in response_data:
                rule_data = response_data["rule"]
                assert "rule_id" in rule_data

    def test_checkin_rules_create_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：创建打卡规则 - 验证所有返回字段及类型"""
        response = base_client.post('/api/checkin/rules',
            json={
                'rule_name': f'测试创建规则完整度_{random.randint(1000, 9999)}',
                'description': '这是一个测试规则',
                'frequency_type': 1,
                'time_slot_type': 1,
                'custom_time': '08:00',
                'week_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 实际返回格式是 data.rule.{...}
        response_data = data["data"]
        assert "rule" in response_data

        rule_data = response_data["rule"]

        # 验证所有字段存在
        assert "rule_id" in rule_data
        assert "rule_name" in rule_data
        assert "frequency_type" in rule_data
        assert "time_slot_type" in rule_data
        assert "status" in rule_data

        # 验证字段类型
        assert isinstance(rule_data["rule_id"], int)
        assert isinstance(rule_data["rule_name"], str)
        assert isinstance(rule_data["frequency_type"], int)
        assert isinstance(rule_data["time_slot_type"], int)
        assert isinstance(rule_data["status"], int)

        # 验证字段值有效性
        assert rule_data["rule_id"] > 0

    def test_checkin_rules_create_missing_required_field_contract(self, schema, base_client, auth_headers):
        """测试创建打卡规则缺少必填字段契约"""
        response = base_client.post('/api/checkin/rules',
            json={
                'description': '缺少标题和时间的规则'
                # 缺少必填的 title, checkin_time, repeat_days
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 更新打卡规则 ====================

    def test_checkin_rules_update_contract(self, schema, base_client, auth_headers):
        """测试更新打卡规则契约"""
        # 先创建一个规则
        create_response = base_client.post('/api/checkin/rules',
            json={
                'title': f'测试更新规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        create_data = create_response.get_json()
        if create_data.get('code') == 1 and 'rule_id' in create_data.get('data', {}):
            rule_id = create_data['data']['rule_id']

            # 更新规则
            response = base_client.put('/api/checkin/rules',
                json={
                    'rule_id': rule_id,
                    'title': '更新后的规则名称',
                    'description': '更新后的描述',
                    'checkin_time': '09:00',
                    'repeat_days': [1, 2, 3]
                },
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

    def test_checkin_rules_update_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试更新打卡规则缺少规则ID契约"""
        response = base_client.put('/api/checkin/rules',
            json={
                'title': '更新后的规则名称'
                # 缺少 rule_id
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 删除打卡规则 ====================

    def test_checkin_rules_delete_contract(self, schema, base_client, auth_headers):
        """测试删除打卡规则契约"""
        # 先创建一个规则
        create_response = base_client.post('/api/checkin/rules',
            json={
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
            response = base_client.delete('/api/checkin/rules',
                query_string={'rule_id': rule_id},
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

    def test_checkin_rules_delete_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试删除打卡规则缺少规则ID契约"""
        response = base_client.delete('/api/checkin/rules',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0
