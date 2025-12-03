# tests/test_user_search_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import app, db
from wxcloudrun.model import User
from tests.base_test import BaseTest


class TestUserSearchAPI(BaseTest):
    """用户搜索API测试"""
    
    def test_search_user_by_phone_success(self, client, setup_test_data):
        """测试通过手机号搜索用户成功"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?phone=13800000002',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        assert len(data['data']['users']) == 1
        
        user = data['data']['users'][0]
        assert user['phone_number'] == '13800000002'
        assert user['nickname'] == '监护人1'
        assert 'user_id' in user
    
    def test_search_user_by_nickname_success(self, client, setup_test_data):
        """测试通过昵称搜索用户成功"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?nickname=监护人',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        assert len(data['data']['users']) >= 1
        
        # 验证返回的用户都包含"监护人"字样
        for user in data['data']['users']:
            assert '监护人' in user['nickname']
    
    def test_search_user_not_found(self, client, setup_test_data):
        """测试搜索不存在的用户"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?phone=19999999999',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        assert len(data['data']['users']) == 0
    
    def test_search_user_missing_params(self, client, setup_test_data):
        """测试缺少搜索参数"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '缺少' in data['msg'] or '参数' in data['msg']
    
    def test_search_user_multiple_params(self, client, setup_test_data):
        """测试同时使用多个搜索参数"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?phone=13800000002&nickname=监护人1',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        assert len(data['data']['users']) == 1
        
        user = data['data']['users'][0]
        assert user['phone_number'] == '13800000002'
        assert user['nickname'] == '监护人1'
    
    def test_search_user_unauthorized(self, client, setup_test_data):
        """测试未授权访问"""
        response = client.get('/api/users/search?phone=13800000002')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert 'token' in data['msg'].lower() or '未授权' in data['msg']
    
    def test_search_user_invalid_token(self, client, setup_test_data):
        """测试无效token"""
        response = client.get('/api/users/search?phone=13800000002',
                            headers={'Authorization': 'Bearer invalid_token'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert 'token' in data['msg'].lower() or '无效' in data['msg']
    
    def test_search_user_pagination(self, client, setup_test_data):
        """测试搜索结果分页"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?nickname=用户&limit=2&offset=0',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        assert len(data['data']['users']) <= 2  # 限制返回数量
    
    def test_search_user_with_role_filter(self, client, setup_test_data):
        """测试按角色过滤搜索"""
        user1 = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': user1.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/users/search?role=supervisor',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'users' in data['data']
        
        # 验证返回的用户都是监护人角色
        for user in data['data']['users']:
            assert user['is_supervisor'] == True


