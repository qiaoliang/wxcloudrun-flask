# tests/test_user_profile.py
import pytest
import os
from unittest.mock import patch
import jwt
from dotenv import load_dotenv
from pathlib import Path

# 在导入任何模块之前，先加载测试环境变量
env_file = Path(__file__).parent.parent / '.env.unit'
load_dotenv(env_file, override=True)

from wxcloudrun import db
from wxcloudrun.model import User


def test_update_user_profile_endpoint(client):
    """Test the update user profile endpoint."""
    # 确保数据库表已创建
    db.create_all()
    
    # First, clean up any existing user with the same phone number
    test_phone = "13800138000"
    existing_user = User.query.filter_by(phone_number=test_phone).first()
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
    
    # Create a test user first with a unique identifier for this test
    test_user = User(
        phone_number=test_phone,
        nickname='Original Name',
        avatar_url='https://example.com/original.jpg',
        role=1,  # 1 = solo
        status=1,  # 1 = normal
        auth_type='phone'
    )
    db.session.add(test_user)
    db.session.commit()

    # Create a valid token using user_id instead of openid
    import datetime
    token_payload = {
        'user_id': test_user.user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # 设置7天过期时间
    }
    token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
    
    # Test updating user profile
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
    
    # Verify the user was updated
    updated_user = User.query.filter_by(phone_number=test_phone).first()
    assert updated_user.nickname == 'Updated Name'
    assert updated_user.avatar_url == 'https://example.com/updated.jpg'
    
    # Clean up: remove the test user
    db.session.delete(updated_user)
    db.session.commit()


def test_update_partial_user_profile_endpoint(client):
    """Test updating partial user profile information."""
    # 确保数据库表已创建
    db.create_all()
    
    # First, clean up any existing user with the same phone number
    test_phone = "13800138001"
    existing_user = User.query.filter_by(phone_number=test_phone).first()
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
    
    # Create a test user
    test_user = User(
        phone_number=test_phone,
        nickname='Test User',
        avatar_url='https://example.com/test.jpg',
        role=1,  # 1 = solo
        status=1,  # 1 = normal
        auth_type='phone'
    )
    db.session.add(test_user)
    db.session.commit()

    # Create a valid token
    import datetime
    token_payload = {
        'user_id': test_user.user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
    
    # Test updating only nickname
    response = client.post('/api/user/profile',
                          headers={
                              'Authorization': f'Bearer {token}'
                          },
                          json={
                              'nickname': 'Partially Updated Name'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['msg'] == 'success'
    
    # Verify only nickname was updated
    updated_user = User.query.filter_by(phone_number=test_phone).first()
    assert updated_user.nickname == 'Partially Updated Name'
    assert updated_user.avatar_url == 'https://example.com/test.jpg'  # Unchanged
    
    # Clean up
    db.session.delete(updated_user)
    db.session.commit()


def test_get_user_profile_endpoint(client):
    """Test the get user profile endpoint."""
    # 确保数据库表已创建
    db.create_all()
    
    # Create a test user
    test_phone = "13800138002"
    test_user = User(
        phone_number=test_phone,
        nickname='Test User',
        avatar_url='https://example.com/test.jpg',
        role=2,  # 2 = supervisor
        is_solo_user=False,  # Not a solo user
        is_supervisor=True,  # Is a supervisor
        status=1,  # 1 = normal
        auth_type='phone'
    )
    db.session.add(test_user)
    db.session.commit()

    # Create a valid token
    import datetime
    token_payload = {
        'user_id': test_user.user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
    
    # Test getting user profile
    response = client.get('/api/user/profile',
                         headers={
                             'Authorization': f'Bearer {token}'
                         })
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert 'data' in data
    assert data['data']['nickname'] == 'Test User'
    assert data['data']['avatar_url'] == 'https://example.com/test.jpg'
    assert data['data']['role_name'] == 'supervisor'
    
    # Clean up
    db.session.delete(test_user)
    db.session.commit()


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


def test_user_profile_missing_token_param(client):
    """Test update user info endpoint with empty request body but valid structure."""
    response = client.post('/api/user/profile',
                          json={},
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
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert 'token' in data['msg'].lower() or '无效' in data['msg'] or 'decode' in data['msg'].lower()  # Error message for invalid token


def test_user_profile_nonexistent_user(client):
    """Test updating profile for a non-existent user."""
    import datetime
    # Create a token with a non-existent user_id
    token_payload = {
        'user_id': 99999,  # Non-existent user ID
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
    }
    token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
    
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