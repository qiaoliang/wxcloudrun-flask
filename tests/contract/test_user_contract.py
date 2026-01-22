"""
用户模块 API 契约测试
测试用户信息、头像、密码、搜索、绑定、事件、病史等功能的 API 契约
"""
import pytest
import random
from tests.contract.helpers import load_schema, validate_response_structure, get_test_user_credentials


class TestUserContract:
    """用户模块契约测试"""

    @pytest.fixture
    def schema(self):
        """加载 user.yaml 规范"""
        return load_schema("user")

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

    # ==================== 用户信息 ====================

    def test_user_profile_contract(self, schema, base_client, auth_headers):
        """测试获取用户信息契约"""
        response = base_client.get('/api/user/profile',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        required_fields = ["user_id", "phone_number", "nickname", "role"]
        for field in required_fields:
            assert field in response_data, f"用户信息响应缺少字段: {field}"

    def test_user_profile_field_types_100_percent(self, schema, base_client, auth_headers):
        """100% 完整度验证：获取用户信息 - 验证所有返回字段及类型"""
        response = base_client.get('/api/user/profile',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # OpenAPI 定义的完整响应字段
        response_data = data["data"]

        # 验证所有字段存在
        assert "user_id" in response_data
        assert "phone_number" in response_data
        assert "nickname" in response_data
        assert "role" in response_data

        # 验证字段类型
        assert isinstance(response_data["user_id"], int)
        assert isinstance(response_data["phone_number"], str)
        assert isinstance(response_data["nickname"], str)
        assert isinstance(response_data["role"], int)

    def test_user_update_profile_contract(self, schema, base_client, auth_headers):
        """测试更新用户信息契约"""
        response = base_client.post('/api/user/profile',
            json={
                'nickname': f'更新昵称_{random.randint(1000, 9999)}',
                'name': '测试用户'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_update_profile_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试更新用户信息缺少参数契约"""
        response = base_client.post('/api/user/profile',
            json={},  # 缺少更新参数
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 可能成功（无更新）或失败
        assert "code" in data

    # ==================== 用户头像 ====================

    def test_user_upload_avatar_contract(self, schema, base_client, auth_headers):
        """测试上传用户头像契约"""
        # 使用模拟的图片数据
        response = base_client.post('/api/user/upload-avatar',
            data={'avatar': 'fake_image_data'},
            headers=auth_headers
        )

        # 验证响应结构（可能因无效图片数据失败）
        data = validate_response_structure(response)

    # ==================== 密码管理 ====================

    def test_user_change_password_contract(self, schema, base_client, auth_headers):
        """测试修改密码契约"""
        response = base_client.post('/api/user/change-password',
            json={
                'old_password': 'F1234567',
                'new_password': 'NewPassword123'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_change_password_wrong_old_password_contract(self, schema, base_client, auth_headers):
        """测试修改密码旧密码错误契约"""
        response = base_client.post('/api/user/change-password',
            json={
                'old_password': 'WrongPassword',
                'new_password': 'NewPassword123'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_user_change_password_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试修改密码缺少参数契约"""
        response = base_client.post('/api/user/change-password',
            json={},  # 缺少密码参数
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 用户搜索 ====================

    def test_user_search_contract(self, schema, base_client, auth_headers):
        """测试搜索用户契约"""
        response = base_client.get('/api/user/search',
            query_string={'keyword': '测试', 'page': 1, 'per_page': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "users" in response_data
        assert isinstance(response_data["users"], list)
        assert "total" in response_data
        assert isinstance(response_data["total"], int)

    def test_user_search_missing_keyword_contract(self, schema, base_client, auth_headers):
        """测试搜索用户缺少关键词契约"""
        response = base_client.get('/api/user/search',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 账号绑定 ====================

    def test_user_bind_phone_contract(self, schema, base_client, auth_headers):
        """测试绑定手机号契约"""
        response = base_client.post('/api/user/bind_phone',
            json={
                'phone': '13800138000',
                'code': '123456'  # 测试环境 mock 验证码
            },
            headers=auth_headers
        )

        # 验证响应结构（可能因手机号已存在失败）
        data = validate_response_structure(response)

    def test_user_bind_phone_missing_parameters_contract(self, schema, base_client, auth_headers):
        """测试绑定手机号缺少参数契约"""
        response = base_client.post('/api/user/bind_phone',
            json={},  # 缺少手机号和验证码
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    def test_user_bind_wechat_contract(self, schema, base_client, auth_headers):
        """测试绑定微信契约"""
        response = base_client.post('/api/user/bind_wechat',
            json={
                'code': 'mock_wechat_code'
            },
            headers=auth_headers
        )

        # 验证响应结构（可能因 mock 限制失败）
        data = validate_response_structure(response)

    def test_user_bind_wechat_missing_code_contract(self, schema, base_client, auth_headers):
        """测试绑定微信缺少 code 契约"""
        response = base_client.post('/api/user/bind_wechat',
            json={},  # 缺少 code
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 社区验证 ====================

    def test_user_community_verify_contract(self, schema, base_client, auth_headers):
        """测试验证用户社区成员身份契约"""
        response = base_client.post('/api/user/community/verify',
            json={
                'community_id': 1  # 默认社区ID
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "is_member" in response_data
        assert "user_role" in response_data

    def test_user_community_verify_missing_community_id_contract(self, schema, base_client, auth_headers):
        """测试社区验证缺少社区ID契约"""
        response = base_client.post('/api/user/community/verify',
            json={},  # 缺少 community_id
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 0

    # ==================== 用户事件 ====================

    def test_user_active_events_contract(self, schema, base_client, auth_headers):
        """测试获取用户进行中的事件契约"""
        response = base_client.get('/api/user/my-active-event',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        # 可能没有进行中的事件
        assert "code" in data

    # ==================== 事件消息 ====================

    def test_user_event_messages_contract(self, schema, base_client, auth_headers):
        """测试添加事件消息契约"""
        # 使用模拟事件ID
        response = base_client.post('/api/user/events/999/messages',
            json={
                'message_type': 1,
                'content': '测试消息内容'
            },
            headers=auth_headers
        )

        # 验证响应结构（事件可能不存在）
        data = validate_response_structure(response)

    def test_user_event_history_contract(self, schema, base_client, auth_headers):
        """测试获取事件历史契约"""
        response = base_client.get('/api/user/events/999/history',
            headers=auth_headers
        )

        # 验证响应结构（事件可能不存在）
        data = validate_response_structure(response)

    # ==================== 病史管理 ====================

    def test_user_medical_history_list_contract(self, schema, base_client, auth_headers):
        """测试获取用户病史列表契约"""
        # 使用当前用户ID
        response = base_client.get('/api/user/1/medical-history',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "medical_history" in response_data
        assert isinstance(response_data["medical_history"], list)

    def test_user_medical_history_add_contract(self, schema, base_client, auth_headers):
        """测试添加病史记录契约"""
        response = base_client.post('/api/user/medical-history',
            json={
                'user_id': 1,
                'condition_name': '测试疾病',
                'description': '测试描述',
                'diagnosis_date': '2024-01-01'
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_medical_history_update_contract(self, schema, base_client, auth_headers):
        """测试更新病史记录契约"""
        # 先添加一条病史
        add_response = base_client.post('/api/user/medical-history',
            json={
                'user_id': 1,
                'condition_name': '测试疾病_更新',
                'description': '测试描述'
            },
            headers=auth_headers
        )
        add_data = validate_response_structure(add_response)

        # 如果添加成功，尝试更新
        if add_data["code"] == 1 and "history_id" in add_data.get("data", {}):
            history_id = add_data["data"]["history_id"]
            response = base_client.put(f'/api/user/medical-history/{history_id}',
                json={
                    'condition_name': '更新的疾病名称',
                    'description': '更新的描述'
                },
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

    def test_user_medical_history_delete_contract(self, schema, base_client, auth_headers):
        """测试删除病史记录契约"""
        # 先添加一条病史
        add_response = base_client.post('/api/user/medical-history',
            json={
                'user_id': 1,
                'condition_name': '测试疾病_删除',
                'description': '测试描述'
            },
            headers=auth_headers
        )
        add_data = validate_response_structure(add_response)

        # 如果添加成功，尝试删除
        if add_data["code"] == 1 and "history_id" in add_data.get("data", {}):
            history_id = add_data["data"]["history_id"]
            response = base_client.delete(f'/api/user/medical-history/{history_id}',
                headers=auth_headers
            )

            data = validate_response_structure(response)
            assert data["code"] == 1

    def test_user_medical_history_common_conditions_contract(self, schema, base_client, auth_headers):
        """测试获取常见疾病列表契约"""
        response = base_client.get('/api/user/medical-history/common-conditions',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "conditions" in response_data
        assert isinstance(response_data["conditions"], list)

    # ==================== 浏览记录 ====================

    def test_user_log_profile_view_contract(self, schema, base_client, auth_headers):
        """测试记录查看成员信息契约"""
        response = base_client.post('/api/user/log-profile-view',
            json={
                'target_user_id': 1
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_log_view_guardian_contract(self, schema, base_client, auth_headers):
        """测试记录查看监护人信息契约"""
        response = base_client.post('/api/user/log-view-guardian',
            json={
                'target_user_id': 1
            },
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

    def test_user_profile_view_logs_contract(self, schema, base_client, auth_headers):
        """测试获取查看记录契约"""
        response = base_client.get('/api/user/profile-view-logs',
            query_string={'page': 1, 'per_page': 10},
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "logs" in response_data
        assert isinstance(response_data["logs"], list)

    # ==================== 管理的社区 ====================

    def test_user_managed_communities_contract(self, schema, base_client, auth_headers):
        """测试获取用户管理的社区列表契约"""
        response = base_client.get('/api/user/managed-communities',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        # 验证响应字段
        response_data = data["data"]
        assert "communities" in response_data
        assert isinstance(response_data["communities"], list)

    def test_user_managed_communities_full_response_fields(self, schema, base_client, auth_headers):
        """100% 完整度验证：获取用户管理的社区列表 - 验证超级管理员获取两个默认社区完整信息"""
        response = base_client.get('/api/user/managed-communities',
            headers=auth_headers
        )

        data = validate_response_structure(response)
        assert data["code"] == 1

        response_data = data["data"]
        assert "communities" in response_data
        assert "count" in response_data
        assert isinstance(response_data["communities"], list)

        # 验证有两个社区
        communities = response_data["communities"]
        assert len(communities) >= 2, f"期望至少2个社区，实际获取{len(communities)}个"

        # 查找两个默认社区
        community_names = [c.get('name') for c in communities]
        assert '安卡大家庭' in community_names, "期望包含安卡大家庭"
        assert '黑屋社区' in community_names, "期望包含黑屋社区"

        # 验证安卡大家庭的完整信息
        ankaji = next((c for c in communities if c.get('name') == '安卡大家庭'), None)
        assert ankaji is not None
        assert ankaji["community_id"] > 0
        assert ankaji["name"] == "安卡大家庭"
        assert "系统默认社区" in ankaji["description"]
        assert ankaji["location"] == "北京市朝阳区柳芳南里29号"
        assert ankaji["location_lat"] == 39.901213
        assert ankaji["location_lon"] == 116.527067
        assert ankaji["province"] == "北京市"
        assert ankaji["city"] == "北京市"
        assert ankaji["district"] == "朝阳区"
        assert ankaji["street"] == "柳芳南里"
        assert ankaji["status"] == 1
        assert ankaji["is_default"] == True
        assert ankaji["is_blackhouse"] == False
        assert ankaji["creator_id"] is not None
        assert ankaji["manager_id"] is not None
        assert ankaji["created_at"] is not None
        assert ankaji["updated_at"] is not None

        # 验证黑屋社区的完整信息
        blackhouse = next((c for c in communities if c.get('name') == '黑屋社区'), None)
        assert blackhouse is not None
        assert blackhouse["community_id"] > 0
        assert blackhouse["name"] == "黑屋社区"
        assert "特殊管理社区" in blackhouse["description"]
        assert blackhouse["location"] == "北京市海淀区中关村大街1号"
        assert blackhouse["location_lat"] == 39.956073
        assert blackhouse["location_lon"] == 116.307079
        assert blackhouse["province"] == "北京市"
        assert blackhouse["city"] == "北京市"
        assert blackhouse["district"] == "海淀区"
        assert blackhouse["street"] == "中关村大街"
        assert blackhouse["status"] == 1
        assert blackhouse["is_default"] == False
        assert blackhouse["is_blackhouse"] == True
        assert blackhouse["creator_id"] is not None
        assert blackhouse["manager_id"] is not None
        assert blackhouse["created_at"] is not None
        assert blackhouse["updated_at"] is not None

        # 验证 count 字段
        assert response_data["count"] >= 2
