"""
监督模块UseCase单元测试
专注于测试UseCase的业务逻辑，使用Mock隔离依赖
"""
import pytest
from datetime import datetime, date
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.supervision.get_supervised_users_use_case import GetSupervisedUsersUseCase
from app.application.use_cases.supervision.get_guardians_use_case import GetGuardiansUseCase
from app.application.use_cases.supervision.get_supervision_records_use_case import GetSupervisionRecordsUseCase
from app.application.use_cases.supervision.get_today_supervision_data_use_case import GetTodaySupervisionDataUseCase
from app.application.use_cases.supervision.send_internal_invitation_use_case import SendInternalInvitationUseCase
from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetSupervisedUsersUseCase:
    """测试GetSupervisedUsersUseCase"""

    @patch('app.application.use_cases.supervision.get_supervised_users_use_case.RepositoryFactory')
    def test_should_successfully_get_supervised_users(self, mock_repo_factory):
        """应该成功获取被监督用户列表"""
        # Arrange
        mock_user_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        relation1 = Mock()
        relation1.solo_user_id = 2
        relation1.rule_id = 101
        relation2 = Mock()
        relation2.solo_user_id = 3
        relation2.rule_id = 102

        mock_relation_repo.find_by_supervisor_id.return_value = [relation1, relation2]

        supervised_user1 = Mock()
        supervised_user1.user_id = 2
        supervised_user1.nickname = 'User2'
        supervised_user1.avatar_url = 'avatar2.jpg'
        supervised_user2 = Mock()
        supervised_user2.user_id = 3
        supervised_user2.nickname = 'User3'
        supervised_user2.avatar_url = 'avatar3.jpg'

        mock_user_repo.find_by_id.side_effect = lambda id: supervised_user1 if id == 2 else supervised_user2

        use_case = GetSupervisedUsersUseCase()

        # Act
        result = use_case.execute(
            supervisor_id=1,
            page=1,
            page_size=20
        )

        # Assert
        assert result.is_success
        assert result.data['total'] == 2
        assert len(result.data['supervised_users']) == 2
        assert result.data['supervised_users'][0]['user_id'] == 2
        assert result.data['supervised_users'][1]['user_id'] == 3

    def test_should_fail_when_supervisor_id_is_empty(self):
        """应该在监督者ID为空时失败"""
        # Arrange
        use_case = GetSupervisedUsersUseCase()

        # Act
        result = use_case.execute(
            supervisor_id=None,
            page=1,
            page_size=20
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '监督者ID不能为空' in result.message

    def test_should_fail_when_page_is_invalid(self):
        """应该在页码无效时失败"""
        # Arrange
        use_case = GetSupervisedUsersUseCase()

        # Act
        result = use_case.execute(
            supervisor_id=1,
            page=0,
            page_size=20
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '页码必须大于0' in result.message

    def test_should_fail_when_page_size_is_invalid(self):
        """应该在每页数量无效时失败"""
        # Arrange
        use_case = GetSupervisedUsersUseCase()

        # Act
        result = use_case.execute(
            supervisor_id=1,
            page=1,
            page_size=150
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '每页数量必须在1-100之间' in result.message


class TestGetGuardiansUseCase:
    """测试GetGuardiansUseCase"""

    @patch('app.application.use_cases.supervision.get_guardians_use_case.RepositoryFactory')
    def test_should_successfully_get_guardians(self, mock_repo_factory):
        """应该成功获取监督者列表"""
        # Arrange
        mock_user_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        relation1 = Mock()
        relation1.supervisor_user_id = 1
        relation1.rule_id = 101
        relation2 = Mock()
        relation2.supervisor_user_id = 2
        relation2.rule_id = 102

        mock_relation_repo.find_by_solo_user_id.return_value = [relation1, relation2]

        guardian1 = Mock()
        guardian1.user_id = 1
        guardian1.nickname = 'Guardian1'
        guardian1.avatar_url = 'avatar1.jpg'
        guardian2 = Mock()
        guardian2.user_id = 2
        guardian2.nickname = 'Guardian2'
        guardian2.avatar_url = 'avatar2.jpg'

        mock_user_repo.find_by_id.side_effect = lambda id: guardian1 if id == 1 else guardian2

        use_case = GetGuardiansUseCase()

        # Act
        result = use_case.execute(
            supervised_id=3,
            page=1,
            page_size=20
        )

        # Assert
        assert result.is_success
        assert result.data['total'] == 2
        assert len(result.data['guardians']) == 2
        assert result.data['guardians'][0]['user_id'] == 1
        assert result.data['guardians'][1]['user_id'] == 2

    def test_should_fail_when_supervised_id_is_empty(self):
        """应该在被监督用户ID为空时失败"""
        # Arrange
        use_case = GetGuardiansUseCase()

        # Act
        result = use_case.execute(
            supervised_id=None,
            page=1,
            page_size=20
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '被监督用户ID不能为空' in result.message


class TestGetSupervisionRecordsUseCase:
    """测试GetSupervisionRecordsUseCase"""

    @patch('app.application.use_cases.supervision.get_supervision_records_use_case.RepositoryFactory')
    def test_should_successfully_get_supervision_records(self, mock_repo_factory):
        """应该成功获取监督记录"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()
        mock_record_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_record_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        supervisor = Mock()
        supervisor.user_id = 1
        supervisor.nickname = 'Supervisor'

        supervised_user = Mock()
        supervised_user.user_id = 2
        supervised_user.nickname = 'Supervised'

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Test Rule'

        relation = Mock()
        relation.solo_user_id = 2
        relation.rule_id = 101

        record = Mock()
        record.record_id = 1001
        record.user_id = 2
        record.checkin_time = datetime(2026, 1, 15, 10, 30)
        record.status = 1
        record.created_at = datetime(2026, 1, 15, 10, 30)
        record.planned_time = datetime(2026, 1, 15, 10, 0)

        mock_user_repo.find_by_id.side_effect = lambda id: supervisor if id == 1 else supervised_user
        mock_relation_repo.find_by_supervisor_id.return_value = [relation]
        mock_rule_repo.find_by_id.return_value = rule
        mock_record_repo.find_by_rule_id.return_value = [record]

        use_case = GetSupervisionRecordsUseCase()

        # Act
        result = use_case.execute(
            user_id=1,
            start_date='2026-01-01',
            end_date='2026-01-31',
            page=1,
            page_size=20
        )

        # Assert
        assert result.is_success
        assert result.data['total'] == 1
        assert len(result.data['records']) == 1
        assert result.data['records'][0]['record_id'] == 1001
        assert result.data['records'][0]['status'] == 'completed'


class TestGetTodaySupervisionDataUseCase:
    """测试GetTodaySupervisionDataUseCase"""

    @patch('app.application.use_cases.supervision.get_today_supervision_data_use_case.RepositoryFactory')
    def test_should_successfully_get_today_supervision_data(self, mock_repo_factory):
        """应该成功获取今日监护数据"""
        # Arrange
        mock_user_repo = Mock()
        mock_relation_repo = Mock()
        mock_rule_repo = Mock()
        mock_record_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_record_repo

        supervised_user = Mock()
        supervised_user.user_id = 2
        supervised_user.nickname = 'Supervised'
        supervised_user.avatar_url = 'avatar2.jpg'

        relation = Mock()
        relation.relation_id = 1001
        relation.solo_user_id = 2
        relation.rule_id = 101
        relation.status = 2  # 已激活

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Test Rule'
        rule.custom_time = datetime(2026, 1, 15, 10, 0).time()

        checkin_record = Mock()
        checkin_record.checkin_time = datetime(2026, 1, 15, 9, 30)

        mock_user_repo.find_by_id.return_value = supervised_user
        mock_relation_repo.find_by_supervisor_id.return_value = [relation]
        mock_rule_repo.find_by_id.return_value = rule
        mock_record_repo.get_today_checkin.return_value = checkin_record

        use_case = GetTodaySupervisionDataUseCase()

        # Act
        result = use_case.execute(
            supervisor_id=1,
            target_date=date(2026, 1, 15)
        )

        # Assert
        assert result.is_success
        assert len(result.data['supervised_users']) == 1
        assert result.data['supervised_users'][0]['user_id'] == 2
        assert result.data['supervised_users'][0]['rules'][0]['today_status'] == 'completed'


class TestSendInternalInvitationUseCase:
    """测试SendInternalInvitationUseCase"""

    @patch('app.application.use_cases.supervision.send_internal_invitation_use_case.RepositoryFactory')
    def test_should_successfully_send_internal_invitation(self, mock_repo_factory):
        """应该成功发送站内邀请"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        sender = Mock()
        sender.user_id = 1
        sender.nickname = 'Sender'

        receiver = Mock()
        receiver.user_id = 2

        rule = Mock()
        rule.rule_id = 101
        rule.user_id = 1
        rule.rule_name = 'Test Rule'

        mock_user_repo.find_by_id.side_effect = lambda id: sender if id == 1 else receiver
        mock_rule_repo.find_by_id.return_value = rule
        mock_relation_repo.find_by_users_and_rule.return_value = None
        mock_relation_repo.find_active_relation.return_value = None

        saved_relation = Mock()
        saved_relation.relation_id = 1001
        mock_relation_repo.save.return_value = saved_relation

        use_case = SendInternalInvitationUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            rule_id=101,
            receiver_ids=[2],
            message='Please supervise me'
        )

        # Assert
        assert result.is_success
        assert result.data['sender_id'] == 1
        assert result.data['receiver_ids'] == [2]
        assert result.data['invitation_type'] == 'internal'
        mock_relation_repo.save.assert_called_once()

    def test_should_fail_when_inviting_self(self):
        """应该在邀请自己时失败"""
        # Arrange
        use_case = SendInternalInvitationUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            rule_id=101,
            receiver_ids=[1]
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '不能邀请自己' in result.message

    def test_should_fail_when_receivers_exceed_limit(self):
        """应该在接收者数量超过限制时失败"""
        # Arrange
        use_case = SendInternalInvitationUseCase()

        # Act
        result = use_case.execute(
            sender_id=1,
            rule_id=101,
            receiver_ids=[2, 3, 4, 5]  # 4个接收者，超过限制
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '一次最多只能邀请3个用户' in result.message


class TestInvitationManagementUseCase:
    """测试InvitationManagementUseCase"""

    @patch('app.application.use_cases.supervision.invitation_management_use_case.RepositoryFactory')
    def test_should_successfully_accept_invitation(self, mock_repo_factory):
        """应该成功接受邀请"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 1001
        invitation.supervisor_user_id = 2
        invitation.solo_user_id = 1
        invitation.rule_id = 101
        invitation.status = 1
        invitation.invite_expires_at = datetime(2026, 2, 15, 10, 0)

        mock_relation_repo.find_by_id.return_value = invitation

        service = InvitationManagementUseCase()

        # Act
        result = service.accept_invitation(
            invitation_id=1001,
            user_id=2
        )

        # Assert
        assert result.is_success
        assert invitation.status == 2
        mock_relation_repo.update.assert_called_once()

    @patch('app.application.use_cases.supervision.invitation_management_use_case.RepositoryFactory')
    def test_should_fail_when_accepting_already_accepted_invitation(self, mock_repo_factory):
        """应该在接受已接受的邀请时失败"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 1001
        invitation.supervisor_user_id = 2
        invitation.status = 2  # 已接受

        mock_relation_repo.find_by_id.return_value = invitation

        service = InvitationManagementUseCase()

        # Act
        result = service.accept_invitation(
            invitation_id=1001,
            user_id=2
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '您已经接受过该邀请' in result.message

    @patch('app.application.use_cases.supervision.invitation_management_use_case.RepositoryFactory')
    def test_should_successfully_reject_invitation(self, mock_repo_factory):
        """应该成功拒绝邀请"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 1001
        invitation.supervisor_user_id = 2
        invitation.status = 1
        invitation.invite_expires_at = datetime(2026, 2, 15, 10, 0)

        mock_relation_repo.find_by_id.return_value = invitation

        service = InvitationManagementUseCase()

        # Act
        result = service.reject_invitation(
            invitation_id=1001,
            user_id=2,
            reason='Not interested'
        )

        # Assert
        assert result.is_success
        assert invitation.status == 3
        mock_relation_repo.update.assert_called_once()

    @patch('app.application.use_cases.supervision.invitation_management_use_case.RepositoryFactory')
    def test_should_successfully_ignore_invitation(self, mock_repo_factory):
        """应该成功忽略邀请"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation = Mock()
        invitation.relation_id = 1001
        invitation.supervisor_user_id = 2
        invitation.status = 1
        invitation.invite_expires_at = datetime(2026, 2, 15, 10, 0)

        mock_relation_repo.find_by_id.return_value = invitation
        mock_relation_repo.delete.return_value = True

        service = InvitationManagementUseCase()

        # Act
        result = service.ignore_invitation(
            invitation_id=1001,
            user_id=2
        )

        # Assert
        assert result.is_success
        mock_relation_repo.delete.assert_called_once_with(1001)

    @patch('app.application.use_cases.supervision.invitation_management_use_case.RepositoryFactory')
    def test_should_successfully_batch_accept_invitations(self, mock_repo_factory):
        """应该成功批量接受邀请"""
        # Arrange
        mock_relation_repo = Mock()
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        invitation1 = Mock()
        invitation1.relation_id = 1001
        invitation1.supervisor_user_id = 2
        invitation1.status = 1
        invitation1.invite_expires_at = datetime(2026, 2, 15, 10, 0)

        invitation2 = Mock()
        invitation2.relation_id = 1002
        invitation2.supervisor_user_id = 2
        invitation2.status = 1
        invitation2.invite_expires_at = datetime(2026, 2, 15, 10, 0)

        mock_relation_repo.find_by_id.side_effect = [invitation1, invitation2]

        service = InvitationManagementUseCase()

        # Act
        result = service.batch_accept_invitations(
            invitation_ids=[1001, 1002],
            user_id=2
        )

        # Assert
        assert result.is_success
        assert result.data['accepted_count'] == 2
        assert result.data['failed_count'] == 0