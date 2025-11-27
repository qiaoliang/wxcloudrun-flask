# tests/test_login.py
import pytest
import os
from unittest.mock import patch
import jwt
from wxcloudrun import db


def test_login_endpoint(client):
    """Test the login endpoint with a mock code."""
    # Mock the response from WeChat API
    mock_wx_response = {
        'openid': 'mock_openid_123',
        'session_key': 'mock_session_key_456'
    }
    
    with patch('wxcloudrun.views.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_wx_response
        mock_get.return_value.status_code = 200
        
        # Call the login endpoint
        response = client.post('/api/login', 
                              json={'code': 'test_code_789'},
                              content_type='application/json')
        
        # Check the response
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1  # Success code is 1 based on response.py
        assert 'data' in data
        assert 'token' in data['data']
        
        # Verify that the token can be decoded
        token = data['data']['token']
        decoded = jwt.decode(token, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithms=['HS256'])
        assert decoded['openid'] == 'mock_openid_123'
        assert decoded['session_key'] == 'mock_session_key_456'


def test_user_profile_endpoint(client):
    """Test the update user info endpoint."""
    from wxcloudrun.model import User
    from wxcloudrun import db
    
    # First, get a valid token by mocking the login
    openid = 'mock_openid_123_test_user_profile'
    mock_wx_response = {
        'openid': openid,
        'session_key': 'mock_session_key_456'
    }
    
    with patch('wxcloudrun.views.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_wx_response
        mock_get.return_value.status_code = 200
        
        # Create a user first
        test_user = User(
            wechat_openid=openid,
            nickname='Test User',
            avatar_url='https://example.com/avatar.jpg',
            role='solo',
            status='active'
        )
        db.session.add(test_user)
        db.session.commit()
        
        # Get a token
        login_response = client.post('/api/login', 
                                   json={'code': 'test_code_789'},
                                   content_type='application/json')
        token = login_response.get_json()['data']['token']
        
        # Now test update user info with the token
        response = client.post('/api/user/profile',
                              json={
                                  'token': token,
                                  'avatar_url': 'https://example.com/avatar.jpg',
                                  'nickname': 'Test User'
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1  # Success code is 1 based on response.py
        assert data['msg'] == 'success'  # Success response has 'msg' field based on response.py
        
        # Clean up: remove the test user
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
    assert '缺少token参数' in data['msg']  # Error message for missing token (not missing params since body is provided)


def test_user_profile_missing_token_param(client):
    """Test update user info endpoint with empty request body but valid structure."""
    response = client.post('/api/user/profile',
                          json={},
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert '缺少token参数' in data['msg']  # Error message for missing token (empty dict still missing token)


def test_user_profile_invalid_token(client):
    """Test update user info endpoint with invalid token."""
    response = client.post('/api/user/profile',
                          json={
                              'token': 'invalid_token',
                              'avatar_url': 'https://example.com/avatar.jpg',
                              'nickname': 'Test User'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert 'token' in data['msg'] or '无效' in data['msg'] or 'decode' in data['msg']  # Error message for invalid token