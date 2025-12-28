"""
用户修改密码集成测试
Happy path: 成功修改用户密码
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestUserChangePassword(IntegrationTestBase):
    """用户修改密码集成测试"""

    def test_change_password_success(self):
        """测试成功修改用户密码"""
        # 创建测试用户（在应用上下文中）
        old_password = TEST_CONSTANTS.DEFAULT_PASSWORD
        new_password = 'NewPassword123'

        phone_number = None
        with self.app.app_context():
            user = self.create_standard_test_user(
                role=1,
                password=old_password,
                test_context='change_password'
            )
            phone_number = user.phone_number  # 在上下文中获取phone_number
            user_id = user.user_id  # 保存user_id用于后续验证
            # 提交到数据库，确保 test_client 可以访问
            self.db.session.commit()
        client = self.get_test_client()

        # 获取JWT token
        token = self.get_jwt_token(phone_number, old_password)

        # 发送修改密码请求
        response = client.post(
            '/api/user/change-password',
            data=json.dumps({
                'old_password': old_password,
                'new_password': new_password
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['message'])
        assert data['data']['message'] == '密码修改成功'

        # 验证用户可以使用新密码登录
        login_response = client.post(
            '/api/auth/login_phone',
            data=json.dumps({
                'phone': phone_number,
                'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                'password': new_password
            }),
            content_type='application/json'
        )

        login_data = self.assert_api_success(login_response, ['token'])
        assert 'token' in login_data['data']

        # 验证用户无法使用旧密码登录
        old_login_response = client.post(
            '/api/auth/login_phone',
            data=json.dumps({
                'phone': phone_number,
                'code': TEST_CONSTANTS.TEST_VERIFICATION_CODE,
                'password': old_password
            }),
            content_type='application/json'
        )

        old_login_data = json.loads(old_login_response.data)
        assert old_login_data['code'] == 0
        assert '密码不正确' in old_login_data['msg']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])