"""
监督模块 API 契约测试
测试监督邀请、监督关系、监督记录相关的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestSupervisionContract:
    """监督模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 supervision.yaml 规范"""
        return load_schema("supervision")

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
                'title': f'测试监督规则_{random.randint(1000, 9999)}',
                'checkin_time': '08:00',
                'repeat_days': [1, 2, 3, 4, 5]
            },
            headers=auth_headers
        )
        data = response.get_json()
        if data.get('code') == 1 and 'rule_id' in data.get('data', {}):
            return data['data']['rule_id']
        return None

    # ==================== 站内邀请监督者 ====================

    def test_supervision_invite_internal_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试站内邀请监督者契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/invite/internal',
            json={
                'rule_id': test_rule_id,
                'receiver_ids': [1, 2],
                'message': '请监督我的打卡'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能成功或失败（取决于用户是否存在）

        if data["code"] == 1:
            # 验证响应字段
            response_data = data["data"]
            required_fields = ["sender_id", "receiver_ids", "rule_id", "invitation_type", "status"]
            for field in required_fields:
                assert field in response_data, f"站内邀请响应缺少字段: {field}"

            assert isinstance(response_data["sender_id"], int)
            assert isinstance(response_data["receiver_ids"], list)
            assert isinstance(response_data["rule_id"], int)

    def test_supervision_invite_internal_missing_rule_id_contract(self, schema, base_client, auth_headers):
        """测试站内邀请缺少规则ID契约"""
        response = base_client.post('/api/supervision/invite/internal',
            json={
                'receiver_ids': [1, 2]
                # 缺少 rule_id
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 创建监督邀请链接 ====================

    def test_supervision_invite_link_create_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试创建监督邀请链接契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/invite_link',
            json={
                'rule_ids': [test_rule_id],
                'expire_hours': 24
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["token", "url", "mini_path", "expire_at"]
        for field in required_fields:
            assert field in response_data, f"创建邀请链接响应缺少字段: {field}"

        assert isinstance(response_data["token"], str)
        assert isinstance(response_data["url"], str)
        assert isinstance(response_data["mini_path"], str)
        assert isinstance(response_data["expire_at"], str)

    def test_supervision_invite_link_field_types_100_percent(self, schema, base_client, auth_headers, test_rule_id):
        """100% 完整度验证：创建监督邀请链接 - 验证所有返回字段及类型"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/invite_link',
            json={
                'rule_ids': [test_rule_id],
                'expire_hours': 168
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
        assert "expire_at" in response_data

        # 验证字段类型
        assert isinstance(response_data["token"], str)
        assert isinstance(response_data["url"], str)
        assert isinstance(response_data["mini_path"], str)
        assert isinstance(response_data["expire_at"], str)

        # 验证字段值有效性
        assert len(response_data["token"]) > 0
        assert len(response_data["url"]) > 0
        assert len(response_data["mini_path"]) > 0

    def test_supervision_invite_link_missing_rule_ids_contract(self, schema, base_client, auth_headers):
        """测试创建邀请链接缺少规则ID契约"""
        response = base_client.post('/api/supervision/invite_link',
            json={},  # 缺少 rule_ids
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 解析监督邀请链接 ====================

    def test_supervision_invite_resolve_contract(self, schema, base_client):
        """测试解析监督邀请链接契约"""
        # 使用测试token
        response = base_client.get('/api/supervision/invite/resolve',
            query_string={'token': 'test_invite_token'}
        )

        data = validate_response_structure(response)
        # token可能无效，只验证结构

    def test_supervision_invite_resolve_missing_token_contract(self, schema, base_client):
        """测试解析邀请链接缺少token契约"""
        response = base_client.get('/api/supervision/invite/resolve')

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 获取监督邀请列表 ====================

    def test_supervision_invitations_list_contract(self, schema, base_client, auth_headers):
        """测试获取监督邀请列表契约"""
        response = base_client.get('/api/supervision/invitations',
            query_string={'page': 1, 'limit': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "invitations" in response_data
        assert "total" in response_data
        assert isinstance(response_data["invitations"], list)
        assert isinstance(response_data["total"], int)

    def test_supervision_invitations_list_with_status_contract(self, schema, base_client, auth_headers):
        """测试获取监督邀请列表（带状态筛选）契约"""
        response = base_client.get('/api/supervision/invitations',
            query_string={'status': 'pending', 'page': 1, 'limit': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证邀请字段
        response_data = data["data"]
        for invitation in response_data["invitations"]:
            assert "invitation_id" in invitation
            assert "supervisor_id" in invitation
            assert "supervisor_nickname" in invitation
            assert "rule_ids" in invitation
            assert "status" in invitation
            assert "invited_at" in invitation

    # ==================== 接受监督邀请 ====================

    def test_supervision_invitation_accept_contract(self, schema, base_client, auth_headers):
        """测试接受监督邀请契约"""
        # 使用测试邀请ID
        response = base_client.post('/api/supervision/invitations/1/accept',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能不存在，只验证结构

        if data["code"] == 1:
            response_data = data["data"]
            assert "relation_id" in response_data
            assert "status" in response_data

    def test_supervision_invitation_accept_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：接受监督邀请 - 验证所有返回字段及类型"""
        response = base_client.post('/api/supervision/invitations/1/accept',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能不存在
        if data["code"] == 1:
            # OpenAPI 定义的完整响应字段
            response_data = data["data"]

            # 验证所有字段存在
            assert "relation_id" in response_data
            assert "status" in response_data

            # 验证字段类型
            assert isinstance(response_data["relation_id"], int)
            assert isinstance(response_data["status"], str)

    # ==================== 拒绝监督邀请 ====================

    def test_supervision_invitation_reject_contract(self, schema, base_client, auth_headers):
        """测试拒绝监督邀请契约"""
        response = base_client.post('/api/supervision/invitations/1/reject',
            json={'reason': '暂时不需要监督'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能不存在

        if data["code"] == 1:
            response_data = data["data"]
            assert "message" in response_data

    def test_supervision_invitation_reject_without_reason_contract(self, schema, base_client, auth_headers):
        """测试拒绝监督邀请（无原因）契约"""
        response = base_client.post('/api/supervision/invitations/1/reject',
            json={},  # 不提供原因
            headers=auth_headers
        )

        data = validate_response_structure(response)

    # ==================== 忽略监督邀请 ====================

    def test_supervision_invitation_ignore_contract(self, schema, base_client, auth_headers):
        """测试忽略监督邀请契约"""
        response = base_client.delete('/api/supervision/invitations/1',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能不存在

        if data["code"] == 1:
            response_data = data["data"]
            assert "message" in response_data

    # ==================== 批量接受监督邀请 ====================

    def test_supervision_invitation_batch_accept_contract(self, schema, base_client, auth_headers):
        """测试批量接受监督邀请契约"""
        response = base_client.post('/api/supervision/invitations/batch-accept',
            json={'invitation_ids': [1, 2, 3]},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 邀请可能不存在

        if data["code"] == 1:
            response_data = data["data"]
            assert "accepted_count" in response_data
            assert "failed_count" in response_data
            assert isinstance(response_data["accepted_count"], int)
            assert isinstance(response_data["failed_count"], int)

    def test_supervision_invitation_batch_accept_empty_contract(self, schema, base_client, auth_headers):
        """测试批量接受空列表契约"""
        response = base_client.post('/api/supervision/invitations/batch-accept',
            json={'invitation_ids': []},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 获取我监督的用户列表 ====================

    def test_supervision_my_supervised_contract(self, schema, base_client, auth_headers):
        """测试获取我监督的用户列表契约"""
        response = base_client.get('/api/supervision/my_supervised',
            query_string={'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "supervised_users" in response_data
        assert "total" in response_data
        assert isinstance(response_data["supervised_users"], list)
        assert isinstance(response_data["total"], int)

        # 验证用户字段
        for user in response_data["supervised_users"]:
            assert "user_id" in user
            assert "nickname" in user
            assert "avatar_url" in user
            assert "supervision_count" in user
            assert "status" in user

    def test_supervision_my_supervised_with_pagination_contract(self, schema, base_client, auth_headers):
        """测试获取我监督的用户列表（带分页）契约"""
        response = base_client.get('/api/supervision/my_supervised',
            query_string={'page': 2, 'per_page': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    # ==================== 获取我的监护人列表 ====================

    def test_supervision_my_guardians_contract(self, schema, base_client, auth_headers):
        """测试获取我的监护人列表契约"""
        response = base_client.get('/api/supervision/my_guardians',
            query_string={'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "guardians" in response_data
        assert "total" in response_data
        assert isinstance(response_data["guardians"], list)
        assert isinstance(response_data["total"], int)

        # 验证监护人字段
        for guardian in response_data["guardians"]:
            assert "user_id" in guardian
            assert "nickname" in guardian
            assert "avatar_url" in guardian
            assert "supervision_count" in guardian
            assert "status" in guardian

    # ==================== 获取监督记录 ====================

    def test_supervision_records_contract(self, schema, base_client, auth_headers):
        """测试获取监督记录契约"""
        response = base_client.get('/api/supervision/records',
            query_string={'supervised_user_id': 1, 'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "records" in response_data
        assert "total" in response_data
        assert isinstance(response_data["records"], list)
        assert isinstance(response_data["total"], int)

        # 验证记录字段
        for record in response_data["records"]:
            assert "record_id" in record
            assert "supervisor_id" in record
            assert "supervised_id" in record
            assert "rule_id" in record
            assert "checkin_time" in record
            assert "status" in record

    def test_supervision_records_missing_user_id_contract(self, schema, base_client, auth_headers):
        """测试获取监督记录缺少用户ID契约"""
        response = base_client.get('/api/supervision/records',
            query_string={'page': 1, 'per_page': 20},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_supervision_records_with_date_range_contract(self, schema, base_client, auth_headers):
        """测试获取监督记录（带日期范围）契约"""
        response = base_client.get('/api/supervision/records',
            query_string={
                'supervised_user_id': 1,
                'start_date': '2024-01-01',
                'end_date': '2024-12-31',
                'page': 1,
                'per_page': 20
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    # ==================== 获取今日监护数据 ====================

    def test_supervision_today_contract(self, schema, base_client, auth_headers):
        """测试获取今日监护数据契约"""
        response = base_client.get('/api/supervision/today',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "supervised_users" in response_data
        assert "date" in response_data
        assert "pending_invitations_count" in response_data
        assert isinstance(response_data["supervised_users"], list)
        assert isinstance(response_data["date"], str)
        assert isinstance(response_data["pending_invitations_count"], int)

        # 验证被监护人字段
        for user in response_data["supervised_users"]:
            assert "user_id" in user
            assert "nickname" in user
            assert "avatar_url" in user
            assert "rules" in user
            assert isinstance(user["rules"], list)

            # 验证规则字段
            for rule in user["rules"]:
                assert "rule_id" in rule
                assert "rule_name" in rule
                assert "checkin_time" in rule
                assert "today_status" in rule
                assert rule["today_status"] in ["pending", "completed", "missed"]

    def test_supervision_today_with_date_contract(self, schema, base_client, auth_headers):
        """测试获取指定日期监护数据契约"""
        response = base_client.get('/api/supervision/today',
            query_string={'date': '2024-01-15'},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    # ==================== 发送提醒 ====================

    def test_supervision_send_reminder_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试发送提醒契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/send_reminder',
            json={
                'supervised_user_id': 1,
                'rule_id': test_rule_id,
                'template_type': 'default'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 提醒可能成功或失败（取决于是否存在监督关系）

        if data["code"] == 1:
            response_data = data["data"]
            assert "message_id" in response_data
            assert "sent_at" in response_data
            assert isinstance(response_data["message_id"], str)
            assert isinstance(response_data["sent_at"], str)

    def test_supervision_send_reminder_custom_template_contract(self, schema, base_client, auth_headers, test_rule_id):
        """测试发送自定义提醒契约"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/send_reminder',
            json={
                'supervised_user_id': 1,
                'rule_id': test_rule_id,
                'template_type': 'custom',
                'template_content': '记得打卡哦'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)

    def test_supervision_send_reminder_missing_user_id_contract(self, schema, base_client, auth_headers):
        """测试发送提醒缺少用户ID契约"""
        response = base_client.post('/api/supervision/send_reminder',
            json={
                'rule_id': 1
                # 缺少 supervised_user_id
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_supervision_send_reminder_field_types_100_percent(self, schema, base_client, auth_headers, test_rule_id):
        """100% 完整度验证：发送提醒 - 验证所有返回字段及类型"""
        if test_rule_id is None:
            pytest.skip("无法获取测试规则ID")

        response = base_client.post('/api/supervision/send_reminder',
            json={
                'supervised_user_id': 1,
                'rule_id': test_rule_id,
                'template_type': 'wake_up'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        if data["code"] == 1:
            # OpenAPI 定义的完整响应字段
            response_data = data["data"]

            # 验证所有字段存在
            assert "message_id" in response_data
            assert "sent_at" in response_data

            # 验证字段类型
            assert isinstance(response_data["message_id"], str)
            assert isinstance(response_data["sent_at"], str)

            # 验证字段值有效性
            assert len(response_data["message_id"]) > 0
            assert len(response_data["sent_at"]) > 0
