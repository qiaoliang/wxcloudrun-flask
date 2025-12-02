# tests/integration_test_supervision_flow.py
import pytest
import json
from wxcloudrun import app, db
from wxcloudrun.model import User, CheckinRule, RuleSupervision


class TestSupervisionFlow:
    """监护功能完整流程集成测试"""
    
    def test_complete_supervision_flow(self, client, setup_test_data):
        """测试完整的监护流程"""
        with app.test_request_context():
            from flask import g
            
            # Step 1: 用户1搜索用户2
            g.current_user = type('User', (), {'user_id': 1})()
            response = client.get('/api/users/search?nickname=监护人')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert len(data['data']['users']) > 0
            
            # 找到用户2
            supervisor_user = None
            for user in data['data']['users']:
                if user['user_id'] == 2:
                    supervisor_user = user
                    break
            assert supervisor_user is not None
            
            # Step 2: 用户1邀请用户2作为监护人
            response = client.post('/api/rules/supervision/invite',
                                 json={
                                     'rule_id': 1,
                                     'supervisor_user_id': 2,
                                     'invitation_message': '请监督我起床打卡'
                                 })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            invitation_id = data['data']['rule_supervision_id']
            
            # Step 3: 用户2查看收到的邀请
            g.current_user = type('User', (), {'user_id': 2})()
            response = client.get('/api/supervision/invitations?type=received')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert len(data['data']['invitations']) > 0
            
            # 验证邀请信息
            invitation = None
            for inv in data['data']['invitations']:
                if inv['rule_supervision_id'] == invitation_id:
                    invitation = inv
                    break
            assert invitation is not None
            assert invitation['status'] == 0  # 待确认
            assert invitation['invitation_message'] == '请监督我起床打卡'
            
            # Step 4: 用户2接受邀请
            response = client.post('/api/supervision/respond',
                                 json={
                                     'rule_supervision_id': invitation_id,
                                     'action': 'accept',
                                     'response_message': '我很乐意监督您'
                                 })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert data['data']['status'] == 1  # 已确认
            
            # Step 5: 验证监护关系已建立
            response = client.get('/api/rules/supervision/list?rule_id=1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert len(data['data']['supervisions']) > 0
            
            # 验证监护人信息
            supervision = None
            for sup in data['data']['supervisions']:
                if sup['supervisor']['user_id'] == 2:
                    supervision = sup
                    break
            assert supervision is not None
            assert supervision['status'] == 1
            assert supervision['supervisor']['nickname'] == '监护人1'
            
            # Step 6: 用户2查看监护的规则
            response = client.get('/api/supervisor/rules')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert len(data['data']['supervised_rules']) > 0
            
            # 验证规则信息
            supervised_rule = None
            for rule in data['data']['supervised_rules']:
                if rule['rule']['rule_id'] == 1:
                    supervised_rule = rule
                    break
            assert supervised_rule is not None
            assert supervised_rule['rule']['rule_name'] == '起床打卡'
            assert supervised_rule['solo_user']['nickname'] == '用户1'
            
            # Step 7: 用户1查看发出的邀请
            g.current_user = type('User', (), {'user_id': 1})()
            response = client.get('/api/supervision/invitations?type=sent')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            
            # 找到已接受的邀请
            accepted_invitation = None
            for inv in data['data']['invitations']:
                if inv['rule_supervision_id'] == invitation_id:
                    accepted_invitation = inv
                    break
            assert accepted_invitation is not None
            assert accepted_invitation['status'] == 1  # 已确认
            assert accepted_invitation['responded_at'] is not None
    
    def test_reject_invitation_flow(self, client, setup_test_data):
        """测试拒绝邀请的流程"""
        with app.test_request_context():
            from flask import g
            
            # Step 1: 用户1邀请用户2
            g.current_user = type('User', (), {'user_id': 1})()
            response = client.post('/api/rules/supervision/invite',
                                 json={
                                     'rule_id': 1,
                                     'supervisor_user_id': 2,
                                     'invitation_message': '请监督我'
                                 })
            assert response.status_code == 200
            data = json.loads(response.data)
            invitation_id = data['data']['rule_supervision_id']
            
            # Step 2: 用户2拒绝邀请
            g.current_user = type('User', (), {'user_id': 2})()
            response = client.post('/api/supervision/respond',
                                 json={
                                     'rule_supervision_id': invitation_id,
                                     'action': 'reject',
                                     'response_message': '我现在没有时间'
                                 })
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert data['data']['status'] == 2  # 已拒绝
            
            # Step 3: 验证监护关系没有建立
            response = client.get('/api/rules/supervision/list?rule_id=1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            # 应该没有活跃的监护关系
            for supervision in data['data']['supervisions']:
                assert supervision['status'] != 1
    
    def test_multiple_supervisors_flow(self, client, setup_test_data):
        """测试多个监护人的流程"""
        with app.test_request_context():
            from flask import g
            
            # Step 1: 用户1邀请多个监护人
            g.current_user = type('User', (), {'user_id': 1})()
            for supervisor_id in [2, 3, 4]:
                response = client.post('/api/rules/supervision/invite',
                                     json={
                                         'rule_id': 1,
                                         'supervisor_user_id': supervisor_id,
                                         'invitation_message': f'请监督我 - 邀请监护人{supervisor_id}'
                                     })
                assert response.status_code == 200
            
            # Step 2: 所有监护人都接受邀请
            for supervisor_id in [2, 3, 4]:
                g.current_user = type('User', (), {'user_id': supervisor_id})()
                response = client.get('/api/supervision/invitations?type=received')
                assert response.status_code == 200
                data = json.loads(response.data)
                
                # 找到邀请并接受
                for invitation in data['data']['invitations']:
                    if invitation['rule']['rule_id'] == 1:
                        response = client.post('/api/supervision/respond',
                                             json={
                                                 'rule_supervision_id': invitation['rule_supervision_id'],
                                                 'action': 'accept'
                                             })
                        assert response.status_code == 200
                        break
            
            # Step 3: 验证有多个监护人
            g.current_user = type('User', (), {'user_id': 1})()
            response = client.get('/api/rules/supervision/list?rule_id=1')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            
            active_supervisors = [s for s in data['data']['supervisions'] if s['status'] == 1]
            assert len(active_supervisors) == 3
            
            # Step 4: 每个监护人都能看到监护的规则
            for supervisor_id in [2, 3, 4]:
                g.current_user = type('User', (), {'user_id': supervisor_id})()
                response = client.get('/api/supervisor/rules')
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['code'] == 1
                assert len(data['data']['supervised_rules']) > 0


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
                nickname='监护人2',
                is_solo_user=False,
                is_supervisor=True,
                status=1
            ),
            User(
                user_id=4,
                wechat_openid='test4',
                nickname='监护人3',
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
        
        for user in users:
            db.session.add(user)
        db.session.add(rule)
        db.session.commit()
        
        yield
        
        # 清理测试数据
        RuleSupervision.query.delete()
        CheckinRule.query.delete()
        for user in users:
            db.session.delete(user)
        db.session.commit()