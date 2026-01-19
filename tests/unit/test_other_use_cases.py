"""
其他模块UseCase单元测试
专注于测试UseCase的业务逻辑，使用Mock隔离依赖
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.user.search_users_use_case import SearchUsersUseCase
from app.application.use_cases.misc.counter_use_case import CounterUseCase
from app.application.use_cases.misc.get_environments_use_case import GetEnvironmentsUseCase
from app.application.use_cases.user_checkin.get_user_all_rules_use_case import GetUserAllRulesUseCase
from app.application.use_cases.user_checkin.get_user_today_plan_use_case import GetUserTodayPlanUseCase
from app.application.use_cases.user_checkin.get_user_rule_detail_use_case import GetUserRuleDetailUseCase
from app.application.use_cases.user_checkin.get_user_checkin_statistics_use_case import GetUserCheckinStatisticsUseCase
from app.application.use_cases.user_checkin.get_rules_source_info_use_case import GetRulesSourceInfoUseCase
from app.application.use_cases.base import UseCaseStatus


class TestSearchUsersUseCase:
    """测试SearchUsersUseCase"""

    @patch('app.application.use_cases.user.search_users_use_case.RepositoryFactory')
    def test_should_successfully_search_users(self, mock_repo_factory):
        """应该成功搜索用户"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        user1 = Mock()
        user1.user_id = 1
        user1.nickname = 'User1'
        user1.name = 'Name1'
        user1.phone_number = '13800138001'
        user1.role = 1
        user1.role_name = '普通用户'
        user1.avatar_url = 'avatar1.jpg'
        user1.community_id = 1
        user1.community = Mock()
        user1.community.name = 'Community1'
        user1.created_at = None

        user2 = Mock()
        user2.user_id = 2
        user2.nickname = 'User2'
        user2.name = 'Name2'
        user2.phone_number = '13800138002'
        user2.role = 1
        user2.role_name = '普通用户'
        user2.avatar_url = 'avatar2.jpg'
        user2.community_id = 1
        user2.community = Mock()
        user2.community.name = 'Community1'
        user2.created_at = None

        mock_user_repo.search_users.return_value = [user1, user2]

        use_case = SearchUsersUseCase()

        # Act
        result = use_case.execute(
            keyword='User',
            page=1,
            page_size=20
        )

        # Assert
        assert result.is_success
        assert result.data['total'] == 2
        assert len(result.data['users']) == 2
        assert result.data['users'][0]['user_id'] == 1

    def test_should_fail_when_keyword_is_empty(self):
        """应该在关键词为空时失败"""
        # Arrange
        use_case = SearchUsersUseCase()

        # Act
        result = use_case.execute(
            keyword='',
            page=1,
            page_size=20
        )

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '搜索关键词不能为空' in result.message

    @patch('app.application.use_cases.user.search_users_use_case.RepositoryFactory')
    def test_should_filter_by_role(self, mock_repo_factory):
        """应该按角色筛选"""
        # Arrange
        mock_user_repo = Mock()
        mock_repo_factory.get_user_repository.return_value = mock_user_repo

        user1 = Mock()
        user1.user_id = 1
        user1.nickname = 'User1'
        user1.role = 1
        user1.role_name = '普通用户'
        user1.avatar_url = 'avatar1.jpg'
        user1.community = None
        user1.created_at = None

        user2 = Mock()
        user2.user_id = 2
        user2.nickname = 'User2'
        user2.role = 2
        user2.role_name = '工作人员'
        user2.avatar_url = 'avatar2.jpg'
        user2.community = None
        user2.created_at = None

        mock_user_repo.search_users.return_value = [user1, user2]

        use_case = SearchUsersUseCase()

        # Act
        result = use_case.execute(
            keyword='User',
            role=1,
            page=1,
            page_size=20
        )

        # Assert
        assert result.is_success
        assert result.data['total'] == 1
        assert result.data['users'][0]['role'] == 1


