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

from tests.integration.conftest import IntegrationTestBase
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
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            client = self.get_test_client()
            token = self.get_jwt_token(supervisor.phone_number)

            # 发送邀请监督者请求
            response = client.post(
                '/api/supervision/invite',
                data=json.dumps({
                    'invite_type': 'wechat',
                    'target_openid': supervised.wechat_openid,
                    'rule_ids': [rule_id]
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
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            client = self.get_test_client()
            token = self.get_jwt_token(supervisor.phone_number)

            # 发送创建邀请链接请求
            response = client.post(
                '/api/supervision/invite_link',
                data=json.dumps({
                    'rule_ids': [rule_id],
                    'expire_hours': 24
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应 - 根据 API 契约应该返回 token, url, mini_path, expire_at
            data = self.assert_api_success(response, ['token', 'url', 'mini_path', 'expire_at'])
            assert 'token' in data['data']
            assert 'url' in data['data']
            assert 'mini_path' in data['data']
            assert 'expire_at' in data['data']

    def test_resolve_invite_link_success(self):
        """测试成功解析监督邀请链接"""
        with self.app.app_context():
            # 创建监督者
            supervisor = self.create_standard_test_user(role=1, test_context='resolve_invite_link')

            # 为监督者创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日阅读',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '20:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 创建监督邀请链接
            import secrets
            from database.flask_models import db, SupervisionRuleRelation
            from datetime import datetime, timedelta

            invite_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=24)

            # 创建监督关系（模拟邀请链接创建）
            relation = SupervisionRuleRelation(
                solo_user_id=supervisor.user_id,
                supervisor_user_id=supervisor.user_id + 1,  # 假设被监督者
                rule_id=rule_id,
                status=1,  # Pending status
                invite_token=invite_token,
                invite_expires_at=expires_at
            )
            db.session.add(relation)
            db.session.commit()

            client = self.get_test_client()

            # 发送解析邀请链接请求
            response = client.get(
                f'/api/supervision/invite/resolve?token={invite_token}'
            )

            # 验证响应格式
            data = self.assert_api_success(response, ['relation_id', 'rule_info', 'inviter_info', 'expires_at'])
            assert 'relation_id' in data['data']
            assert 'rule_info' in data['data']
            assert 'inviter_info' in data['data']
            assert 'expires_at' in data['data']
            assert data['data']['rule_info']['rule_name'] == '每日阅读'
            assert data['data']['inviter_info']['user_id'] == supervisor.user_id
            assert data['data']['is_expired'] == False

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
            # 创建用户和监督关系
            supervisor = self.create_standard_test_user(role=1, test_context='accept_supervision')
            supervised = self.create_standard_test_user(role=1, test_context='accept_supervised')

            # 为监督者创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 创建监督关系
            from database.flask_models import db, SupervisionRuleRelation
            relation = SupervisionRuleRelation(
                solo_user_id=supervisor.user_id,
                supervisor_user_id=supervised.user_id,
                rule_id=rule_id,
                status=1  # Pending status
            )
            db.session.add(relation)
            db.session.commit()

            client = self.get_test_client()
            token = self.get_jwt_token(supervised.phone_number)

            # 发送接受监督邀请请求
            response = client.post(
                '/api/supervision/accept',
                data=json.dumps({
                    'relation_id': relation.relation_id  # 使用 relation_id 而不是 invitation_id
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['relation_id', 'status'])
            assert data['data']['relation_id'] == relation.relation_id
            assert data['data']['status'] == 2  # 2 = 已激活

    def test_reject_supervision_success(self):
        """测试成功拒绝监督邀请"""
        with self.app.app_context():
            # 创建用户和监督关系
            supervisor = self.create_standard_test_user(role=1, test_context='reject_supervision')
            supervised = self.create_standard_test_user(role=1, test_context='reject_supervised')

            # 为监督者创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 创建监督关系
            from database.flask_models import db, SupervisionRuleRelation
            relation = SupervisionRuleRelation(
                solo_user_id=supervisor.user_id,
                supervisor_user_id=supervised.user_id,
                rule_id=rule_id,
                status=1  # Pending status
            )
            db.session.add(relation)
            db.session.commit()

            client = self.get_test_client()
            token = self.get_jwt_token(supervised.phone_number)

            # 发送拒绝监督邀请请求
            response = client.post(
                '/api/supervision/reject',
                data=json.dumps({
                    'relation_id': relation.relation_id,
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

            # 发送获取我监督的用户列表请求
            response = client.get(
                '/api/supervision/my_supervised',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['supervised_users', 'total'])
            assert 'supervised_users' in data['data']

    def test_get_my_guardians_success(self):
        """测试成功获取我的监护人列表"""
        with self.app.app_context():
            # 创建用户
            user = self.create_standard_test_user(role=1, test_context='get_guardians')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 发送获取我的监护人列表请求
            response = client.get(
                '/api/supervision/my_guardians',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['guardians', 'total'])
            assert 'guardians' in data['data']

    def test_check_expired_invitations(self):
        """测试邀请过期检查功能"""
        with self.app.app_context():
            from datetime import datetime, timedelta
            from database.flask_models import SupervisionRuleRelation, db
            from app.infrastructure.persistence.repository_factory import RepositoryFactory

            # 创建监督者
            supervisor = self.create_standard_test_user(role=1, test_context='expired_invitation')
            supervised = self.create_standard_test_user(role=1, test_context='expired_invitation_user')

            # 为监督者创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 创建一个已过期的邀请（过期时间设置为昨天）
            expires_at = datetime.now() - timedelta(days=1)
            relation = SupervisionRuleRelation(
                solo_user_id=supervised.user_id,
                supervisor_user_id=supervisor.user_id,
                rule_id=rule_id,
                status=1,  # 待处理
                invite_expires_at=expires_at,
                invitation_type='internal'
            )
            db.session.add(relation)
            db.session.commit()

            # 执行过期检查
            supervision_repo = RepositoryFactory.get_supervision_relation_repository()
            expired_invitations = supervision_repo.find_expired_invitations()

            # 验证找到了过期的邀请
            assert len(expired_invitations) > 0
            assert relation.relation_id in [inv.relation_id for inv in expired_invitations]

            # 批量更新状态为已过期
            expired_ids = [inv.relation_id for inv in expired_invitations]
            updated_count = supervision_repo.batch_update_status(expired_ids, 4)

            # 验证更新成功
            assert updated_count > 0

            # 从数据库重新查询，验证状态已更新
            db.session.refresh(relation)
            assert relation.status == 4  # 已过期

    def test_check_expired_invitations_with_active(self):
        """测试邀请过期检查功能 - 验证不会影响未过期的邀请"""
        with self.app.app_context():
            from datetime import datetime, timedelta
            from database.flask_models import SupervisionRuleRelation, db
            from app.infrastructure.persistence.repository_factory import RepositoryFactory

            # 创建监督者
            supervisor = self.create_standard_test_user(role=1, test_context='mixed_invitation')
            supervised = self.create_standard_test_user(role=1, test_context='mixed_invitation_user')

            # 为监督者创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=supervisor.user_id,
                rule_data={
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 创建一个已过期的邀请
            expires_at_past = datetime.now() - timedelta(days=1)
            expired_relation = SupervisionRuleRelation(
                solo_user_id=supervised.user_id,
                supervisor_user_id=supervisor.user_id,
                rule_id=rule_id,
                status=1,  # 待处理
                invite_expires_at=expires_at_past,
                invitation_type='internal'
            )
            db.session.add(expired_relation)

            # 创建一个未过期的邀请（过期时间设置为明天）
            expires_at_future = datetime.now() + timedelta(days=1)
            active_relation = SupervisionRuleRelation(
                solo_user_id=supervised.user_id,
                supervisor_user_id=supervisor.user_id,
                rule_id=rule_id,
                status=1,  # 待处理
                invite_expires_at=expires_at_future,
                invitation_type='internal'
            )
            db.session.add(active_relation)
            db.session.commit()

            # 执行过期检查
            supervision_repo = RepositoryFactory.get_supervision_relation_repository()
            expired_invitations = supervision_repo.find_expired_invitations()

            # 验证只找到了过期的邀请
            assert len(expired_invitations) == 1
            assert expired_relation.relation_id in [inv.relation_id for inv in expired_invitations]
            assert active_relation.relation_id not in [inv.relation_id for inv in expired_invitations]

            # 批量更新状态为已过期
            expired_ids = [inv.relation_id for inv in expired_invitations]
            supervision_repo.batch_update_status(expired_ids, 4)

            # 从数据库重新查询，验证状态
            db.session.refresh(expired_relation)
            db.session.refresh(active_relation)

            assert expired_relation.status == 4  # 已过期
            assert active_relation.status == 1  # 仍然待处理