# tests/test_user_profile.py
import pytest
import os
from unittest.mock import patch
import jwt
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timedelta, timezone
from tests.unit.util import create_jwt_token

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
    test_user = UserBuilder().with_phone_number("13800138000").with_nickname("Test User").with_avatar_url("https://example.com/default.jpg").build()
    insert_user(test_user)
    token = create_jwt_token(test_user.user_id)

    uri = '/api/user/profile'
    method = 'POST'
    data = {
        'avatar_url': 'https://example.com/updated.jpg',
        'nickname': 'Updated Name'
    }
    response = client.post(uri,
        headers={
            'Authorization': f'Bearer {token}'
        },
        json=data,
        content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success code is 1 based on response.py
    assert data['msg'] == 'success'  # Success response has 'msg' field based on response.py

    # 验证用户信息已更新
    updated_user = query_user_by_id(test_user.user_id)
    assert updated_user.nickname == 'Updated Name'
    assert updated_user.avatar_url == 'https://example.com/updated.jpg'