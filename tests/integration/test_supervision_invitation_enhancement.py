"""
监督邀请功能增强集成测试
测试新增的API端点：撤回邀请、批量拒绝邀请、获取待处理邀请数量
"""
import json
import pytest
from tests.integration.conftest import IntegrationTestBase


class TestSupervisionInvitationEnhancement(IntegrationTestBase):
    """监督邀请功能增强集成测试"""

    def create_checkin_rule_for_user(self, user_id):
        """为用户创建打卡规则"""
        from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
        from tests.test_data_generator import generate_unique_nickname

        create_rule_use_case = CreateCheckinRuleUseCase()
        result = create_rule_use_case.execute(
            user_id=user_id,
            rule_data={
                'rule_name': f'测试规则_{generate_unique_nickname()}',
                'rule_type': 'daily',
                'custom_time': '08:00',
                'week_days': 127,
                'timezone': 'Asia/Shanghai',
                'status': 1
            }
        )

        if not result.is_success:
            raise Exception(f'创建打卡规则失败: {result.message}')

        return result.data['rule'].rule_id

    def test_withdraw_invitation_success(self):
        """测试成功撤回邀请"""
        with self.app.app_context():
            inviter = self.create_standard_test_user(role=1, test_context='withdraw_inviter')
            supervisor = self.create_standard_test_user(role=1, test_context='withdraw_supervisor')
            self.db.session.commit()

            rule_id = self.create_checkin_rule_for_user(inviter.user_id)
            inviter_phone = inviter.phone_number
            supervisor_user_id = supervisor.user_id

        client = self.get_test_client()

        # 邀请者邀请监督者
        inviter_token = self.get_jwt_token(inviter_phone)
        invite_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        invite_data = self.assert_api_success(invite_response)
        relation_id = invite_data['data']['relation_ids'][0]

        # 撤回邀请
        withdraw_response = client.post(
            f'/api/supervision/invitations/{relation_id}/withdraw',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        # 验证撤回成功
        withdraw_data = self.assert_api_success(withdraw_response)
        assert withdraw_data['data']['invitation_id'] == relation_id
        assert 'withdrawn_at' in withdraw_data['data']

    def test_withdraw_invitation_forbidden(self):
        """测试无权限撤回邀请"""
        with self.app.app_context():
            inviter = self.create_standard_test_user(role=1, test_context='withdraw_forbidden_inviter')
            supervisor = self.create_standard_test_user(role=1, test_context='withdraw_forbidden_supervisor')
            other_user = self.create_standard_test_user(role=1, test_context='withdraw_forbidden_other')
            self.db.session.commit()

            rule_id = self.create_checkin_rule_for_user(inviter.user_id)
            inviter_phone = inviter.phone_number
            supervisor_user_id = supervisor.user_id
            other_phone = other_user.phone_number

        client = self.get_test_client()

        # 邀请者邀请监督者
        inviter_token = self.get_jwt_token(inviter_phone)
        invite_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        invite_data = self.assert_api_success(invite_response)
        relation_id = invite_data['data']['relation_ids'][0]

        # 其他用户尝试撤回邀请（应该失败）
        other_token = self.get_jwt_token(other_phone)
        withdraw_response = client.post(
            f'/api/supervision/invitations/{relation_id}/withdraw',
            headers={'Authorization': f'Bearer {other_token}'}
        )

        # 验证撤回失败
        self.assert_api_error(withdraw_response)
        assert '您不是该邀请的发起者' in withdraw_response.json['msg']

    def test_batch_reject_invitations_success(self):
        """测试批量拒绝邀请成功"""
        with self.app.app_context():
            inviter1 = self.create_standard_test_user(role=1, test_context='batch_reject_inviter1')
            inviter2 = self.create_standard_test_user(role=1, test_context='batch_reject_inviter2')
            supervisor = self.create_standard_test_user(role=1, test_context='batch_reject_supervisor')
            self.db.session.commit()

            rule_id1 = self.create_checkin_rule_for_user(inviter1.user_id)
            rule_id2 = self.create_checkin_rule_for_user(inviter2.user_id)
            supervisor_phone = supervisor.phone_number
            inviter1_phone = inviter1.phone_number
            inviter2_phone = inviter2.phone_number
            supervisor_user_id = supervisor.user_id

        client = self.get_test_client()

        # 创建两个邀请
        inviter1_token = self.get_jwt_token(inviter1_phone)
        invite1_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id1,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡1'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter1_token}'}
        )

        inviter2_token = self.get_jwt_token(inviter2_phone)
        invite2_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id2,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡2'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter2_token}'}
        )

        invite1_data = self.assert_api_success(invite1_response)
        invite2_data = self.assert_api_success(invite2_response)
        invitation_ids = [
            invite1_data['data']['relation_ids'][0],
            invite2_data['data']['relation_ids'][0]
        ]

        # 批量拒绝邀请
        supervisor_token = self.get_jwt_token(supervisor_phone)
        batch_reject_response = client.post(
            '/api/supervision/invitations/batch-reject',
            data=json.dumps({
                'invitation_ids': invitation_ids
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {supervisor_token}'}
        )

        # 验证批量拒绝成功
        batch_reject_data = self.assert_api_success(batch_reject_response)
        assert batch_reject_data['data']['rejected_count'] == 2
        assert batch_reject_data['data']['failed_count'] == 0

    def test_batch_reject_invitations_partial_failure(self):
        """测试批量拒绝邀请部分失败"""
        with self.app.app_context():
            inviter = self.create_standard_test_user(role=1, test_context='batch_reject_partial_inviter')
            supervisor = self.create_standard_test_user(role=1, test_context='batch_reject_partial_supervisor')
            self.db.session.commit()

            rule_id = self.create_checkin_rule_for_user(inviter.user_id)
            supervisor_phone = supervisor.phone_number
            inviter_phone = inviter.phone_number
            supervisor_user_id = supervisor.user_id

        client = self.get_test_client()

        # 创建一个邀请
        inviter_token = self.get_jwt_token(inviter_phone)
        invite_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        invite_data = self.assert_api_success(invite_response)
        valid_invitation_id = invite_data['data']['relation_ids'][0]

        # 尝试批量拒绝，包含一个不存在的邀请ID
        supervisor_token = self.get_jwt_token(supervisor_phone)
        batch_reject_response = client.post(
            '/api/supervision/invitations/batch-reject',
            data=json.dumps({
                'invitation_ids': [valid_invitation_id, 99999]
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {supervisor_token}'}
        )

        # 验证部分失败
        batch_reject_data = self.assert_api_success(batch_reject_response)
        assert batch_reject_data['data']['rejected_count'] == 1
        assert batch_reject_data['data']['failed_count'] == 1
        assert 99999 in batch_reject_data['data']['failed_ids']

    def test_get_pending_invitations_count_success(self):
        """测试获取待处理邀请数量成功"""
        with self.app.app_context():
            inviter = self.create_standard_test_user(role=1, test_context='pending_count_inviter')
            supervisor = self.create_standard_test_user(role=1, test_context='pending_count_supervisor')
            self.db.session.commit()

            rule_id = self.create_checkin_rule_for_user(inviter.user_id)
            supervisor_phone = supervisor.phone_number
            inviter_phone = inviter.phone_number
            supervisor_user_id = supervisor.user_id

        client = self.get_test_client()

        # 创建邀请
        inviter_token = self.get_jwt_token(inviter_phone)
        invite_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        # 获取待处理邀请数量
        supervisor_token = self.get_jwt_token(supervisor_phone)
        count_response = client.get(
            '/api/supervision/invitations/pending-count',
            headers={'Authorization': f'Bearer {supervisor_token}'}
        )

        # 验证获取成功
        count_data = self.assert_api_success(count_response)
        assert count_data['data']['pending_count'] == 1

    def test_get_pending_invitations_count_zero(self):
        """测试无待处理邀请时返回0"""
        with self.app.app_context():
            supervisor = self.create_standard_test_user(role=1, test_context='pending_count_zero')
            self.db.session.commit()

            supervisor_phone = supervisor.phone_number

        client = self.get_test_client()

        # 获取待处理邀请数量
        supervisor_token = self.get_jwt_token(supervisor_phone)
        count_response = client.get(
            '/api/supervision/invitations/pending-count',
            headers={'Authorization': f'Bearer {supervisor_token}'}
        )

        # 验证返回0
        count_data = self.assert_api_success(count_response)
        assert count_data['data']['pending_count'] == 0

    def test_withdraw_after_accept_fails(self):
        """测试接受邀请后撤回应该失败"""
        with self.app.app_context():
            inviter = self.create_standard_test_user(role=1, test_context='withdraw_after_accept_inviter')
            supervisor = self.create_standard_test_user(role=1, test_context='withdraw_after_accept_supervisor')
            self.db.session.commit()

            rule_id = self.create_checkin_rule_for_user(inviter.user_id)
            inviter_phone = inviter.phone_number
            supervisor_phone = supervisor.phone_number
            supervisor_user_id = supervisor.user_id

        client = self.get_test_client()

        # 邀请者邀请监督者
        inviter_token = self.get_jwt_token(inviter_phone)
        invite_response = client.post(
            '/api/supervision/invite/internal',
            data=json.dumps({
                'rule_id': rule_id,
                'receiver_ids': [supervisor_user_id],
                'message': '请监督我的打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        invite_data = self.assert_api_success(invite_response)
        relation_id = invite_data['data']['relation_ids'][0]

        # 监督者接受邀请
        supervisor_token = self.get_jwt_token(supervisor_phone)
        accept_response = client.post(
            f'/api/supervision/invitations/{relation_id}/accept',
            headers={'Authorization': f'Bearer {supervisor_token}'}
        )

        self.assert_api_success(accept_response)

        # 尝试撤回已接受的邀请（应该失败）
        withdraw_response = client.post(
            f'/api/supervision/invitations/{relation_id}/withdraw',
            headers={'Authorization': f'Bearer {inviter_token}'}
        )

        # 验证撤回失败
        self.assert_api_error(withdraw_response)
        assert '邀请状态不允许撤回' in withdraw_response.json['msg']