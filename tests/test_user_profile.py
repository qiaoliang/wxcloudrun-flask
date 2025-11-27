# tests/test_user_profile.py
import pytest
import os
from unittest.mock import patch
import jwt
from wxcloudrun import db
from wxcloudrun.model import User


def test_update_user_profile_endpoint(client):
    """Test the update user profile endpoint."""
    # First, clean up any existing user with the same openid
    existing_user = User.query.filter_by(wechat_openid='test_openid_123_update').first()
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
    
    # Create a test user first with a unique identifier for this test
    test_user = User(
        wechat_openid='test_openid_123_update',
        nickname='Original Name',
        avatar_url='https://example.com/original.jpg',
        role='solo',
        status='active'
    )
    db.session.add(test_user)
    db.session.commit()

    # Create a valid token
    token_payload = {
        'openid': 'test_openid_123_update',  # Match the openid to the test user
        'session_key': 'test_session_key'
    }
    token = jwt.encode(token_payload, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')
    
    # Test updating user profile
    response = client.post('/api/user/profile',
                          json={
                              'token': token,
                              'nickname': 'Updated Name',
                              'avatar_url': 'https://example.com/updated.jpg',
                              'phone_number': '13900139000'  # 使用唯一电话号码
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success code is 1 based on response.py
    assert data['msg'] == 'success'
    
    # Verify the user was updated in the database
    updated_user = User.query.filter_by(wechat_openid='test_openid_123_update').first()
    assert updated_user.nickname == 'Updated Name'
    assert updated_user.avatar_url == 'https://example.com/updated.jpg'
    assert updated_user.phone_number == '13900139000'
    
    # Clean up: remove the test user
    db.session.delete(updated_user)
    db.session.commit()


def test_update_user_profile_partial_fields(client):
    """Test updating only some fields in user profile."""
    # First, clean up any existing user with the same openid
    existing_user = User.query.filter_by(wechat_openid='test_openid_456_partial').first()
    if existing_user:
        db.session.delete(existing_user)
        db.session.commit()
    
    # Create a test user first with a unique identifier for this test
    test_user = User(
        wechat_openid='test_openid_456_partial',
        nickname='Original Name',
        avatar_url='https://example.com/original.jpg',
        phone_number='13800138001',  # 使用唯一电话号码
        role='solo',
        status='active'
    )
    db.session.add(test_user)
    db.session.commit()

    # Create a valid token
    token_payload = {
        'openid': 'test_openid_456_partial',  # Match the openid to the test user
        'session_key': 'test_session_key'
    }
    token = jwt.encode(token_payload, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')
    
    # Test updating only nickname, leaving other fields unchanged
    response = client.post('/api/user/profile',
                          json={
                              'token': token,
                              'nickname': 'Partially Updated Name'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['msg'] == 'success'
    
    # Verify only nickname was updated
    updated_user = User.query.filter_by(wechat_openid='test_openid_456_partial').first()
    assert updated_user.nickname == 'Partially Updated Name'
    assert updated_user.avatar_url == 'https://example.com/original.jpg'  # Should remain unchanged
    assert updated_user.phone_number == '13800138001'  # Should remain unchanged
    
    # Clean up: remove the test user
    db.session.delete(updated_user)
    db.session.commit()


def test_update_user_profile_missing_token(client):
    """Test update user profile endpoint without token."""
    response = client.post('/api/user/profile',
                          json={
                              'nickname': 'Should Not Update',
                              'avatar_url': 'https://example.com/test.jpg'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert '缺少token参数' in data['msg']


def test_update_user_profile_invalid_token(client):
    """Test update user profile endpoint with invalid token."""
    response = client.post('/api/user/profile',
                          json={
                              'token': 'invalid_token',
                              'nickname': 'Should Not Update',
                              'avatar_url': 'https://example.com/test.jpg'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert 'token' in data['msg']  # Should contain token-related error message


def test_update_user_profile_user_not_found(client):
    """Test update user profile endpoint with non-existent user."""
    # Create a valid token for non-existent user
    token_payload = {
        'openid': 'non_existent_openid',
        'session' : 'test_session_key'
    }
    token = jwt.encode(token_payload, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithm='HS256')
    
    response = client.post('/api/user/profile',
                          json={
                              'token': token,
                              'nickname': 'Should Not Update',
                              'avatar_url': 'https://example.com/test.jpg'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert '用户不存在' in data['msg']