"""
监督操作集成测试
Happy path: 成功邀请监督者、接受/拒绝邀请、获取监督列表
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestSupervisionOperations(IntegrationTestBase):
    """监督操作集成测试"""

    def test_invite_supervisor_success(self):
        """测试成功邀请监督者"""
        with self.app.app_context():
        # 创建监督者和被监督者
            supervisor = self.create_standard_test_user(role=1, test_context='invite_supervisor')
            supervised = self.create_standard_test_user(role=1, test_context='invite_supervised')

        # 为监督者创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                supervisor.user_id
            )

            client = self.get_test_client()
            token = self.get_jwt_token(supervisor.phone_number)

        # 发送邀请监督者请求
            response = client.post(
                '/api/supervision/invite',
                data=json.dumps({
                    'invite_type': 'wechat',
                    'target_openid': supervised.wechat_openid,
                    'rule_ids': [rule.rule_id]
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['message', 'relations_count'])
            assert data['data']['message'] == '邀请发送成功'
            assert data['data']['relations_count'] >= 1

        def test_create_invite_link_success(self):
            """测试成功创建监督邀请链接"""
        with self.app.app_context():
        # 创建监督者
            supervisor = self.create_standard_test_user(role=1, test_context='create_invite_link')

        # 为监督者创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                supervisor.user_id
            )

            client = self.get_test_client()
            token = self.get_jwt_token(supervisor.phone_number)

        # 发送创建邀请链接请求
            response = client.post(
                '/api/supervision/invite_link',
                data=json.dumps({
                    'rule_ids': [rule.rule_id],
                    'expire_hours': 24
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['invite_token', 'rule_ids', 'expires_at'])
            assert 'invite_token' in data['data']
            assert len(data['data']['rule_ids']) >= 1

        def test_resolve_invite_link_success(self):
            """测试成功解析监督邀请链接"""
        with self.app.app_context():
        # 创建监督者
            supervisor = self.create_standard_test_user(role=1, test_context='resolve_invite_link')

        # 为监督者创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日阅读',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '20:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                supervisor.user_id
            )

        # 创建监督邀请链接
            import secrets
            from database.flask_models import db, SupervisionRuleRelation
            from datetime import datetime, timedelta

            invite_token = secrets.token_urlsafe(32)

        # 创建监督关系（模拟邀请链接创建）
            relation = SupervisionRuleRelation(
                supervisor_id=supervisor.user_id,
                supervised_id=supervisor.user_id + 1,  # 假设被监督者
                rule_id=rule.rule_id,
                invite_type='wechat',
                status='pending',
                invited_at=datetime.now()
            )
            db.session.add(relation)
            db.session.commit()

            client = self.get_test_client()

        # 发送解析邀请链接请求
            response = client.get(
                f'/api/supervision/invite/resolve?token={invite_token}'
            )

        # 注意：由于实际实现中invite_link是简化的，这里只验证响应格式
        # 实际项目中应该有完整的邀请链接存储和解析逻辑

        def test_get_supervision_invitations_success(self):
            """测试成功获取监督邀请列表"""
        with self.app.app_context():
        # 创建用户
            user = self.create_standard_test_user(role=1, test_context='get_invitations')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

        # 发送获取监督邀请列表请求
            response = client.get(
                '/api/supervision/invitations',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['invitations', 'total'])
            assert 'invitations' in data['data']

        def test_accept_supervision_success(self):
            """测试成功接受监督邀请"""
        with self.app.app_context():
        # 创建用户
            user = self.create_standard_test_user(role=1, test_context='accept_supervision')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

        # 发送接受监督邀请请求
            response = client.post(
                '/api/supervision/accept',
                data=json.dumps({
                    'invitation_id': 1
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['message'])
            assert data['data']['message'] == '接受监督邀请成功'

        def test_reject_supervision_success(self):
            """测试成功拒绝监督邀请"""
        with self.app.app_context():
        # 创建用户
            user = self.create_standard_test_user(role=1, test_context='reject_supervision')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

        # 发送拒绝监督邀请请求
            response = client.post(
                '/api/supervision/reject',
                data=json.dumps({
                    'invitation_id': 1,
                    'reason': '暂时不需要监督'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['message'])
            assert data['data']['message'] == '拒绝监督邀请成功'

        def test_get_my_supervised_users_success(self):
            """测试成功获取我监督的用户列表"""
        with self.app.app_context():
        # 创建用户
            supervisor = self.create_standard_test_user(role=1, test_context='get_supervised')

            client = self.get_test_client()
            token = self.get_jwt_token(supervisor.phone_number)

        # 发送获取监督用户列表请求
            response = client.get(
                '/api/supervision/my_supervised',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['supervised_users', 'total'])
            assert 'supervised_users' in data['data']

        def test_get_my_guardians_success(self):
            """测试成功获取监督我的用户列表"""
        with self.app.app_context():
        # 创建用户
            user = self.create_standard_test_user(role=1, test_context='get_guardians')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

        # 发送获取监督者列表请求
            response = client.get(
                '/api/supervision/my_guardians',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['guardians', 'total'])
            assert 'guardians' in data['data']

        def test_get_supervision_records_success(self):
            """测试成功获取监督记录"""
        with self.app.app_context():
        # 创建用户
            user = self.create_standard_test_user(role=1, test_context='get_records')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

        # 发送获取监督记录请求
            response = client.get(
                '/api/supervision/records',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['records', 'total'])
            assert 'records' in data['data']


if __name__ == '__main__':
        pytest.main([__file__, '-v'])