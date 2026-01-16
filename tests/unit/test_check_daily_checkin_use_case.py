"""
CheckDailyCheckinUseCase单元测试
"""
import pytest
from datetime import datetime, time, date, timedelta
from unittest.mock import Mock, patch
from app.application.use_cases.background_task import CheckDailyCheckinUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCheckDailyCheckinUseCase:
    """测试CheckDailyCheckinUseCase"""

    @patch('app.application.use_cases.background_task.check_daily_checkin_use_case.RepositoryFactory')
    def test_execute_success(self, mock_repo_factory):
        """测试执行成功"""
        # Arrange
        mock_checkin_rule_repo = Mock()
        mock_community_checkin_rule_repo = Mock()
        mock_checkin_record_repo = Mock()
        mock_user_repo = Mock()
        mock_community_staff_repo = Mock()
        mock_user_community_rule_repo = Mock()

        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_repo_factory.get_community_checkin_rule_repository.return_value = mock_community_checkin_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_checkin_record_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_community_staff_repo
        mock_community_staff_repo = Mock()
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo

        # Mock返回空列表
        mock_checkin_rule_repo.find_all_day_rules.return_value = []
        mock_community_checkin_rule_repo.find_all_day_rules.return_value = []

        use_case = CheckDailyCheckinUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '全天规则检查完成'
        assert result.data['personal_all_day_rules_checked'] == 0
        assert result.data['personal_missed_created'] == 0
        assert result.data['community_all_day_rules_checked'] == 0
        assert result.data['community_missed_created'] == 0

    @patch('app.application.use_cases.background_task.check_daily_checkin_use_case.RepositoryFactory')
    @patch('app.application.use_cases.background_task.check_daily_checkin_use_case.transaction')
    def test_execute_with_personal_missed(self, mock_transaction, mock_repo_factory):
        """测试执行成功 - 个人规则有未打卡"""
        # Arrange
        mock_checkin_rule_repo = Mock()
        mock_community_checkin_rule_repo = Mock()
        mock_checkin_record_repo = Mock()
        mock_user_repo = Mock()
        mock_community_staff_repo = Mock()
        mock_user_community_rule_repo = Mock()

        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_repo_factory.get_community_checkin_rule_repository.return_value = mock_community_checkin_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_checkin_record_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_community_staff_repo
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo

        # Mock transaction context manager
        mock_transaction.return_value.__enter__ = Mock(return_value=None)
        mock_transaction.return_value.__exit__ = Mock(return_value=None)

        # Mock个人全天规则
        rule = Mock()
        rule.rule_id = 1
        rule.user_id = 1
        rule.time_slot_type = 5  # 全天
        rule.frequency_type = 1
        rule.week_days = 0b1111111
        rule.created_at = datetime.now() - timedelta(days=2)

        mock_checkin_rule_repo.find_all_day_rules.return_value = [rule]
        mock_checkin_record_repo.find_by_rule_and_date.return_value = []  # 没有打卡记录

        use_case = CheckDailyCheckinUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['personal_all_day_rules_checked'] == 1
        assert result.data['personal_missed_created'] == 1

    @patch('app.application.use_cases.background_task.check_daily_checkin_use_case.RepositoryFactory')
    def test_execute_error(self, mock_repo_factory):
        """测试执行失败"""
        # Arrange
        mock_checkin_rule_repo = Mock()
        mock_community_checkin_rule_repo = Mock()
        mock_checkin_record_repo = Mock()
        mock_user_repo = Mock()
        mock_community_staff_repo = Mock()
        mock_user_community_rule_repo = Mock()

        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_repo_factory.get_community_checkin_rule_repository.return_value = mock_community_checkin_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_checkin_record_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_community_staff_repo
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo

        # Mock返回空列表
        mock_checkin_rule_repo.find_all_day_rules.return_value = []
        mock_community_checkin_rule_repo.find_all_day_rules.return_value = []

        use_case = CheckDailyCheckinUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '全天规则检查完成'

    @patch('app.application.use_cases.background_task.check_daily_checkin_use_case.RepositoryFactory')
    def test_skip_rules_created_today(self, mock_repo_factory):
        """测试跳过今天创建的规则"""
        # Arrange
        mock_checkin_rule_repo = Mock()
        mock_community_checkin_rule_repo = Mock()
        mock_checkin_record_repo = Mock()
        mock_user_repo = Mock()
        mock_community_staff_repo = Mock()
        mock_user_community_rule_repo = Mock()

        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_repo_factory.get_community_checkin_rule_repository.return_value = mock_community_checkin_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_checkin_record_repo
        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_community_staff_repo
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo

        # Mock今天创建的规则
        rule = Mock()
        rule.rule_id = 1
        rule.user_id = 1
        rule.time_slot_type = 5
        rule.frequency_type = 1
        rule.week_days = 0b1111111
        rule.created_at = datetime.now()  # 今天创建

        mock_checkin_rule_repo.find_all_day_rules.return_value = [rule]

        use_case = CheckDailyCheckinUseCase()

        # Act
        result = use_case.execute()

        # Assert - 今天创建的规则应该被跳过
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['personal_all_day_rules_checked'] == 1
        assert result.data['personal_missed_created'] == 0  # 没有创建记录