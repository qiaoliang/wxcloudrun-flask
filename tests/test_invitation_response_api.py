# tests/test_invitation_response_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision
from tests.base_test import BaseTest


class TestInvitationResponseAPI(BaseTest):
    """邀请响应API测试"""
    
    def test_accept_invitation_success(self, client, setup_test_data):
        """测试接受邀请成功"""
        # Get the supervisor user
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        # Create a valid token for the supervisor
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        print(f"DEBUG: 接受邀请响应数据 = {data}")
        assert data['code'] == 1
        assert data['data']['status'] == 1  # 已确认状态
        assert "已同意邀请" in data['data']['message']
    
    def test_reject_invitation_success(self, client, setup_test_data):
        """测试拒绝邀请成功"""
        # Get the supervisor user (监护人2)
        supervisor = User.query.filter_by(phone_number='13800000004').first()
        
        # Create a valid token for the supervisor
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 2,
                                 'action': 'reject'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        print(f"DEBUG: 拒绝邀请响应数据 = {data}")
        assert data['code'] == 1
        assert data['data']['status'] == 2  # 已拒绝状态
        assert "已拒绝邀请" in data['data']['message']
    
    def test_respond_nonexistent_invitation(self, client, setup_test_data):
        """测试响应不存在的邀请"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 99999,  # 不存在的邀请ID
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '不存在' in data['msg']
    
    def test_respond_without_permission(self, client, setup_test_data):
        """测试无权限响应邀请"""
        # 用户4尝试响应用户2的邀请
        user4 = User.query.filter_by(phone_number='13800000004').first()
        
        token_payload = {
            'user_id': user4.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '权限不足' in data['msg'] or '无权' in data['msg']
    
    def test_respond_already_responded(self, client, setup_test_data):
        """测试重复响应邀请"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 先接受邀请
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        assert json.loads(response.data)['code'] == 1
        
        # 再尝试接受同一邀请
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '邀请已被处理' in data['msg'] or '已处理' in data['msg']
    
    def test_respond_invalid_action(self, client, setup_test_data):
        """测试无效的响应动作"""
        supervisor = User.query.filter_by(phone_number='13800000003').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 2,
                                 'action': 'invalid_action'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '无效' in data['msg'] or 'action' in data['msg'].lower()
    
    def test_respond_missing_fields(self, client, setup_test_data):
        """测试缺少必需字段"""
        supervisor = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': supervisor.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 缺少action字段
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '参数不完整' in data['msg']


