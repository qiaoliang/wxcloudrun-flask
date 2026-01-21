"""
手机号登录API快照对比集成测试
专注于数据一致性验证
"""

import pytest
import json
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community
from error_code import INVALID_CAPTCHA
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestAuthLoginPhoneSnapshotFinal(IntegrationTestBase):
    """手机号登录API快照对比测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建标准测试用户（兼容现有测试）
            cls.test_user = cls.create_standard_test_user(role=1)
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='测试社区',
                creator=cls.test_user
            )
            
            # 建立用户-社区关系
            cls.test_user.community_id = cls.test_community.community_id
            cls.db.session.commit()

            # 保存预期值用于快照对比
            cls.expected_values = {
                'user_id': cls.test_user.user_id,
                'wechat_openid': cls.test_user.wechat_openid,
                'phone_number': cls.test_user.phone_number,
                'nickname': cls.test_user.nickname,
                'name': cls.test_user.name,
                'avatar_url': cls.test_user.avatar_url,
                'role': 1,  # role=1 对应整数类型
                'role_name': '普通用户',  # role_name=1 对应的角色名（字符串）
                'community_id': cls.test_community.community_id,
                'community_name': '测试社区',
                'login_type': 'existing_user'
            }

            print(f"✅ 创建测试用户: user_id={cls.test_user.user_id}")
            print(f"✅ phone_number: {cls.test_user.phone_number}")
            print(f"✅ phone_hash: {cls.test_user.phone_hash[:20]}...")
            print(f"✅ community_id: {cls.test_user.community_id}")
            print(f"✅ 预期快照字段数量: {len(cls.expected_values)}")

    def test_login_phone_snapshot_data_integrity(self):
        """测试登录API返回数据的完整性和一致性"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,  # 使用测试中实际创建的用户手机号
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,  # 测试验证码
            'password': TEST_CONSTANTS.DEFAULT_PASSWORD
        }

        # 发送登录请求
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')

        print(f"📱 登录响应状态码: {response.status_code}")

        # 使用快照验证器
        validator = self.create_snapshot_validator(self.expected_values)
        data = validator(response)

        # 验证动态字段存在
        response_data = data['data']
        dynamic_fields = ['token', 'refresh_token']
        for field in dynamic_fields:
            assert field in response_data, f"❌ 缺少动态字段: {field}"

        # 验证数据类型正确性
        assert isinstance(response_data['user_id'], int)
        assert isinstance(response_data['community_id'], int)
        assert isinstance(response_data['role'], int)  # role 是整数类型
        assert isinstance(response_data['role_name'], str)  # role_name 是字符串类型
        assert isinstance(response_data['login_type'], str)
        assert isinstance(response_data['token'], str)
        assert isinstance(response_data['refresh_token'], str)

        # 验证token格式
        assert len(response_data['token']) > 20  # JWT token应该有一定长度
        assert len(response_data['refresh_token']) > 10  # Refresh token应该有一定长度

        print(f"✅ Token格式验证通过")

        # 验证关键业务逻辑
        assert response_data['user_id'] == self.test_user.user_id
        assert response_data['role'] == 1  # role 是整数类型
        assert response_data['role_name'] == '普通用户'  # role_name 是字符串类型
        assert response_data['login_type'] == 'existing_user'
        assert response_data['community_name'] == '测试社区'

        print(f"✅ 关键业务逻辑验证通过")

    def test_login_phone_error_cases_data_consistency(self):
        """测试登录API错误情况的数据一致性"""
        client = self.get_test_client()

        # 测试用例：各种错误情况
        # 注意：login_phone 已更新为通用登录接口，支持多种场景
        error_cases = [
            {
                'name': '错误验证码',
                'data': {'phone': self.test_user.phone_number, 'code': TEST_CONSTANTS.INVALID_VERIFICATION_CODE, 'password': TEST_CONSTANTS.DEFAULT_PASSWORD},
                'expected_msg_key': '验证码错误'
            },
            {
                'name': '错误密码',
                'data': {'phone': self.test_user.phone_number, 'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE, 'password': 'wrong_test_password'},
                'expected_msg_key': '密码不正确'
            },
            {
                'name': '缺少认证方式',
                'data': {'phone': self.test_user.phone_number},  # 缺少 code 和 password
                'expected_msg_key': '请提供验证码或密码进行登录'
            },
            {
                'name': '用户不存在',
                'data': {'phone': '19900007997', 'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE, 'password': TEST_CONSTANTS.DEFAULT_PASSWORD},
                'expected_msg_key': '账号不存在，请先注册'
            }
        ]

        for case in error_cases:
            print(f"\n🧪 测试错误情况: {case['name']}")

            response = client.post('/api/auth/login_phone',
                                 data=json.dumps(case['data']),
                                 content_type='application/json')

            # 使用标准错误断言
            data = self.assert_api_error(response, expected_msg_pattern=case['expected_msg_key'])

            # 验证错误情况下的数据一致性
            error_data = data['data']
            if 'code' in error_data:
                # 某些错误情况会返回特定的错误代码
                assert isinstance(error_data['code'], str)

            print(f"✅ {case['name']} 错误响应验证通过: {data['msg']}")

    def test_login_phone_performance_consistency(self):
        """测试登录API的性能一致性"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'password': TEST_CONSTANTS.DEFAULT_PASSWORD
        }

        # 执行多次登录，验证响应一致性
        responses = []
        for i in range(3):
            response = client.post('/api/auth/login_phone',
                                 data=json.dumps(login_data),
                                 content_type='application/json')

            data = self.assert_api_success(response)
            responses.append(data['data'])

        # 验证关键字段在多次请求中保持一致
        base_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            for key in self.expected_values.keys():
                assert response[key] == base_response[key], f"字段 {key} 在第 {i+1} 次请求中不一致"

        print(f"✅ 性能一致性测试通过：{len(responses)} 次请求响应数据一致")

        # 验证token的唯一性（每次登录应该生成不同的token）
        tokens = [resp['token'] for resp in responses]
        refresh_tokens = [resp['refresh_token'] for resp in responses]

        assert len(set(tokens)) == len(tokens), "每次登录应该生成不同的token"
        assert len(set(refresh_tokens)) == len(refresh_tokens), "每次登录应该生成不同的refresh_token"

        print(f"✅ Token唯一性验证通过：{len(tokens)} 个token均唯一")

    def test_login_phone_data_type_consistency(self):
        """测试登录API返回数据类型的一致性"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'password': TEST_CONSTANTS.DEFAULT_PASSWORD
        }

        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')

        data = self.assert_api_success(response, expected_data_keys=[
            'user_id', 'wechat_openid', 'phone_number', 'nickname', 'name',
            'avatar_url', 'role', 'role_name', 'community_id', 'community_name', 'login_type',
            'token', 'refresh_token'
        ])
        
        response_data = data['data']

        # 定义预期的数据类型
        expected_types = {
            'user_id': int,
            'wechat_openid': str,
            'phone_number': str,
            'nickname': str,
            'name': str,
            'avatar_url': (type(None), str),  # 允许None或字符串
            'role': int,  # role 是整数类型（1=普通用户, 2=社区专员, 3=社区主管, 4=超级系统管理员）
            'role_name': str,  # role_name 是字符串类型
            'community_id': int,
            'community_name': str,
            'login_type': str,
            'token': str,
            'refresh_token': str
        }

        type_mismatches = []
        for field, expected_type in expected_types.items():
            if not isinstance(response_data[field], expected_type):
                type_mismatches.append(f"❌ 字段 {field} 类型错误: 期望 {expected_type}, 实际 {type(response_data[field])}")

        assert not type_mismatches, f"数据类型一致性验证失败: {type_mismatches}"
        print(f"✅ 数据类型一致性验证通过：{len(expected_types)} 个字段类型正确")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
