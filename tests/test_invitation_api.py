# tests/test_invitation_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision
from tests.base_test import BaseTest


class TestInvitationAPI(BaseTest):
    """邀请API测试"""
    
    def test_invite_supervisor_success(self, client):
        """测试成功邀请监护人"""
        # Create test data using factory methods
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        supervisor_user = self.create_user(
            phone_number='13800000002', 
            nickname='监护人',
            is_solo_user=False,
            is_supervisor=True
        )
        rule = self.create_checkin_rule(
            solo_user_id=solo_user.user_id,
            rule_name='起床打卡'
        )
        
        # Create a valid token for the solo user
        token = self.create_auth_token(solo_user.user_id)
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': rule.rule_id,
                                 'supervisor_user_id': supervisor_user.user_id,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'rule_supervision_id' in data['data']
        assert data['data']['status'] == 0  # 待确认状态
        assert '邀请已发送' in data['data']['message']
    
    def test_invite_self_error(self, client):
        """测试不能邀请自己"""
        # Create test user
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        rule = self.create_checkin_rule(
            solo_user_id=solo_user.user_id,
            rule_name='起床打卡'
        )
        
        # Create a valid token for the solo user
        token = self.create_auth_token(solo_user.user_id)
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': rule.rule_id,
                                 'supervisor_user_id': solo_user.user_id,  # 尝试邀请自己
                                 'invitation_message': '监督自己'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '不能邀请自己' in data['msg']
    
    def test_invite_nonexistent_rule(self, client):
        """测试邀请不存在的规则"""
        # Create test users
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        supervisor_user = self.create_user(
            phone_number='13800000002',
            nickname='监护人',
            is_solo_user=False,
            is_supervisor=True
        )
        
        token = self.create_auth_token(solo_user.user_id)
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 99999,  # 不存在的规则ID
                                 'supervisor_user_id': supervisor_user.user_id,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '不存在' in data['msg']
    
    def test_invite_nonexistent_supervisor(self, client):
        """测试邀请不存在的监护人"""
        # Create test user and rule
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        rule = self.create_checkin_rule(
            solo_user_id=solo_user.user_id,
            rule_name='起床打卡'
        )
        
        token = self.create_auth_token(solo_user.user_id)
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': rule.rule_id,
                                 'supervisor_user_id': 99999,  # 不存在的监护人ID
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '不存在' in data['msg']
    
    def test_invite_without_permission(self, client):
        """测试非规则所有者邀请"""
        # Create test users
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        other_user = self.create_user(
            phone_number='13800000003',
            nickname='其他用户',
            is_solo_user=True,
            is_supervisor=False
        )
        supervisor_user = self.create_user(
            phone_number='13800000002',
            nickname='监护人',
            is_solo_user=False,
            is_supervisor=True
        )
        
        # Create rule for solo_user
        rule = self.create_checkin_rule(
            solo_user_id=solo_user.user_id,
            rule_name='起床打卡'
        )
        
        # other_user tries to invite supervisor for solo_user's rule
        token = self.create_auth_token(other_user.user_id)
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': rule.rule_id,
                                 'supervisor_user_id': supervisor_user.user_id,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '只有规则创建者才能邀请监护人' in data['msg']
    
    def test_invite_missing_fields(self, client):
        """测试缺少必需字段"""
        # Create test user and rule
        solo_user = self.create_user(
            phone_number='13800000001',
            nickname='独居者',
            is_solo_user=True,
            is_supervisor=False
        )
        rule = self.create_checkin_rule(
            solo_user_id=solo_user.user_id,
            rule_name='起床打卡'
        )
        
        token = self.create_auth_token(solo_user.user_id)
        
        # 缺少supervisor_user_id
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': rule.rule_id,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '参数不完整' in data['msg']


