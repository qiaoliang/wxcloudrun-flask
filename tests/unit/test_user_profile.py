# tests/test_user_profile.py
import pytest
import os
from unittest.mock import patch
import jwt
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta, timezone

# 在导入任何模块之前，先加载测试环境变量
env_file = Path(__file__).parent.parent / '.env.unit'
load_dotenv(env_file, override=True)

from wxcloudrun import db
from wxcloudrun.model import User
from wxcloudrun.dao import insert_user, query_user_by_id
from tests.unit.fixtures.user_builder import UserBuilder

def test_update_user_profile_endpoint(client):
    """Test the update user profile endpoint."""
    # 使用Builder模式创建测试用户
    test_user = UserBuilder().with_phone_number("13800138000").build()

    # 使用 DAO 方法插入用户
    insert_user(test_user)

    # 使用 JWT 创建有效的 token
    token = jwt.encode({
        'user_id': test_user.user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')

    # 测试更新用户资料
    response = client.post('/api/user/profile',
                          headers={
                              'Authorization': f'Bearer {token}'
                          },
                          json={
                              'avatar_url': 'https://example.com/updated.jpg',
                              'nickname': 'Updated Name'
                          },
                          content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success code is 1 based on response.py
    assert data['msg'] == 'success'  # Success response has 'msg' field based on response.py

    # 验证用户信息已更新
    updated_user = query_user_by_id(test_user.user_id)
    assert updated_user.nickname == 'Updated Name'
    assert updated_user.avatar_url == 'https://example.com/updated.jpg'