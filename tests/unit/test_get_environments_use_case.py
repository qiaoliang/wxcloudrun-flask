"""
测试 GetEnvironmentsUseCase
"""
import pytest
from unittest.mock import patch, MagicMock
from app.application.use_cases.misc.get_environments_use_case import GetEnvironmentsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetEnvironmentsUseCase:
    """测试 GetEnvironmentsUseCase"""

    def test_validate_always_returns_success(self):
        """测试 _validate 方法总是返回成功"""
        use_case = GetEnvironmentsUseCase()
        result = use_case._validate()
        
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == "验证通过"

    @patch('app.application.use_cases.misc.get_environments_use_case.analyze_all_configs')
    @patch('app.application.use_cases.misc.get_environments_use_case.detect_external_systems_status')
    @patch('app.application.use_cases.misc.get_environments_use_case.current_app')
    def test_execute_success(self, mock_app, mock_detect_external, mock_analyze_configs):
        """测试成功执行"""
        # Arrange
        mock_analyze_configs.return_value = {'status': 'ok'}
        mock_detect_external.return_value = {'status': 'ok'}
        mock_app.logger = MagicMock()
        
        use_case = GetEnvironmentsUseCase()
        
        # Act
        result = use_case._execute()
        
        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '获取环境配置信息成功'
        assert 'config_status' in result.data
        assert 'external_status' in result.data
        assert 'timestamp' in result.data
        mock_app.logger.info.assert_called_once()

    @patch('app.application.use_cases.misc.get_environments_use_case.analyze_all_configs')
    @patch('app.application.use_cases.misc.get_environments_use_case.current_app')
    def test_execute_failure(self, mock_app, mock_analyze_configs):
        """测试执行失败"""
        # Arrange
        mock_analyze_configs.side_effect = Exception("配置错误")
        mock_app.logger = MagicMock()
        
        use_case = GetEnvironmentsUseCase()
        
        # Act
        result = use_case._execute()
        
        # Assert
        assert result.status == UseCaseStatus.FAILURE
        assert '配置错误' in result.message
        assert result.data == {}
        mock_app.logger.error.assert_called_once()

    @patch('app.application.use_cases.misc.get_environments_use_case.analyze_all_configs')
    @patch('app.application.use_cases.misc.get_environments_use_case.detect_external_systems_status')
    @patch('app.application.use_cases.misc.get_environments_use_case.current_app')
    def test_execute_returns_correct_data_structure(self, mock_app, mock_detect_external, mock_analyze_configs):
        """测试返回正确的数据结构"""
        # Arrange
        mock_analyze_configs.return_value = {'env': 'dev'}
        mock_detect_external.return_value = {'db': 'ok'}
        mock_app.logger = MagicMock()
        
        use_case = GetEnvironmentsUseCase()
        
        # Act
        result = use_case._execute()
        
        # Assert
        assert result.data['config_status'] == {'env': 'dev'}
        assert result.data['external_status'] == {'db': 'ok'}
        assert result.data['timestamp'] is not None
