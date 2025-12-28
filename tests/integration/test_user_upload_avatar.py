"""
用户头像上传集成测试
Happy path: 成功上传用户头像
"""

import pytest
import json
import os
import sys
from io import BytesIO

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.integration.conftest import IntegrationTestBase


class TestUserUploadAvatar(IntegrationTestBase):
    """用户头像上传集成测试"""

    def test_upload_avatar_success(self):
        """测试成功上传用户头像"""
        # 创建测试用户（在应用上下文中）
        phone_number = None
        with self.app.app_context():
            user = self.create_standard_test_user(role=1, test_context='upload_avatar')
            phone_number = user.phone_number  # 在上下文中获取phone_number
        client = self.get_test_client()

        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 创建测试图片数据（1x1像素的PNG图片）
        test_image_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01'
            b'\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        )

        # 准备文件上传数据
        data = {
            'avatar': (BytesIO(test_image_data), 'test_avatar.png')
        }

        # 发送上传头像请求
        response = client.post(
            '/api/user/upload-avatar',
            data=data,
            content_type='multipart/form-data',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['avatar_url', 'message'])

        # 验证返回的avatar_url格式
        assert data['data']['avatar_url'].startswith('/static/uploads/avatars/')
        assert data['data']['message'] == '头像上传成功'

        # 验证数据库中的用户头像已更新
        from database.flask_models import User
        with self.app.app_context():
            updated_user = self.db.session.get(User, user.user_id)
            assert updated_user.avatar_url == data['data']['avatar_url']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
