# tests/test_invitation_response_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import app, db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class TestInvitationResponseAPI:
    """邀请响应API测试"""
    
    def test_accept_invitation_success(self, client, setup_test_data):
        """测试接受邀请成功"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
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
        assert data['code'] == 1
        assert data['data']['status'] == 1  # 已确认状态
        assert "已同意邀请" in data['data']['message']
    
    def test_reject_invitation_success(self, client, setup_test_data):
        """测试拒绝邀请成功"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'reject'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert data['data']['status'] == 2  # 已拒绝状态
        assert "已拒绝邀请" in data['data']['message']
    
    def test_respond_nonexistent_invitation(self, client, setup_test_data):
        """测试响应不存在的邀请"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 999,  # 不存在的邀请
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "邀请不存在" in data['msg']
    
    def test_respond_invalid_action(self, client, setup_test_data):
        """测试无效的响应动作"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'invalid_action'  # 无效动作
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "操作类型无效" in data['msg']
    
    def test_respond_without_permission(self, client, setup_test_data):
        """测试无权限响应邀请"""
        # Create a valid token for user_id 3 (not the invited supervisor)
        token_payload = {
            'openid': 'test_openid_3',
            'user_id': 3,
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
        assert "无权限操作此邀请" in data['msg']
    
    def test_respond_already_processed_invitation(self, client, setup_test_data):
        """测试响应已处理的邀请"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 先将邀请状态改为已确认
        supervision = RuleSupervision.query.filter_by(rule_supervision_id=1).first()
        supervision.status = 1
        db.session.commit()
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "邀请已被处理" in data['msg']
    
    def test_respond_with_message(self, client, setup_test_data):
        """测试带响应消息的邀请响应"""
        # Create a valid token for user_id 2 (the supervisor)
        token_payload = {
            'openid': 'test_openid_2',
            'user_id': 2,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/supervision/respond',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_supervision_id': 1,
                                 'action': 'accept',
                                 'response_message': '我很乐意监督您'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 1
        assert data['data']['status'] == 1
        
        # 检查响应消息是否被添加
        supervision = RuleSupervision.query.filter_by(rule_supervision_id=1).first()
        assert "我很乐意监督您" in supervision.invitation_message


@pytest.fixture
def setup_test_data():
    """设置测试数据"""
    with app.app_context():
        # 创建测试用户
        users = [
            User(
                user_id=1,
                wechat_openid='test1',
                nickname='用户1',
                is_solo_user=True,
                is_supervisor=False,
                status=1
            ),
            User(
                user_id=2,
                wechat_openid='test2',
                nickname='监护人1',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                user_id=3,
                wechat_openid='test3',
                nickname='其他用户',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            )
        ]
        
        # 创建测试规则
        rule = CheckinRule(
            rule_id=1,
            solo_user_id=1,
            rule_name='起床打卡',
            status=1
        )
        
        # 创建测试邀请
        supervision = RuleSupervision(
            rule_supervision_id=1,
            rule_id=1,
            solo_user_id=1,
            supervisor_user_id=2,
            invited_by_user_id=1,
            status=0,  # 待确认
            invitation_message='请监督我打卡'
        )
        
        for user in users:
            db.session.add(user)
        db.session.add(rule)
        db.session.add(supervision)
        db.session.commit()
        
        yield
        
        # 清理测试数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        for user in users:
            db.session.delete(user)
        db.session.commit()