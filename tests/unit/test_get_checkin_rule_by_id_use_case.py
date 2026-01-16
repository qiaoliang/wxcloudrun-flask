"""
GetCheckinRuleByIdUseCase单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.supervision.get_checkin_rule_by_id_use_case import GetCheckinRuleByIdUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetCheckinRuleByIdUseCase:
    """测试GetCheckinRuleByIdUseCase"""

    @patch('app.application.use_cases.supervision.get_checkin_rule_by_id_use_case.RepositoryFactory')
    def test_should_successfully_get_rule_by_id(self, mock_repo_factory):
        """应该成功通过ID获取打卡规则"""
        # Arrange - 准备测试数据和Mock
        mock_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo

        rule = Mock()
        rule.rule_id = 101
        rule.rule_name = 'Morning Checkin'
        rule.user_id = 1

        mock_rule_repo.find_by_id.return_value = rule

        use_case = GetCheckinRuleByIdUseCase()

        # Act - 执行被测试的方法
        result = use_case.execute(rule_id=101)

        # Assert - 验证行为
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data.rule_id == 101
        assert result.data.rule_name == 'Morning Checkin'
        mock_rule_repo.find_by_id.assert_called_once_with(101)

    @patch('app.application.use_cases.supervision.get_checkin_rule_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_rule_not_found(self, mock_repo_factory):
        """应该在规则不存在时失败"""
        # Arrange
        mock_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_rule_repo.find_by_id.return_value = None

        use_case = GetCheckinRuleByIdUseCase()

        # Act
        result = use_case.execute(rule_id=999)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '打卡规则不存在' in result.message

    @patch('app.application.use_cases.supervision.get_checkin_rule_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_rule_id_is_empty(self, mock_repo_factory):
        """应该在规则ID为空时失败"""
        # Arrange
        use_case = GetCheckinRuleByIdUseCase()

        # Act
        result = use_case.execute(rule_id=None)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_checkin_rule_by_id_use_case.RepositoryFactory')
    def test_should_fail_when_rule_id_is_zero(self, mock_repo_factory):
        """应该在规则ID为0时失败"""
        # Arrange
        use_case = GetCheckinRuleByIdUseCase()

        # Act
        result = use_case.execute(rule_id=0)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '规则ID不能为空' in result.message

    @patch('app.application.use_cases.supervision.get_checkin_rule_by_id_use_case.RepositoryFactory')
    def test_should_handle_repository_exception(self, mock_repo_factory):
        """应该处理Repository异常"""
        # Arrange
        mock_rule_repo = Mock()
        mock_repo_factory.get_checkin_rule_repository.return_value = mock_rule_repo
        mock_rule_repo.find_by_id.side_effect = Exception('Database error')

        use_case = GetCheckinRuleByIdUseCase()

        # Act
        result = use_case.execute(rule_id=101)

        # Assert
        assert not result.is_success
        assert result.status == UseCaseStatus.FAILURE
        assert '查询失败' in result.message