class TestGetUserAllRulesUseCase:
    """测试GetUserAllRulesUseCase"""

    @patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.RepositoryFactory')
    def test_should_successfully_get_user_all_rules(self, mock_repo_factory):
        """应该成功获取用户所有规则"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        rule1 = Mock()
        rule1.rule_id = 101
        rule1.rule_name = 'Rule1'
        rule1.rule_type = 'personal'
        rule1.status = 1
        rule1.to_dict.return_value = {
            'rule_id': 101,
            'rule_name': 'Rule1',
            'rule_type': 'personal',
            'status': 1
        }

        rule2 = Mock()
        rule2.rule_id = 102
        rule2.rule_name = 'Rule2'
        rule2.rule_type = 'personal'
        rule2.status = 1
        rule2.to_dict.return_value = {
            'rule_id': 102,
            'rule_name': 'Rule2',
            'rule_type': 'personal',
            'status': 1
        }

        mock_rule_repo.find_active_by_user_id.return_value = [rule1, rule2]

        use_case = GetUserAllRulesUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert len(result.data['rules']) == 2


class TestGetUserTodayPlanUseCase:
    """测试GetUserTodayPlanUseCase"""

    def test_should_successfully_get_user_today_plan(self, test_session, test_user, test_community):
        """应该成功获取用户今日计划"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()
        mock_record_repo = Mock()
        mock_user_community_rule_repo = Mock()

        # Use monkeypatch to replace RepositoryFactory methods
        from app.application.use_cases.user_checkin import get_user_today_plan_use_case
        monkeypatch.setattr(get_user_today_plan_use_case.RepositoryFactory, 'get_user_repository', Mock(return_value=mock_user_repo))
        monkeypatch.setattr(get_user_today_plan_use_case.RepositoryFactory, 'get_checkin_rule_repository', Mock(return_value=mock_rule_repo))
        monkeypatch.setattr(get_user_today_plan_use_case.RepositoryFactory, 'get_checkin_record_repository', Mock(return_value=mock_record_repo))
        monkeypatch.setattr(get_user_today_plan_use_case.RepositoryFactory, 'get_user_community_rule_repository', Mock(return_value=mock_user_community_rule_repo))
        monkeypatch.setattr(get_user_today_plan_use_case.RepositoryFactory, 'get_community_checkin_rule_repository', Mock(return_value=Mock()))

        mock_user_community_rule_repo.find_by_user_id.return_value = []  # No community mappings

        # Mock db.session.execute
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.session.execute.return_value = mock_result

        user = Mock()
        user.user_id = 1
        user.community_id = None  # 用户不在社区，跳过社区规则
        mock_user_repo.find_by_id.return_value = user

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Rule1'
        rule.custom_time = None
        rule.status = 1
        rule.frequency_type = 0  # 每天
        rule.time_slot_type = 1  # 上午
        rule.icon_url = 'icon1.jpg'
        rule.week_days = None
        rule.custom_start_date = None
        rule.custom_end_date = None

        mock_rule_repo.find_active_by_user_id.return_value = [rule]
        mock_record_repo.get_today_checkin.return_value = None

        use_case = GetUserTodayPlanUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert len(result.data['items']) == 1


class TestGetUserRuleDetailUseCase:
    """测试GetUserRuleDetailUseCase"""

    @patch('app.application.use_cases.user_checkin.get_user_rule_detail_use_case.RepositoryFactory')
    def test_should_successfully_get_user_rule_detail(self, mock_repo_factory):
        """应该成功获取用户规则详情"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Rule1'
        rule.rule_type = 'personal'
        rule.status = 1
        rule.custom_time = None
        rule.user_id = 1  # 添加 user_id 属性
        rule.to_dict.return_value = {
            'rule_id': 101,
            'rule_name': 'Rule1',
            'rule_type': 'personal',
            'status': 1,
            'custom_time': None,
            'user_id': 1
        }

        mock_rule_repo.find_by_id.return_value = rule

        use_case = GetUserRuleDetailUseCase()

        # Act
        result = use_case.execute(user_id=1, rule_id=101)

        # Assert
        assert result.is_success
        assert result.data['rule_id'] == 101


class TestGetUserCheckinStatisticsUseCase:
    """测试GetUserCheckinStatisticsUseCase"""

    def test_should_successfully_get_user_checkin_statistics(self, mock_db, mock_repo_factory):
        """应该成功获取用户打卡统计"""
        # Arrange
        mock_user_repo = Mock()
        mock_rule_repo = Mock()
        mock_record_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_repo_factory.get_checkin_record_repository.return_value = mock_record_repo

        # Mock db.session.execute
        mock_result = Mock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.session.execute.return_value = mock_result

        user = Mock()
        user.user_id = 1
        mock_user_repo.find_by_id.return_value = user

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Rule1'
        mock_rule_repo.find_by_id.return_value = rule
        mock_rule_repo.find_active_by_user_id.return_value = [rule]

        mock_record_repo.get_statistics.return_value = {
            'total': 30,
            'completed': 25,
            'missed': 5
        }

        use_case = GetUserCheckinStatisticsUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert 'total_rules' in result.data
        assert 'checkin_days' in result.data


class TestGetRulesSourceInfoUseCase:
    """测试GetRulesSourceInfoUseCase"""

    @patch('app.application.use_cases.user_checkin.get_rules_source_info_use_case.RepositoryFactory')
    def test_should_successfully_get_rules_source_info(self, mock_repo_factory):
        """应该成功获取规则来源信息"""
        # Arrange
        mock_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        # UseCase 实际上不使用 rule_ids 和 community_rule_ids 参数
        # 而是返回空的 personal_rules 和 community_rules 列表
        use_case = GetRulesSourceInfoUseCase()

        # Act
        result = use_case.execute(user_id=1)

        # Assert
        assert result.is_success
        assert 'personal_rules' in result.data
        assert 'community_rules' in result.data