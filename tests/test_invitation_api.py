# tests/test_invitation_api.py
import pytest
import json
import jwt
import datetime
from wxcloudrun import db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class TestInvitationAPI:
    """邀请API测试"""
    
    def test_invite_supervisor_success(self, client, setup_test_data):
        """测试成功邀请监护人"""
        # Get the actual user IDs from the database
        solo_user = User.query.filter_by(wechat_openid='test1').first()
        supervisor_user = User.query.filter_by(wechat_openid='test2').first()
        
        # Create a valid token for the solo user
        token_payload = {
            'openid': 'test1',
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
        token_payload = {
            'openid': 'test_openid_1',
            'user_id': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 1,
                                 'supervisor_user_id': 1,  # 自己
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "不能邀请自己" in data['msg']
    
    def test_invite_nonexistent_rule(self, client, setup_test_data):
        """测试邀请不存在的规则"""
        # Create a valid token for user_id 1
        token_payload = {
            'openid': 'test_openid_1',
            'user_id': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 999,  # 不存在的规则
                                 'supervisor_user_id': 2,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "打卡规则不存在" in data['msg']
    
    def test_invite_non_supervisor_user(self, client, setup_test_data):
        """测试邀请非监护人用户"""
        # Create a valid token for user_id 1
        token_payload = {
            'openid': 'test_openid_1',
            'user_id': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 1,
                                 'supervisor_user_id': 3,  # 非监护人用户
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
    
    def test_invite_max_supervisors(self, client, setup_test_data):
        """测试监护人数量限制"""
        # Create a valid token for user_id 1
        token_payload = {
            'openid': 'test_openid_1',
            'user_id': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 先创建5个监护关系
        for i in range(2, 7):
            supervision = RuleSupervision(
                rule_id=1,
                solo_user_id=1,
                supervisor_user_id=i,
                invited_by_user_id=1,
                status=1  # 已确认
            )
            db.session.add(supervision)
        db.session.commit()
        
        # 尝试邀请第6个监护人
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 1,
                                 'supervisor_user_id': 7,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['code'] == 0
        assert "最多只能有5个监护人" in data['msg']
    
    def test_invite_duplicate_invitation(self, client, setup_test_data):
        """测试重复邀请"""
        # Create a valid token for user_id 1
        token_payload = {
            'openid': 'test_openid_1',
            'user_id': 1,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)
        }
        token = jwt.encode(token_payload, '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f', algorithm='HS256')
        
        # 先创建一个待确认的邀请
        supervision = RuleSupervision(
            rule_id=1,
            solo_user_id=1,
            supervisor_user_id=2,
            invited_by_user_id=1,
            status=0  # 待确认
        )
        db.session.add(supervision)
        db.session.commit()
        
        # 尝试再次邀请同一个用户
        response = client.post('/api/rules/supervision/invite',
                             headers={'Authorization': f'Bearer {token}'},
                             json={
                                 'rule_id': 1,
                                 'supervisor_user_id': 2,
                                 'invitation_message': '请监督我'
                             })
        assert response.status_code == 200
        
        data = json.loads(response.data)
            assert data['code'] == 0
            assert "已向该用户发送邀请" in data['msg']


@pytest.fixture
def setup_test_data():
    """设置测试数据"""
    from wxcloudrun import app
    with app.app_context():
        # 创建测试用户
        users = [
            User(
                wechat_openid='test1',
                nickname='用户1',
                is_solo_user=True,
                is_supervisor=False,
                status=1
            ),
            User(
                wechat_openid='test2',
                nickname='监护人1',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                wechat_openid='test3',
                nickname='普通用户',
                is_solo_user=False,
                is_supervisor=False,
                status=1
            ),
            User(
                wechat_openid='test4',
                nickname='监护人2',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                wechat_openid='test5',
                nickname='监护人3',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                wechat_openid='test6',
                nickname='监护人4',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                wechat_openid='test7',
                nickname='监护人5',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            )
        ]
        
        # 先提交用户以获取自动生成的ID
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        # 创建测试规则（使用第一个用户的ID）
        rule = CheckinRule(
            solo_user_id=users[0].user_id,  # 使用实际的用户ID
            rule_name='起床打卡',
            status=1
        )
        
        db.session.add(rule)
        db.session.commit()
        
        yield
        
        # 清理测试数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        for user in users:
            db.session.delete(user)
        db.session.commit()