"""
User Checkin UseCases 单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.user_checkin.get_user_today_plan_use_case import GetUserTodayPlanUseCase
from app.application.use_cases.user_checkin.get_rules_source_info_use_case import GetRulesSourceInfoUseCase
from app.application.use_cases.user_checkin.get_user_all_rules_use_case import GetUserAllRulesUseCase
from app.application.use_cases.user_checkin.get_user_checkin_statistics_use_case import GetUserCheckinStatisticsUseCase
from app.application.use_cases.user_checkin.get_user_rule_detail_use_case import GetUserRuleDetailUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetUserTodayPlanUseCase:
    """GetUserTodayPlanUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserTodayPlanUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123

        # Act
        result = use_case._validate(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == "验证通过"

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 无效的用户ID
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = -1

        # Act
        result = use_case._validate(user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID无效" in result.message

    @patch('app.application.use_cases.user_checkin.get_user_today_plan_use_case.RepositoryFactory')
    def test_execute_success(self, mock_repo_factory, use_case):
        """
        测试执行成功
        Given: 有效的用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含计划数据
        """
        # Arrange
        user_id = 123

        mock_checkin_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_checkin_rule_repo.find_active_by_user_id.return_value = []

        mock_user_community_rule_repo = Mock()
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo
        mock_user_community_rule_repo.find_by_user_id.return_value = []

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取今日计划成功" in result.message
        assert 'total_items' in result.data


class TestGetRulesSourceInfoUseCase:
    """GetRulesSourceInfoUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetRulesSourceInfoUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123

        # Act
        result = use_case._validate(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    @patch('app.application.use_cases.user_checkin.get_rules_source_info_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user_checkin.get_rules_source_info_use_case.db')
    def test_execute_success(self, mock_db, mock_repo_factory, use_case):
        """
        测试执行成功
        Given: 有效的用户ID和规则ID列表
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含来源信息
        """
        # Arrange
        user_id = 123
        rule_ids = [1, 2, 3]
        community_rule_ids = [4, 5]

        mock_user = Mock()
        mock_user.community_id = 1
        mock_db.session.get.return_value = mock_user

        mock_checkin_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_checkin_rule_repo.find_by_id.return_value = None

        mock_community_checkin_rule_repo = Mock()
        mock_repo_factory.get_community_checkin_rule_repository.return_value = mock_community_checkin_rule_repo
        mock_community_checkin_rule_repo.find_by_id.return_value = None

        mock_user_community_rule_repo = Mock()
        mock_repo_factory.get_user_community_rule_repository.return_value = mock_user_community_rule_repo
        mock_user_community_rule_repo.find_by_user_and_rule.return_value = None

        # Act
        result = use_case.execute(user_id, rule_ids, community_rule_ids)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取来源信息成功" in result.message
        assert 'personal_rules' in result.data
        assert 'community_rules' in result.data


class TestGetUserAllRulesUseCase:
    """GetUserAllRulesUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserAllRulesUseCase()

    def test_validate_success_get_method(self, use_case):
        """
        测试验证成功 - GET 方法
        Given: 有效的用户ID和 GET 方法
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123
        method = 'GET'

        # Act
        result = use_case._validate(user_id, method)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_delete_method_success(self, use_case):
        """
        测试验证成功 - DELETE 方法
        Given: 有效的用户ID、DELETE 方法和参数
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123
        method = 'DELETE'
        params = {'rule_id': 1, 'rule_source': 'personal'}

        # Act
        result = use_case._validate(user_id, method, params)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_delete_method_missing_params(self, use_case):
        """
        测试验证失败 - DELETE 方法缺少参数
        Given: DELETE 方法但缺少参数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 123
        method = 'DELETE'

        # Act
        result = use_case._validate(user_id, method)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "缺少请求参数" in result.message

    def test_validate_delete_method_community_rule(self, use_case):
        """
        测试验证失败 - DELETE 方法尝试删除社区规则
        Given: DELETE 方法，规则来源为 community
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 123
        method = 'DELETE'
        params = {'rule_id': 1, 'rule_source': 'community'}

        # Act
        result = use_case._validate(user_id, method, params)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "不允许删除社区规则" in result.message

    @patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.RepositoryFactory')
    @patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.db')
    def test_execute_get_method_success(self, mock_db, mock_repo_factory, use_case):
        """
        测试执行成功 - GET 方法
        Given: 有效的用户ID和 GET 方法
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则列表
        """
        # Arrange
        user_id = 123
        method = 'GET'

        mock_user = Mock()
        mock_user.community_id = None
        mock_db.session.get.return_value = mock_user

        mock_checkin_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_checkin_rule_repo.find_active_by_user_id.return_value = []

        # Act
        result = use_case.execute(user_id, method)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取规则成功" in result.message
        assert 'rules' in result.data

    @patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.RepositoryFactory')
    def test_execute_delete_method_success(self, mock_repo_factory, use_case):
        """
        测试执行成功 - DELETE 方法
        Given: 有效的用户ID、DELETE 方法和参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123
        method = 'DELETE'
        params = {'rule_id': 1, 'rule_source': 'personal'}

        mock_rule = Mock()
        mock_rule.user_id = 123

        mock_checkin_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_checkin_rule_repo.find_by_id.return_value = mock_rule
        mock_checkin_rule_repo.soft_delete.return_value = True

        # Act
        result = use_case.execute(user_id, method, params)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "删除规则成功" in result.message



class TestGetUserRuleDetailUseCase:
    """GetUserRuleDetailUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserRuleDetailUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的用户ID和规则ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123
        rule_id = 1

        # Act
        result = use_case._validate(user_id, rule_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_rule_id(self, use_case):
        """
        测试验证失败 - 无效的规则ID
        Given: 无效的规则ID
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 123
        rule_id = -1

        # Act
        result = use_case._validate(user_id, rule_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则ID无效" in result.message

    @patch('app.application.use_cases.user_checkin.get_user_rule_detail_use_case.RepositoryFactory')
    def test_execute_success(self, mock_repo_factory, use_case):
        """
        测试执行成功
        Given: 有效的用户ID和规则ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则详情
        """
        # Arrange
        user_id = 123
        rule_id = 1

        mock_rule = Mock()
        mock_rule.user_id = 123
        mock_rule.to_dict.return_value = {'id': 1, 'name': '规则1'}

        mock_checkin_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_checkin_rule_repo
        mock_checkin_rule_repo.find_by_id.return_value = mock_rule

        # Act
        result = use_case.execute(user_id, rule_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取规则详情成功" in result.message
        assert result.data['rule_source'] == 'personal'