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
    
    def test_invite_supervisor_success(self, client, setup_test_data):
        """测试成功邀请监护人"""
        # Get the actual user IDs from the database
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        supervisor_user = User.query.filter_by(phone_number='13800000006').first()  # 使用用户6而不是用户2避免冲突
        
        # Create a valid token for the solo user
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # Get the rule for the solo user
        rule = CheckinRule.query.filter_by(solo_user_id=solo_user.user_id).first()
        
        # 确保数据库中没有这个监护关系
        existing_supervision = RuleSupervision.query.filter_by(
            rule_id=rule.rule_id,
            supervisor_user_id=supervisor_user.user_id
        ).first()
        if existing_supervision:
            db.session.delete(existing_supervision)
            db.session.commit()
        
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
    
    def test_invite_self_error(self, client, setup_test_data):
        """测试不能邀请自己"""
        # Create a valid token for user_id 1
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # Get the rule for the solo user
        rule = CheckinRule.query.filter_by(solo_user_id=solo_user.user_id).first()
        
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
    
    def test_invite_nonexistent_rule(self, client, setup_test_data):
        """测试邀请不存在的规则"""
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        supervisor_user = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
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
    
    def test_invite_nonexistent_supervisor(self, client, setup_test_data):
        """测试邀请不存在的监护人"""
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        rule = CheckinRule.query.filter_by(solo_user_id=solo_user.user_id).first()
        
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
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
    
    def test_invite_without_permission(self, client, setup_test_data):
        """测试非规则所有者邀请"""
        # 用户3尝试邀请监护人监督用户1的规则
        user3 = User.query.filter_by(phone_number='13800000003').first()
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        supervisor_user = User.query.filter_by(phone_number='13800000002').first()
        
        token_payload = {
            'user_id': user3.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # Get the rule for the solo user
        rule = CheckinRule.query.filter_by(solo_user_id=solo_user.user_id).first()
        
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
    
    def test_invite_missing_fields(self, client, setup_test_data):
        """测试缺少必需字段"""
        solo_user = User.query.filter_by(phone_number='13800000001').first()
        
        token_payload = {
            'user_id': solo_user.user_id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 缺少supervisor_user_id
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 1,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '参数不完整' in data['msg']


