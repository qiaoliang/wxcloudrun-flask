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

def test_get_user_profile_endpoint(client):
    """Test the get user profile endpoint."""
    # Create a test user using factory method
    test_user = UserBuilder().with_phone_number("13900139000").with_avatar_url('https://example.com/get.jpg').with_nickname('Test GET User').build()
    insert_user(test_user)
    # Create a valid token using factory method
    token = create_jwt_token(test_user.user_id)

    # Test getting user profile
    response = client.get('/api/user/profile',
                         headers={
                             'Authorization': f'Bearer {token}'
                         })

    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert 'data' in data
    assert data['data']['phone_number'] == '13900139000'
    assert data['data']['nickname'] == 'Test GET User'
    assert data['data']['avatar_url'] == 'https://example.com/get.jpg'


def test_user_profile_missing_token(client):
    """Test update user info endpoint without token."""
    response = client.post('/api/user/profile',
                          json={
                              'avatar_url': 'https://example.com/avatar.jpg',
                              'nickname': 'Test User'
                          },
                          content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert '缺少token参数' in data['msg']  # Error message for missing token

def test_user_profile_invalid_token(client):
    """Test update user info endpoint with invalid token."""
    response = client.post('/api/user/profile',
                          headers={
                              'Authorization': 'Bearer invalid_token'
                          },
                          json={
                              'avatar_url': 'https://example.com/avatar.jpg',
                              'nickname': 'Test User'
                          },
                          content_type='application/json')

    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert 'token' in data['msg'].lower() or '无效' in data['msg'] or 'decode' in data['msg'].lower()

def test_user_profile_nonexistent_user(client):
    """Test updating profile for a non-existent user."""
    # Create a token with a non-existent user_id
    token = create_jwt_token(99999)  # Non-existent user ID
    response = client.post('/api/user/profile',
                          headers={
                              'Authorization': f'Bearer {token}'
                          },
                          json={
                              'nickname': 'Should Not Work'
                          },
                          content_type='application/json')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Should return error for non-existent user
    assert '用户不存在' in data['msg'] or '不存在' in data['msg']