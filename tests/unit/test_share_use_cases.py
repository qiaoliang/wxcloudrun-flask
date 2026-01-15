"""
分享链接模块UseCase单元测试
专注于测试UseCase的业务逻辑，使用Mock隔离依赖
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.application.use_cases.share.create_share_link_use_case import CreateShareLinkUseCase
from app.application.use_cases.share.resolve_share_link_use_case import ResolveShareLinkUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCreateShareLinkUseCase:
    """测试CreateShareLinkUseCase"""

    @patch('app.application.use_cases.share.create_share_link_use_case.RepositoryFactory')
    @patch('app.application.use_cases.share.create_share_link_use_case.qrcode')
    def test_should_successfully_create_share_link(self, mock_qrcode, mock_repo_factory):
        """应该成功创建分享链接"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()
        mock_share_link_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_share_link_repository.return_value = mock_share_link_repo

        user = Mock()
        user.user_id = 1
        rule = Mock()
        rule.rule_id = 101
        rule.user_id = 1

        mock_user_repo.find_by_id.return_value = user
        mock_rule_repo.find_by_id.return_value = rule

        saved_link = Mock()
        saved_link.token = 'test_token_123'
        saved_link.rule_id = 101
        saved_link.solo_user_id = 1
        saved_link.expires_at = datetime.now() + timedelta(hours=168)
        mock_share_link_repo.save.return_value = saved_link

        # Mock qrcode
        mock_qr_instance = Mock()
        mock_qr_instance.make.return_value = None
        mock_qr_instance.make_image.return_value = Mock()
        mock_qrcode.QRCode.return_value = mock_qr_instance

        use_case = CreateShareLinkUseCase()

        # Act
        result = use_case.execute(
            user_id=1,
            rule_id=101,
            expire_hours=168
        )

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['token'] == 'test_token_123'
        assert result.data['rule_id'] == 101
        mock_share_link_repo.save.assert_called_once()

    @patch('app.application.use_cases.share.create_share_link_use_case.RepositoryFactory')
    def test_should_fail_when_user_not_found(self, mock_repo_factory):
        """应该在用户不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_user_repo.find_by_id.return_value = None

        use_case = CreateShareLinkUseCase()

        # Act
        result = use_case.execute(
            user_id=999,
            rule_id=101,
            expire_hours=168
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不存在' in result.message

    @patch('app.application.use_cases.share.create_share_link_use_case.RepositoryFactory')
    def test_should_fail_when_rule_not_found(self, mock_repo_factory):
        """应该在规则不存在时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user
        mock_rule_repo.find_by_id.return_value = None

        use_case = CreateShareLinkUseCase()

        # Act
        result = use_case.execute(
            user_id=1,
            rule_id=999,
            expire_hours=168
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '打卡规则不存在' in result.message

    @patch('app.application.use_cases.share.create_share_link_use_case.RepositoryFactory')
    def test_should_fail_when_no_permission(self, mock_repo_factory):
        """应该在无权限时失败"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        user = Mock()
        user.user_id = 1
        rule = Mock()
        rule.rule_id = 101
        rule.user_id = 999  # 规则不属于用户

        mock_user_repo.find_by_id.return_value = user
        mock_rule_repo.find_by_id.return_value = rule

        use_case = CreateShareLinkUseCase()

        # Act
        result = use_case.execute(
            user_id=1,
            rule_id=101,
            expire_hours=168
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FORBIDDEN
        assert '无权限操作此打卡规则' in result.message

    def test_should_fail_when_expire_hours_invalid(self):
        """应该在过期时间无效时失败"""
        # Arrange
        use_case = CreateShareLinkUseCase()

        # Act - 过期时间太短
        result = use_case.execute(
            user_id=1,
            rule_id=101,
            expire_hours=0
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR

        # Act - 过期时间太长
        result = use_case.execute(
            user_id=1,
            rule_id=101,
            expire_hours=1000
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR


class TestResolveShareLinkUseCase:
    """测试ResolveShareLinkUseCase"""

    @patch('app.application.use_cases.share.resolve_share_link_use_case.RepositoryFactory')
    def test_should_successfully_resolve_share_link(self, mock_repo_factory):
        """应该成功解析分享链接"""
        # Arrange
        mock_share_link_repo = Mock()
        mock_rule_repo = Mock()
        mock_user_repo = Mock()
        mock_access_log_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_share_link_repository.return_value = mock_share_link_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_share_link_access_log_repository.return_value = mock_access_log_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        link = Mock()
        link.token = 'test_token_123'
        link.rule_id = 101
        link.solo_user_id = 1
        link.expires_at = datetime.now() + timedelta(hours=168)

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Test Rule'
        rule.custom_time = datetime(2026, 1, 15, 10, 0).time()
        rule.status = 1

        user = Mock()
        user.user_id = 1
        user.nickname = 'Test User'
        user.avatar_url = 'avatar.jpg'

        mock_share_link_repo.find_by_token.return_value = link
        mock_rule_repo.find_by_id.return_value = rule
        mock_user_repo.find_by_id.return_value = user
        mock_relation_repo.find_active_relation.return_value = None

        use_case = ResolveShareLinkUseCase()

        # Act
        result = use_case.execute(
            token='test_token_123',
            ip_address='127.0.0.1',
            user_agent='Test Agent',
            current_user_id=2
        )

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['rule_info']['rule_id'] == 101
        assert result.data['inviter_info']['user_id'] == 1
        assert result.data['is_expired'] == False
        assert result.data['is_already_supervisor'] == False

    @patch('app.application.use_cases.share.resolve_share_link_use_case.RepositoryFactory')
    def test_should_fail_when_token_not_found(self, mock_repo_factory):
        """应该在token不存在时失败"""
        # Arrange
        mock_share_link_repo = Mock()
        mock_repo_factory.get_share_link_repository.return_value = mock_share_link_repo
        mock_share_link_repo.find_by_token.return_value = None

        use_case = ResolveShareLinkUseCase()

        # Act
        result = use_case.execute(
            token='invalid_token'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '分享链接不存在' in result.message

    @patch('app.application.use_cases.share.resolve_share_link_use_case.RepositoryFactory')
    def test_should_fail_when_link_expired(self, mock_repo_factory):
        """应该在链接过期时失败"""
        # Arrange
        mock_share_link_repo = Mock()
        mock_repo_factory.get_share_link_repository.return_value = mock_share_link_repo

        link = Mock()
        link.token = 'test_token_123'
        link.expires_at = datetime.now() - timedelta(hours=1)  # 已过期

        mock_share_link_repo.find_by_token.return_value = link

        use_case = ResolveShareLinkUseCase()

        # Act
        result = use_case.execute(
            token='test_token_123'
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert '分享链接已过期' in result.message

    def test_should_fail_when_token_is_empty(self):
        """应该在token为空时失败"""
        # Arrange
        use_case = ResolveShareLinkUseCase()

        # Act
        result = use_case.execute(
            token=''
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert 'token不能为空' in result.message

    @patch('app.application.use_cases.share.resolve_share_link_use_case.RepositoryFactory')
    def test_should_detect_existing_supervisor(self, mock_repo_factory):
        """应该检测到已存在的监督关系"""
        # Arrange
        mock_share_link_repo = Mock()
        mock_rule_repo = Mock()
        mock_user_repo = Mock()
        mock_relation_repo = Mock()

        mock_repo_factory.get_share_link_repository.return_value = mock_share_link_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_supervision_relation_repository.return_value = mock_relation_repo

        link = Mock()
        link.token = 'test_token_123'
        link.rule_id = 101
        link.solo_user_id = 1
        link.expires_at = datetime.now() + timedelta(hours=168)

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Test Rule'
        rule.custom_time = datetime(2026, 1, 15, 10, 0).time()
        rule.status = 1

        user = Mock()
        user.user_id = 1
        user.nickname = 'Test User'
        user.avatar_url = 'avatar.jpg'

        mock_share_link_repo.find_by_token.return_value = link
        mock_rule_repo.find_by_id.return_value = rule
        mock_user_repo.find_by_id.return_value = user
        mock_relation_repo.find_active_relation.return_value = Mock()  # 已存在关系

        use_case = ResolveShareLinkUseCase()

        # Act
        result = use_case.execute(
            token='test_token_123',
            current_user_id=2
        )

        # Assert
        assert result.is_success
        assert result.data['is_already_supervisor'] == True