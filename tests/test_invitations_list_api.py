# tests/test_invitations_list_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import app, db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class TestInvitationsListAPI:
    """邀请列表API测试"""
    
    def test_get_sent_invitations_success(self, client, setup_test_data):
        """测试获取发送的邀请列表成功"""
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/supervision/invitations?type=sent',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        assert len(data['data']['invitations']) > 0
        
        # 验证返回的数据结构
        invitation = data['data']['invitations'][0]
        assert 'rule_supervision_id' in invitation
        assert 'rule' in invitation
        assert 'rule_name' in invitation['rule']
        assert 'invited_by' in invitation
        assert 'status' in invitation
        assert 'created_at' in invitation
    
    def test_get_received_invitations_success(self, client, setup_test_data):
        """测试获取收到的邀请列表成功"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/supervision/invitations?type=received',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        assert len(data['data']['invitations']) > 0
        
        # 验证返回的数据结构
        invitation = data['data']['invitations'][0]
        assert 'rule_supervision_id' in invitation
        assert 'rule' in invitation
        assert 'rule_name' in invitation['rule']
        assert 'solo_user' in invitation['rule']
        assert 'invited_by' in invitation
        assert 'status' in invitation
        assert 'created_at' in invitation
    
    def test_get_sent_invitations_empty(self, client, setup_test_data):
        """测试获取发送的邀请列表"""
        user5 = User.query.filter_by(phone_number='13800000005').first()  # User5 has no sent invitations
        
        token_payload = {
            'user_id': user5.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/supervision/invitations?type=sent',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        assert len(data['data']['invitations']) == 0
    
    def test_get_received_invitations_empty(self, client, setup_test_data):
        """测试获取收到的邀请列表为空"""
        user6 = User.query.filter_by(phone_number='13800000006').first()  # User6 has no received invitations
        
        token_payload = {
            'user_id': user6.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/supervision/invitations?type=received',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        assert len(data['data']['invitations']) == 0
    
    def test_get_invitations_with_status_filter(self, client, setup_test_data):
        """测试带状态过滤的邀请列表"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 获取待确认的邀请
        response = client.get('/api/supervision/invitations?type=received&status=0',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        
        # 验证所有返回的邀请都是待确认状态
        for invitation in data['data']['invitations']:
            assert invitation['status'] == 0
    
    def test_get_invitations_invalid_status(self, client, setup_test_data):
        """测试无效的状态过滤"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.get('/api/supervision/invitations?type=received&status=invalid',
                            headers={'Authorization': f'Bearer {token}'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'invitations' in data['data']
        # Invalid status should be ignored and return all invitations
        assert len(data['data']['invitations']) > 0
    
    def test_get_invitations_unauthorized(self, client, setup_test_data):
        """测试未授权访问"""
        response = client.get('/api/supervision/invitations?type=sent')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert 'token' in data['msg'].lower() or '未授权' in data['msg']
    
    def test_get_invitations_invalid_token(self, client, setup_test_data):
        """测试无效token"""
        response = client.get('/api/supervision/invitations?type=sent',
                            headers={'Authorization': 'Bearer invalid_token'})
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert 'token' in data['msg'].lower() or '无效' in data['msg']


