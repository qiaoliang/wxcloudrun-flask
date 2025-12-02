# tests/test_invitations_list_api.py
import pytest
import json
from wxcloudrun import app, db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class TestInvitationsListAPI:
    """邀请列表API测试"""
    
    def test_get_received_invitations(self, client, setup_test_data):
        """测试获取收到的邀请"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 2})()
            
            response = client.get('/api/supervision/invitations?type=received')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
            assert len(data['data']['invitations']) > 0
            
            # 检查邀请数据结构
            invitation = data['data']['invitations'][0]
            assert 'rule_supervision_id' in invitation
            assert 'status' in invitation
            assert 'status_name' in invitation
            assert 'invitation_message' in invitation
            assert 'created_at' in invitation
            assert 'rule' in invitation
            assert 'solo_user' in invitation
            assert 'invited_by' in invitation
    
    def test_get_sent_invitations(self, client, setup_test_data):
        """测试获取发出的邀请"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/supervision/invitations?type=sent')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
            assert len(data['data']['invitations']) > 0
    
    def test_get_invitations_default_type(self, client, setup_test_data):
        """测试默认获取收到的邀请"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 2})()
            
            response = client.get('/api/supervision/invitations')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
    
    def test_get_invitations_with_status_filter(self, client, setup_test_data):
        """测试带状态过滤的邀请列表"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 2})()
            
            response = client.get('/api/supervision/invitations?type=received&status=0')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
            
            # 验证所有返回的邀请都是指定状态
            for invitation in data['data']['invitations']:
                assert invitation['status'] == 0
    
    def test_get_invitations_invalid_status(self, client, setup_test_data):
        """测试无效状态参数的处理"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 2})()
            
            response = client.get('/api/supervision/invitations?type=received&status=invalid')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
    
    def test_get_invitations_empty_result(self, client, setup_test_data):
        """测试空的邀请列表"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 3})()  # 没有邀请的用户
            
            response = client.get('/api/supervision/invitations?type=received')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'invitations' in data['data']
            assert len(data['data']['invitations']) == 0
    
    def test_invitation_data_structure(self, client, setup_test_data):
        """测试邀请数据的完整结构"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 2})()
            
            response = client.get('/api/supervision/invitations?type=received')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            invitation = data['data']['invitations'][0]
            
            # 检查规则信息
            rule = invitation['rule']
            assert 'rule_id' in rule
            assert 'rule_name' in rule
            assert 'icon_url' in rule
            assert 'solo_user' in rule
            
            # 检查独居者信息
            solo_user = rule['solo_user']
            assert 'user_id' in solo_user
            assert 'nickname' in solo_user
            assert 'avatar_url' in solo_user
            
            # 检查邀请人信息
            invited_by = invitation['invited_by']
            assert 'user_id' in invited_by
            assert 'nickname' in invited_by
            assert 'avatar_url' in invited_by


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
            icon_url='icon_url',
            status=1
        )
        
        # 创建测试邀请
        supervisions = [
            RuleSupervision(
                rule_supervision_id=1,
                rule_id=1,
                solo_user_id=1,
                supervisor_user_id=2,
                invited_by_user_id=1,
                status=0,  # 待确认
                invitation_message='请监督我打卡'
            ),
            RuleSupervision(
                rule_supervision_id=2,
                rule_id=1,
                solo_user_id=1,
                supervisor_user_id=3,
                invited_by_user_id=1,
                status=1,  # 已确认
                invitation_message='另一个邀请'
            )
        ]
        
        for user in users:
            db.session.add(user)
        db.session.add(rule)
        for supervision in supervisions:
            db.session.add(supervision)
        db.session.commit()
        
        yield
        
        # 清理测试数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        for user in users:
            db.session.delete(user)
        db.session.commit()