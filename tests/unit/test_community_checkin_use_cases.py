"""
Community Checkin UseCases 单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.community_checkin.create_community_checkin_rule_use_case import CreateCommunityCheckinRuleUseCase
from app.application.use_cases.community_checkin.delete_community_checkin_rule_use_case import DeleteCommunityCheckinRuleUseCase
from app.application.use_cases.community_checkin.disable_community_checkin_rule_use_case import DisableCommunityCheckinRuleUseCase
from app.application.use_cases.community_checkin.enable_community_checkin_rule_use_case import EnableCommunityCheckinRuleUseCase
from app.application.use_cases.community_checkin.get_community_checkin_rule_use_case import GetCommunityCheckinRuleUseCase
from app.application.use_cases.community_checkin.get_community_checkin_rules_use_case import GetCommunityCheckinRulesUseCase
from app.application.use_cases.community_checkin.get_community_checkin_stats_use_case import GetCommunityCheckinStatsUseCase
from app.application.use_cases.community_checkin.get_community_daily_stats_use_case import GetCommunityDailyStatsUseCase
from app.application.use_cases.community_checkin.update_community_checkin_rule_use_case import UpdateCommunityCheckinRuleUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCreateCommunityCheckinRuleUseCase:
    """CreateCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CreateCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的参数、社区ID和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        params = {'rule_name': '测试规则'}
        community_id = 1
        user_id = 123

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '验证通过'

    def test_validate_empty_params(self, use_case):
        """
        测试验证失败 - 参数为空
        Given: 参数为空
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        params = None
        community_id = 1
        user_id = 123

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '请求参数不能为空' in result.message

    def test_validate_invalid_params_format(self, use_case):
        """
        测试验证失败 - 参数格式错误
        Given: 参数不是字典类型
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        params = "invalid"
        community_id = 1
        user_id = 123

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '请求参数格式错误' in result.message

    def test_validate_missing_required_field(self, use_case):
        """
        测试验证失败 - 缺少必要参数
        Given: 缺少 rule_name 参数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        params = {'description': '测试描述'}
        community_id = 1
        user_id = 123

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '缺少必要参数' in result.message

    def test_validate_invalid_community_id(self, use_case):
        """
        测试验证失败 - 无效的社区ID
        Given: 社区ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        params = {'rule_name': '测试规则'}
        community_id = -1
        user_id = 123

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '社区ID必须为正整数' in result.message

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 用户ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        params = {'rule_name': '测试规则'}
        community_id = 1
        user_id = 0

        # Act
        result = use_case._validate(params, community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的参数、社区ID和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则ID
        """
        # Arrange
        params = {'rule_name': '测试规则'}
        community_id = 1
        user_id = 123
        mock_rule = Mock()
        mock_rule.community_rule_id = 1

        with patch('app.application.use_cases.community_checkin.create_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.create_community_rule.return_value = mock_rule
            # Act
            result = use_case.execute(params, community_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '创建成功' in result.message
            assert result.data['rule_id'] == 1

    def test_execute_failure(self, use_case):
        """
        测试执行失败
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        params = {'rule_name': '测试规则'}
        community_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.create_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.create_community_rule.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(params, community_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '创建规则失败' in result.message


class TestDeleteCommunityCheckinRuleUseCase:
    """DeleteCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return DeleteCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的规则ID和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_rule_id(self, use_case):
        """
        测试验证失败 - 无效的规则ID
        Given: 规则ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 0
        user_id = 123

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID必须为正整数' in result.message

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 用户ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 1
        user_id = -1

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的规则ID和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.delete_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.delete_community_rule.return_value = True
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '删除成功' in result.message
            assert result.data['rule_id'] == 1

    def test_execute_failure(self, use_case):
        """
        测试执行失败
        Given: 服务层返回删除失败
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.delete_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.delete_community_rule.return_value = False
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '删除失败' in result.message

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.delete_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.delete_community_rule.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '删除规则失败' in result.message


class TestDisableCommunityCheckinRuleUseCase:
    """DisableCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return DisableCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的规则ID和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_rule_id(self, use_case):
        """
        测试验证失败 - 无效的规则ID
        Given: 规则ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = -1
        user_id = 123

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的规则ID和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123
        mock_rule = {'community_rule_id': 1}

        with patch('app.application.use_cases.community_checkin.disable_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.disable_community_rule.return_value = mock_rule
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '禁用成功' in result.message
            assert result.data['rule_id'] == 1

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.disable_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.disable_community_rule.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '禁用规则失败' in result.message


class TestEnableCommunityCheckinRuleUseCase:
    """EnableCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return EnableCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的规则ID和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 用户ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 1
        user_id = 0

        # Act
        result = use_case._validate(rule_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的规则ID和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123
        mock_rule = {'community_rule_id': 1}

        with patch('app.application.use_cases.community_checkin.enable_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.enable_community_rule.return_value = mock_rule
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '启用成功' in result.message
            assert result.data['rule_id'] == 1

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.enable_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.enable_community_rule.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(rule_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '启用规则失败' in result.message


class TestGetCommunityCheckinRuleUseCase:
    """GetCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的规则ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1

        # Act
        result = use_case._validate(rule_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_rule_id(self, use_case):
        """
        测试验证失败 - 无效的规则ID
        Given: 规则ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = -1

        # Act
        result = use_case._validate(rule_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的规则ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则详情
        """
        # Arrange
        rule_id = 1
        mock_rule = {'community_rule_id': 1, 'rule_name': '测试规则'}

        with patch('app.application.use_cases.community_checkin.get_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.get_rule_detail.return_value = mock_rule
            # Act
            result = use_case.execute(rule_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '获取规则详情成功' in result.message
            assert result.data['rule'] == mock_rule

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1

        with patch('app.application.use_cases.community_checkin.get_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.get_rule_detail.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(rule_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '获取规则详情失败' in result.message


class TestGetCommunityCheckinRulesUseCase:
    """GetCommunityCheckinRulesUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityCheckinRulesUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的社区ID和分页参数
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        community_id = 1
        page = 1
        per_page = 20

        # Act
        result = use_case._validate(community_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_community_id(self, use_case):
        """
        测试验证失败 - 无效的社区ID
        Given: 社区ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 0
        page = 1
        per_page = 20

        # Act
        result = use_case._validate(community_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '社区ID必须为正整数' in result.message

    def test_validate_invalid_page(self, use_case):
        """
        测试验证失败 - 无效的页码
        Given: 页码为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        page = -1
        per_page = 20

        # Act
        result = use_case._validate(community_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '页码必须为正整数' in result.message

    def test_validate_invalid_per_page(self, use_case):
        """
        测试验证失败 - 无效的每页数量
        Given: 每页数量超过100
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        page = 1
        per_page = 150

        # Act
        result = use_case._validate(community_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '每页数量必须在1-100之间' in result.message

    def test_validate_invalid_status_filter(self, use_case):
        """
        测试验证失败 - 无效的状态过滤参数
        Given: 状态过滤参数不是 enabled 或 disabled
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        page = 1
        per_page = 20
        status_filter = 'invalid'

        # Act
        result = use_case._validate(community_id, page, per_page, status_filter)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '状态过滤参数必须是 enabled 或 disabled' in result.message

    def test_validate_invalid_grouped(self, use_case):
        """
        测试验证失败 - 无效的分组参数
        Given: 分组参数不是布尔值
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        page = 1
        per_page = 20
        grouped = 'true'

        # Act
        result = use_case._validate(community_id, page, per_page, grouped=grouped)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '分组参数必须是布尔值' in result.message

    def test_execute_success_flat_list(self, use_case):
        """
        测试执行成功 - 获取扁平列表
        Given: 有效的社区ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则列表
        """
        # Arrange
        community_id = 1
        mock_rules = [{'community_rule_id': 1, 'rule_name': '规则1'}]

        with patch('app.application.use_cases.community_checkin.get_community_checkin_rules_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.get_community_rules.return_value = mock_rules
            # Act
            result = use_case.execute(community_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '获取规则列表成功' in result.message
            assert result.data['rules'] == mock_rules
            assert result.data['total'] == 1

    def test_execute_success_grouped(self, use_case):
        """
        测试执行成功 - 获取分组列表
        Given: 有效的社区ID和分组参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含分组规则
        """
        # Arrange
        community_id = 1
        mock_grouped = {
            'enabled': [{'community_rule_id': 1}],
            'disabled': [{'community_rule_id': 2}],
            'deleted': [{'community_rule_id': 3}]
        }

        with patch('app.application.use_cases.community_checkin.get_community_checkin_rules_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.get_all_community_rules_grouped.return_value = mock_grouped
            # Act
            result = use_case.execute(community_id, grouped=True)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_grouped

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        community_id = 1

        with patch('app.application.use_cases.community_checkin.get_community_checkin_rules_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.get_community_rules.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(community_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '获取规则列表失败' in result.message


class TestGetCommunityCheckinStatsUseCase:
    """GetCommunityCheckinStatsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityCheckinStatsUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的社区ID、用户ID和天数
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        community_id = 1
        user_id = 123
        days = 7

        # Act
        result = use_case._validate(community_id, user_id, days)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_community_id(self, use_case):
        """
        测试验证失败 - 无效的社区ID
        Given: 社区ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = -1
        user_id = 123
        days = 7

        # Act
        result = use_case._validate(community_id, user_id, days)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '社区ID必须为正整数' in result.message

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 用户ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        user_id = 0
        days = 7

        # Act
        result = use_case._validate(community_id, user_id, days)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID必须为正整数' in result.message

    def test_validate_invalid_days(self, use_case):
        """
        测试验证失败 - 无效的天数
        Given: 天数超过365
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 1
        user_id = 123
        days = 400

        # Act
        result = use_case._validate(community_id, user_id, days)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '统计天数必须在1-365之间' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的社区ID、用户ID和天数，且有权限
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含统计信息
        """
        # Arrange
        community_id = 1
        user_id = 123
        days = 7
        mock_stats = {'total_rules': 5, 'completed': 3}

        with patch('app.application.use_cases.community_checkin.get_community_checkin_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = True
            mock_service.get_community_checkin_stats.return_value = mock_stats
            # Act
            result = use_case.execute(community_id, user_id, days)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '获取统计信息成功' in result.message
            assert result.data == mock_stats

    def test_execute_no_permission(self, use_case):
        """
        测试执行失败 - 无权限
        Given: 用户无权限访问社区
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        community_id = 1
        user_id = 123
        days = 7

        with patch('app.application.use_cases.community_checkin.get_community_checkin_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = False
            # Act
            result = use_case.execute(community_id, user_id, days)

            # Assert
            assert result.status == UseCaseStatus.FORBIDDEN
            assert '无权限访问该社区' in result.message

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        community_id = 1
        user_id = 123
        days = 7

        with patch('app.application.use_cases.community_checkin.get_community_checkin_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = True
            mock_service.get_community_checkin_stats.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(community_id, user_id, days)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '获取统计信息失败' in result.message


class TestGetCommunityDailyStatsUseCase:
    """GetCommunityDailyStatsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityDailyStatsUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的社区ID和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        community_id = 1
        user_id = 123

        # Act
        result = use_case._validate(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_community_id(self, use_case):
        """
        测试验证失败 - 无效的社区ID
        Given: 社区ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = 0
        user_id = 123

        # Act
        result = use_case._validate(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '社区ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的社区ID和用户ID，且有权限
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含每日统计信息
        """
        # Arrange
        community_id = 1
        user_id = 123
        mock_stats = {'date': '2026-01-15', 'total': 10, 'completed': 8}

        with patch('app.application.use_cases.community_checkin.get_community_daily_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = True
            mock_service.get_community_daily_stats.return_value = mock_stats
            # Act
            result = use_case.execute(community_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '获取统计信息成功' in result.message
            assert result.data == mock_stats

    def test_execute_no_permission(self, use_case):
        """
        测试执行失败 - 无权限
        Given: 用户无权限访问社区
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        community_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.get_community_daily_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = False
            # Act
            result = use_case.execute(community_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FORBIDDEN
            assert '无权限访问该社区' in result.message

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        community_id = 1
        user_id = 123

        with patch('app.application.use_cases.community_checkin.get_community_daily_stats_use_case.CommunityService') as mock_service:
            mock_service.has_community_permission.return_value = True
            mock_service.get_community_daily_stats.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(community_id, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '获取统计信息失败' in result.message


class TestUpdateCommunityCheckinRuleUseCase:
    """UpdateCommunityCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UpdateCommunityCheckinRuleUseCase()

    def test_validate_success(self, use_case):
        """
        测试验证成功
        Given: 有效的规则ID、参数和用户ID
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        rule_id = 1
        params = {'rule_name': '更新后的规则'}
        user_id = 123

        # Act
        result = use_case._validate(rule_id, params, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_rule_id(self, use_case):
        """
        测试验证失败 - 无效的规则ID
        Given: 规则ID为负数
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = -1
        params = {'rule_name': '更新后的规则'}
        user_id = 123

        # Act
        result = use_case._validate(rule_id, params, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID必须为正整数' in result.message

    def test_validate_empty_params(self, use_case):
        """
        测试验证失败 - 参数为空
        Given: 参数为空字典
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 1
        params = {}
        user_id = 123

        # Act
        result = use_case._validate(rule_id, params, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '请求参数不能为空' in result.message

    def test_validate_invalid_params_format(self, use_case):
        """
        测试验证失败 - 参数格式错误
        Given: 参数不是字典类型
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 1
        params = "invalid"
        user_id = 123

        # Act
        result = use_case._validate(rule_id, params, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '请求参数格式错误' in result.message

    def test_validate_invalid_user_id(self, use_case):
        """
        测试验证失败 - 无效的用户ID
        Given: 用户ID为0
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = 1
        params = {'rule_name': '更新后的规则'}
        user_id = 0

        # Act
        result = use_case._validate(rule_id, params, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '用户ID必须为正整数' in result.message

    def test_execute_success(self, use_case):
        """
        测试执行成功
        Given: 有效的规则ID、参数和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含规则ID
        """
        # Arrange
        rule_id = 1
        params = {'rule_name': '更新后的规则'}
        user_id = 123
        mock_rule = Mock()
        mock_rule.community_rule_id = 1

        with patch('app.application.use_cases.community_checkin.update_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.update_community_rule.return_value = mock_rule
            # Act
            result = use_case.execute(rule_id, params, user_id)

            # Assert
            assert result.status == UseCaseStatus.SUCCESS
            assert '更新成功' in result.message
            assert result.data['rule_id'] == 1

    def test_execute_exception(self, use_case):
        """
        测试执行异常
        Given: 服务层抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        rule_id = 1
        params = {'rule_name': '更新后的规则'}
        user_id = 123

        with patch('app.application.use_cases.community_checkin.update_community_checkin_rule_use_case.CommunityCheckinRuleService') as mock_service:
            mock_service.update_community_rule.side_effect = Exception('数据库错误')
            # Act
            result = use_case.execute(rule_id, params, user_id)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert '更新规则失败' in result.message