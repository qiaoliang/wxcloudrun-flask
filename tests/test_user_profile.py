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
from tests.base_test import BaseTest


class TestUserProfile(BaseTest):
    """用户档案测试"""
    
    def test_update_user_profile_endpoint(self, client):
        """Test the update user profile endpoint."""
        # Create a test user using factory method
        test_user = self.create_user(
            phone_number="13800138000",
            nickname='Original Name',
            avatar_url='https://example.com/original.jpg',
            role=1,  # 1 = solo
            status=1,  # 1 = normal
        )

        # Create a valid token using factory method
        token = self.create_auth_token(test_user.user_id)
        
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
        updated_user = User.query.filter_by(phone_number="13800138000").first()
        assert updated_user.nickname == 'Updated Name'
        assert updated_user.avatar_url == 'https://example.com/updated.jpg'

    def test_update_partial_user_profile_endpoint(self, client):
        """Test updating partial user profile information."""
        # Create a test user using factory method
        test_user = self.create_user(
            phone_number="13800138001",
            nickname='Test User',
            avatar_url='https://example.com/test.jpg',
            role=1,  # 1 = solo
            status=1,  # 1 = normal
        )

        # Create a valid token using factory method
        token = self.create_auth_token(test_user.user_id)
        
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
        updated_user = User.query.filter_by(phone_number="13800138001").first()
        assert updated_user.nickname == 'Partially Updated Name'
        assert updated_user.avatar_url == 'https://example.com/test.jpg'  # Unchanged

    def test_get_user_profile_endpoint(self, client):
        """Test the get user profile endpoint."""
        # Create a test user using factory method
        test_user = self.create_user(
            phone_number="13800138002",
            nickname='Test User',
            avatar_url='https://example.com/test.jpg',
            role=2,  # 2 = supervisor
            is_solo_user=False,  # Not a solo user
            is_supervisor=True,  # Is a supervisor
            status=1,  # 1 = normal
        )

        # Create a valid token using factory method
        token = self.create_auth_token(test_user.user_id)
        
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

    def test_user_profile_missing_token(self, client):
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

    def test_user_profile_missing_token_param(self, client):
        """Test update user info endpoint with empty request body but valid structure."""
        response = client.post('/api/user/profile',
                              json={},
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0  # Error response code is 0 based on response.py
        assert '缺少token参数' in data['msg']  # Error message for missing token

    def test_user_profile_invalid_token(self, client):
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

    def test_user_profile_nonexistent_user(self, client):
        """Test updating profile for a non-existent user."""
        # Create a token with a non-existent user_id
        token = self.create_auth_token(99999)  # Non-existent user ID
        
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