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

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含计划数据
        """
        # Arrange
        user_id = 123
        mock_plan = {'total_items': 5, 'items': []}

        with patch('app.application.use_cases.user_checkin.get_user_today_plan_use_case.UserCheckinRuleService') as mock_service:
            mock_service.get_today_checkin_plan.return_value = mock_plan
            # Act
            result = use_case.execute(user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "获取今日计划成功" in result.message
            assert result.data == mock_plan


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

    def test_execute_success(self, use_case):
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
        mock_source_info = {'rules': []}

        with patch('app.application.use_cases.user_checkin.get_rules_source_info_use_case.UserCheckinRuleService') as mock_service:
            mock_service.get_rules_source_info.return_value = mock_source_info
            # Act
            result = use_case.execute(user_id, rule_ids, community_rule_ids)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "获取来源信息成功" in result.message
            assert result.data == mock_source_info


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

    def test_execute_get_method_success(self, use_case):
        """
        测试执行成功 - GET 方法
        Given: 有效的用户ID和 GET 方法
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则列表
        """
        # Arrange
        user_id = 123
        method = 'GET'
        mock_rules = [{'id': 1, 'name': '规则1'}]

        with patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.UserCheckinRuleService') as mock_service:
            mock_service.get_user_all_rules.return_value = mock_rules
            # Act
            result = use_case.execute(user_id, method)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "获取规则成功" in result.message
            assert result.data == mock_rules

    def test_execute_delete_method_success(self, use_case):
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
        mock_response = {'deleted': True}

        with patch('app.application.use_cases.user_checkin.get_user_all_rules_use_case.CheckinRuleService') as mock_service:
            mock_service.delete_rule.return_value = mock_response
            # Act
            result = use_case.execute(user_id, method, params)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "删除规则成功" in result.message


class TestGetUserCheckinStatisticsUseCase:
    """GetUserCheckinStatisticsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserCheckinStatisticsUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的用户ID和周期
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = 123
        period = 'week'

        # Act
        result = use_case._validate(user_id, period)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_period(self, use_case):
        """
        测试验证失败 - 无效的统计周期
        Given: 无效的统计周期
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 123
        period = 'year'

        # Act
        result = use_case._validate(user_id, period)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "统计周期无效" in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的用户ID和周期
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含统计信息
        """
        # Arrange
        user_id = 123
        period = 'week'
        mock_stats = {'total': 10, 'completed': 8}

        with patch('app.application.use_cases.user_checkin.get_user_checkin_statistics_use_case.UserCheckinRuleService') as mock_service:
            mock_service.get_user_checkin_statistics.return_value = mock_stats
            # Act
            result = use_case.execute(user_id, period)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "获取统计信息成功" in result.message
            assert result.data == mock_stats


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

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的用户ID和规则ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则详情
        """
        # Arrange
        user_id = 123
        rule_id = 1
        mock_rule = {'id': 1, 'name': '规则1'}

        with patch('app.application.use_cases.user_checkin.get_user_rule_detail_use_case.UserCheckinRuleService') as mock_service:
            mock_service.get_user_rule_detail.return_value = mock_rule
            # Act
            result = use_case.execute(user_id, rule_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert "获取规则详情成功" in result.message
            assert result.data == mock_rule