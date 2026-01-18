"""
用户注册API集成测试 - 验证 community_id 返回

此测试专门用于验证用户注册API是否正确返回 community_id 和 community_name，
帮助诊断前端测试失败的根本原因。
"""

import pytest
import json
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

# 不直接导入 flask_models 避免循环导入
# 从 .conftest 导入测试基类
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS
# 导入测试数据生成器
from test_data_generator import generate_unique_phone_number


class TestUserRegistrationCommunityId(IntegrationTestBase):
    """用户注册API community_id 返回验证测试"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        # 不预先创建用户或社区，测试中使用默认的 DEFAULT_COMMUNITY
        # 这样可以验证新用户是否正确分配到默认社区

    def test_register_phone_returns_community_id(self):
        """
        测试：用户注册API应该返回 community_id 和 community_name

        这是核心测试 - 直接验证API返回值，排除前端因素
        """
        client = self.get_test_client()

        # 生成唯一的手机号（避免冲突）
        unique_suffix = __class__.__name__ + '_test'
        test_phone = generate_unique_phone_number(unique_suffix)

        print(f"\n📱 测试手机号: {test_phone}")
        print(f"📝 使用测试验证码: {TEST_CONSTANTS.TEST_VERIFICATION_CODE}")

        # 发送注册请求
        register_data = {
            'phone': test_phone,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'nickname': '测试用户_' + unique_suffix[:10]
        }

        response = client.post('/api/auth/register_phone',
                             data=json.dumps(register_data),
                             content_type='application/json')

        print(f"📊 注册响应状态码: {response.status_code}")
        print(f"📊 响应内容: {response.get_json()}")

        # 验证请求成功
        assert response.status_code == 200, f"注册失败，状态码: {response.status_code}"

        data = response.get_json()
        assert data['code'] == 1, f"注册返回code错误: {data.get('msg')}"

        response_data = data['data']

        print(f"\n✅ 注册成功，开始验证返回字段...")

        # === 验证关键字段存在 ===
        required_fields = [
            'user_id', 'token', 'refresh_token', 'phone_number',
            'nickname', 'avatar_url', 'role', 'role_name',
            'community_id', 'community_name',  # 重点验证
            'login_type'
        ]

        for field in required_fields:
            assert field in response_data, f"❌ 缺少必需字段: {field}"
            print(f"  ✓ 字段存在: {field} = {response_data[field]}")

        # === 验证 community_id 不为空 ===
        assert response_data['community_id'] is not None, "❌ community_id 为 None"
        assert response_data['community_id'] > 0, f"❌ community_id 值无效: {response_data['community_id']}"

        print(f"\n✅ community_id 验证通过: {response_data['community_id']}")

        # === 验证 community_name 不为空 ===
        assert response_data['community_name'] is not None, "❌ community_name 为 None"
        assert len(response_data['community_name']) > 0, f"❌ community_name 值无效: {response_data['community_name']}"

        print(f"✅ community_name 验证通过: {response_data['community_name']}")

        # === 验证 community_name 与 DEFAULT_COMMUNITY_NAME 一致 ===
        from const_default import DEFAULT_COMMUNITY_NAME
        assert response_data['community_name'] == DEFAULT_COMMUNITY_NAME, \
            f"❌ community_name 不匹配: 期望 '{DEFAULT_COMMUNITY_NAME}', 实际 '{response_data['community_name']}'"

        print(f"✅ 社区名称验证通过: {response_data['community_name']}")

        # === 验证数据类型 ===
        assert isinstance(response_data['community_id'], int), \
            f"❌ community_id 类型错误: {type(response_data['community_id'])}"
        assert isinstance(response_data['community_name'], str), \
            f"❌ community_name 类型错误: {type(response_data['community_name'])}"

        print(f"✅ 数据类型验证通过")

        # === 验证数据库中的实际数据 ===
        with self.app.app_context():
            # 在app_context中导入避免循环导入
            from database.flask_models import User

            # 从数据库查询刚创建的用户
            created_user = self.db.session.query(User).filter(
                User.phone_hash.like(f"%{test_phone.replace('+', '')}%")
            ).first()

            assert created_user is not None, "❌ 数据库中未找到创建的用户"
            assert created_user.community_id == response_data['community_id'], \
                f"❌ 数据库 community_id 与API返回不匹配: DB={created_user.community_id}, API={response_data['community_id']}"

            # 验证 community 关联是否正确加载
            if created_user.community:
                print(f"✅ community 关联正确加载: {created_user.community.name}")
            else:
                print(f"⚠️  community 关联未加载（但 community_id 值正确）")

        print(f"\n✅✅✅ 所有验证通过！注册API正确返回 community_id")

    def test_register_phone_login_type_field(self):
        """
        测试：注册API应该返回 login_type='new_user'
        """
        client = self.get_test_client()

        unique_suffix = __class__.__name__ + '_login_type'
        test_phone = generate_unique_phone_number(unique_suffix)

        register_data = {
            'phone': test_phone,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'nickname': '测试用户'
        }

        response = client.post('/api/auth/register_phone',
                             data=json.dumps(register_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        response_data = data['data']

        assert 'login_type' in response_data, "❌ 缺少 login_type 字段"
        assert response_data['login_type'] == 'new_user', \
            f"❌ login_type 值错误: 期望 'new_user', 实际 '{response_data['login_type']}'"

        print(f"✅ login_type 验证通过: {response_data['login_type']}")

    def test_register_multiple_users_community_consistency(self):
        """
        测试：多次注册的用户都应该有相同的默认社区
        """
        client = self.get_test_client()

        from const_default import DEFAULT_COMMUNITY_ID, DEFAULT_COMMUNITY_NAME

        # 注册3个用户
        registered_users = []
        for i in range(3):
            unique_suffix = f"{__class__.__name__}_multi_{i}"
            test_phone = generate_unique_phone_number(unique_suffix)

            register_data = {
                'phone': test_phone,
                'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                'nickname': f'测试用户{i}'
            }

            response = client.post('/api/auth/register_phone',
                                 data=json.dumps(register_data),
                                 content_type='application/json')

            assert response.status_code == 200
            data = response.get_json()
            response_data = data['data']

            # 验证每个用户都有相同的默认社区
            assert response_data['community_id'] == DEFAULT_COMMUNITY_ID, \
                f"❌ 用户{i+1}的community_id不匹配: 期望 {DEFAULT_COMMUNITY_ID}, 实际 {response_data['community_id']}"
            assert response_data['community_name'] == DEFAULT_COMMUNITY_NAME, \
                f"❌ 用户{i+1}的community_name不匹配: 期望 '{DEFAULT_COMMUNITY_NAME}', 实际 '{response_data['community_name']}'"

            registered_users.append({
                'phone': test_phone,
                'user_id': response_data['user_id'],
                'community_id': response_data['community_id'],
                'community_name': response_data['community_name']
            })

            print(f"  ✓ 用户{i+1}: user_id={response_data['user_id']}, community_id={response_data['community_id']}")

        print(f"\n✅ 所有用户都正确分配到默认社区: {DEFAULT_COMMUNITY_NAME} (ID={DEFAULT_COMMUNITY_ID})")

    def test_register_with_password(self):
        """
        测试：带密码注册的用户也应该有 community_id
        """
        client = self.get_test_client()

        unique_suffix = __class__.__name__ + '_with_pwd'
        test_phone = generate_unique_phone_number(unique_suffix)

        register_data = {
            'phone': test_phone,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'nickname': '带密码用户',
            'password': 'TestPassword123'  # 8位以上，包含字母和数字
        }

        response = client.post('/api/auth/register_phone',
                             data=json.dumps(register_data),
                             content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        response_data = data['data']

        # 验证 community_id
        assert response_data['community_id'] is not None, "❌ 带密码注册的用户缺少 community_id"
        assert response_data['community_name'] is not None, "❌ 带密码注册的用户缺少 community_name"

        print(f"✅ 带密码注册的用户 community_id 正确: {response_data['community_id']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
