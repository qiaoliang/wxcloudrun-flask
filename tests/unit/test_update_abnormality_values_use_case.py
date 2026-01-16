"""
UpdateAbnormalityValuesUseCase单元测试
"""
import pytest
from datetime import date
from unittest.mock import Mock, patch
from app.application.use_cases.background_task import UpdateAbnormalityValuesUseCase
from app.application.use_cases.base import UseCaseStatus


class TestUpdateAbnormalityValuesUseCase:
    """测试UpdateAbnormalityValuesUseCase"""

    @patch('app.application.use_cases.background_task.update_abnormality_values_use_case.AbnormalityCalculator')
    def test_execute_success(self, mock_calculator):
        """测试执行成功"""
        # Arrange
        mock_calculator.calculate_all_pending_users.return_value = {
            'total_users': 10,
            'calculated': 8,
            'skipped': 2,
            'errors': 0
        }

        use_case = UpdateAbnormalityValuesUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '异常值计算完成'
        assert result.data['total_users'] == 10
        assert result.data['calculated'] == 8

    @patch('app.application.use_cases.background_task.update_abnormality_values_use_case.AbnormalityCalculator')
    def test_execute_with_custom_date(self, mock_calculator):
        """测试使用自定义日期执行"""
        # Arrange
        custom_date = date(2026, 1, 15)
        mock_calculator.calculate_all_pending_users.return_value = {
            'total_users': 5,
            'calculated': 5,
            'skipped': 0,
            'errors': 0
        }

        use_case = UpdateAbnormalityValuesUseCase()

        # Act
        result = use_case.execute(target_date=custom_date)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        mock_calculator.calculate_all_pending_users.assert_called_once_with(custom_date)

    @patch('app.application.use_cases.background_task.update_abnormality_values_use_case.AbnormalityCalculator')
    def test_execute_error(self, mock_calculator):
        """测试执行失败"""
        # Arrange
        mock_calculator.calculate_all_pending_users.side_effect = Exception("Calculation error")

        use_case = UpdateAbnormalityValuesUseCase()

        # Act
        result = use_case.execute()

        # Assert
        assert result.status == UseCaseStatus.FAILURE
        assert 'Calculation error' in result.message