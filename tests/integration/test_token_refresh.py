"""
Token失效重新登录集成测试
测试access token过期后使用refresh token重新登录的完整流程
"""

import pytest
import json
import sys
import os
import jwt
import datetime
from unittest.mock import patch

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestTokenRefreshIntegration(IntegrationTestBase):
    """Token失效重新登录集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建标准测试用户
            cls.test_user = cls.create_standard_test_user(role=1)
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='Token刷新测试社区',
                creator=cls.test_user
            )
            
            # 建立用户-社区关系
            cls.test_user.community_id = cls.test_community.community_id
            cls.db.session.commit()

            print(f"✅ 创建测试用户: user_id={cls.test_user.user_id}")
            print(f"✅ phone_number: {cls.test_user.phone_number}")

    def test_login_and_get_tokens(self):
        """测试登录并获取access token和refresh token"""
        client = self.get_test_client()

        login_data = {
            'phone': self.test_user.phone_number,
            'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
            'password': TEST_CONSTANTS.DEFAULT_PASSWORD
        }

        # 发送登录请求
        response = client.post('/api/auth/login_phone',
                             data=json.dumps(login_data),
                             content_type='application/json')

        data = self.assert_api_success(response, expected_data_keys=[
            'token', 'refresh_token', 'user_id', 'phone_number', 'nickname'
        ])

        response_data = data['data']

        # 验证token格式
        assert isinstance(response_data['token'], str)
        assert len(response_data['token']) > 20
        assert isinstance(response_data['refresh_token'], str)
        assert len(response_data['refresh_token']) > 10

        # 验证用户信息
        assert response_data['user_id'] == self.test_user.user_id
        assert response_data['phone_number'] == self.test_user.phone_number

        print(f"✅ 登录成功，获取到token和refresh_token")

    def test_refresh_token_success(self):
        """测试使用有效的refresh token成功刷新access token"""
        client = self.get_test_client()

        # 先登录获取token
        login_response = client.post('/api/auth/login_phone',
                                    data=json.dumps({
                                        'phone': self.test_user.phone_number,
                                        'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                                        'password': TEST_CONSTANTS.DEFAULT_PASSWORD
                                    }),
                                    content_type='application/json')

        login_data = self.assert_api_success(login_response)
        old_token = login_data['data']['token']
        old_refresh_token = login_data['data']['refresh_token']

        print(f"✅ 原始token: {old_token[:50]}...")
        print(f"✅ 原始refresh_token: {old_refresh_token[:20]}...")

        # 使用refresh token刷新
        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': old_refresh_token
                                      }),
                                      content_type='application/json')

        refresh_data = self.assert_api_success(refresh_response, expected_data_keys=[
            'token', 'refresh_token', 'expires_in'
        ])

        new_token = refresh_data['data']['token']
        new_refresh_token = refresh_data['data']['refresh_token']
        expires_in = refresh_data['data']['expires_in']

        # 验证新token
        assert isinstance(new_token, str)
        assert len(new_token) > 20
        assert isinstance(new_refresh_token, str)
        assert len(new_refresh_token) > 10
        assert expires_in == 7200  # 2小时 = 7200秒

        # 验证新token与旧token不同
        assert new_token != old_token, "新token应该与旧token不同"
        assert new_refresh_token != old_refresh_token, "新refresh_token应该与旧refresh_token不同"

        print(f"✅ Token刷新成功")
        print(f"✅ 新token: {new_token[:50]}...")
        print(f"✅ 新refresh_token: {new_refresh_token[:20]}...")

        # 验证新token可以正常使用
        test_response = client.get('/api/user/profile',
                                  headers={'Authorization': f'Bearer {new_token}'})

        # 验证新token有效
        assert test_response.status_code == 200
        profile_data = json.loads(test_response.data)
        assert profile_data['code'] == 1

        print(f"✅ 新token验证通过，可以正常使用")

    def test_refresh_token_invalid(self):
        """测试使用无效的refresh token刷新失败"""
        client = self.get_test_client()

        # 使用不存在的refresh token
        invalid_refresh_token = "invalid_refresh_token_12345678901234567890"

        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': invalid_refresh_token
                                      }),
                                      content_type='application/json')

        # 验证错误响应
        data = self.assert_api_error(refresh_response, expected_msg_pattern='无效的refresh_token')

        print(f"✅ 无效refresh_token验证通过: {data['msg']}")

    def test_refresh_token_missing(self):
        """测试缺少refresh_token参数的情况"""
        client = self.get_test_client()

        # 提供请求体但不包含refresh_token参数
        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({'other_param': 'value'}),
                                      content_type='application/json')

        # 验证错误响应
        data = self.assert_api_error(refresh_response, expected_msg_pattern='缺少refresh_token参数')

        print(f"✅ 缺少refresh_token参数验证通过: {data['msg']}")

    def test_refresh_token_expired(self):
        """测试使用过期的refresh token刷新失败"""
        client = self.get_test_client()

        # 先登录获取有效的 refresh token
        login_response = client.post('/api/auth/login_phone',
                                    data=json.dumps({
                                        'phone': self.test_user.phone_number,
                                        'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                                        'password': TEST_CONSTANTS.DEFAULT_PASSWORD
                                    }),
                                    content_type='application/json')

        login_data = self.assert_api_success(login_response)
        valid_refresh_token = login_data['data']['refresh_token']

        print(f"✅ 获取有效的refresh_token: {valid_refresh_token[:20]}...")

        # 重新查询用户对象（因为测试基类会回滚事务）
        with self.app.app_context():
            from database.flask_models import User
            user = self.db.session.get(User, self.test_user.user_id)
            # 设置为过期（1天前）
            user.refresh_token = valid_refresh_token
            user.refresh_token_expire = datetime.datetime.now() - datetime.timedelta(days=1)
            self.db.session.commit()

        # 尝试使用过期的refresh token刷新
        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': valid_refresh_token
                                      }),
                                      content_type='application/json')

        # 验证错误响应
        data = self.assert_api_error(refresh_response, expected_msg_pattern='refresh_token已过期')

        print(f"✅ 过期refresh_token验证通过: {data['msg']}")

    def test_access_token_expired_refresh_success(self):
        """测试access token过期后使用refresh token重新获取access token"""
        client = self.get_test_client()

        # 先登录获取token
        login_response = client.post('/api/auth/login_phone',
                                    data=json.dumps({
                                        'phone': self.test_user.phone_number,
                                        'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                                        'password': TEST_CONSTANTS.DEFAULT_PASSWORD
                                    }),
                                    content_type='application/json')

        login_data = self.assert_api_success(login_response)
        refresh_token = login_data['data']['refresh_token']

        print(f"✅ 获取refresh_token: {refresh_token[:20]}...")

        # 模拟access token过期（通过创建一个已过期的token）
        with self.app.app_context():
            # 创建一个已过期的JWT token
            expired_payload = {
                'openid': self.test_user.wechat_openid,
                'user_id': self.test_user.user_id,
                'exp': datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=1),  # 1小时前过期
                'jti': 'expired_test_token'
            }
            
            from config import get_config
            token_secret = get_config().token_secret
            expired_token = jwt.encode(expired_payload, token_secret, algorithm='HS256')

        print(f"✅ 创建过期token: {expired_token[:50]}...")

        # 尝试使用过期的access token访问受保护的API
        test_response = client.get('/api/user/profile',
                                  headers={'Authorization': f'Bearer {expired_token}'})

        # 验证token过期错误
        assert test_response.status_code == 200
        profile_data = json.loads(test_response.data)
        assert profile_data['code'] == 0
        assert '过期' in profile_data['msg']

        print(f"✅ 过期token验证失败: {profile_data['msg']}")

        # 使用refresh token获取新的access token
        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': refresh_token
                                      }),
                                      content_type='application/json')

        refresh_data = self.assert_api_success(refresh_response)
        new_token = refresh_data['data']['token']

        print(f"✅ 使用refresh_token获取新token: {new_token[:50]}...")

        # 使用新token访问受保护的API
        new_test_response = client.get('/api/user/profile',
                                      headers={'Authorization': f'Bearer {new_token}'})

        # 验证新token有效
        assert new_test_response.status_code == 200
        new_profile_data = json.loads(new_test_response.data)
        assert new_profile_data['code'] == 1

        print(f"✅ 新token验证通过，成功重新登录")

    def test_refresh_token_mismatch(self):
        """测试refresh token与数据库中存储的不匹配"""
        client = self.get_test_client()

        # 先登录获取token
        login_response = client.post('/api/auth/login_phone',
                                    data=json.dumps({
                                        'phone': self.test_user.phone_number,
                                        'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                                        'password': TEST_CONSTANTS.DEFAULT_PASSWORD
                                    }),
                                    content_type='application/json')

        login_data = self.assert_api_success(login_response)

        # 使用与数据库不匹配的refresh token
        mismatched_refresh_token = "mismatched_refresh_token_12345678901234567890"

        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': mismatched_refresh_token
                                      }),
                                      content_type='application/json')

        # 验证错误响应
        data = self.assert_api_error(refresh_response, expected_msg_pattern='无效的refresh_token')

        print(f"✅ refresh_token不匹配验证通过: {data['msg']}")

    def test_multiple_token_refreshes(self):
        """测试多次刷新token，每次都生成新的token"""
        client = self.get_test_client()

        # 先登录获取初始token
        login_response = client.post('/api/auth/login_phone',
                                    data=json.dumps({
                                        'phone': self.test_user.phone_number,
                                        'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                                        'password': TEST_CONSTANTS.DEFAULT_PASSWORD
                                    }),
                                    content_type='application/json')

        login_data = self.assert_api_success(login_response)
        current_refresh_token = login_data['data']['refresh_token']
        tokens = [login_data['data']['token']]
        refresh_tokens = [current_refresh_token]

        print(f"✅ 初始token: {tokens[0][:50]}...")

        # 执行3次刷新
        for i in range(3):
            refresh_response = client.post('/api/auth/refresh_token',
                                          data=json.dumps({
                                              'refresh_token': current_refresh_token
                                          }),
                                          content_type='application/json')

            refresh_data = self.assert_api_success(refresh_response)
            new_token = refresh_data['data']['token']
            new_refresh_token = refresh_data['data']['refresh_token']

            tokens.append(new_token)
            refresh_tokens.append(new_refresh_token)
            current_refresh_token = new_refresh_token

            print(f"✅ 第{i+1}次刷新 - 新token: {new_token[:50]}...")

        # 验证所有token都是唯一的
        assert len(set(tokens)) == len(tokens), "所有token应该是唯一的"
        assert len(set(refresh_tokens)) == len(refresh_tokens), "所有refresh_token应该是唯一的"

        print(f"✅ 多次刷新验证通过，生成了{len(tokens)}个唯一token")

    def test_refresh_token_after_logout(self):
        """测试登出后refresh token失效"""
        client = self.get_test_client()

        # 创建一个有 openid 的用户（模拟微信登录用户）
        token = None
        refresh_token = None

        with self.app.app_context():
            wechat_user = self.create_test_user(
                wechat_openid='test_wechat_openid_for_logout',
                phone_number='13900009999',
                role=1
            )
            wechat_user.community_id = self.test_community.community_id
            self.db.session.commit()

            # 模拟微信登录（直接创建 token）
            from app.shared.utils.auth import generate_jwt_token, generate_refresh_token
            token, _ = generate_jwt_token(wechat_user, expires_hours=2)
            refresh_token = generate_refresh_token(wechat_user, expires_days=7)
            self.db.session.commit()

        print(f"✅ 创建微信用户并获取token和refresh_token")

        # 登出（注意：logout路由没有/auth前缀）
        logout_response = client.post('/api/logout',
                                     headers={'Authorization': f'Bearer {token}'})

        logout_data = self.assert_api_success(logout_response)
        print(f"✅ 登出成功: {logout_data['msg']}")

        # 尝试使用refresh token刷新
        refresh_response = client.post('/api/auth/refresh_token',
                                      data=json.dumps({
                                          'refresh_token': refresh_token
                                      }),
                                      content_type='application/json')

        # 验证refresh token失效
        data = self.assert_api_error(refresh_response, expected_msg_pattern='无效的refresh_token')

        print(f"✅ 登出后refresh_token失效验证通过: {data['msg']}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])