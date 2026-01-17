"""
测试 CounterUseCase
"""
import pytest
from unittest.mock import patch, MagicMock
from app.application.use_cases.misc.counter_use_case import CounterUseCase
from app.application.use_cases.base import UseCaseStatus
from database.flask_models import Counters


class TestCounterUseCase:
    """测试 CounterUseCase"""

    def test_validate_with_valid_action(self):
        """测试验证有效的 action"""
        use_case = CounterUseCase()

        # 测试 list 和 clear（不需要参数）
        for action in ['list', 'clear']:
            result = use_case._validate(action, {})
            assert result.status == UseCaseStatus.SUCCESS

        # 测试 increment、reset 和 get（需要 counter_id 参数）
        for action in ['increment', 'reset']:
            result = use_case._validate(action, {'counter_id': 1})
            assert result.status == UseCaseStatus.SUCCESS

        # get 操作使用 id 参数
        result = use_case._validate('get', {'id': 1})
        assert result.status == UseCaseStatus.SUCCESS

    def test_validate_with_invalid_action(self):
        """测试验证无效的 action"""
        use_case = CounterUseCase()
        result = use_case._validate('invalid', {})
        
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '不支持的action参数' in result.message

    def test_validate_increment_requires_counter_id(self):
        """测试 increment 需要 counter_id"""
        use_case = CounterUseCase()
        result = use_case._validate('increment', {})
        
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '需要 counter_id 参数' in result.message

    def test_validate_reset_requires_counter_id(self):
        """测试 reset 需要 counter_id"""
        use_case = CounterUseCase()
        result = use_case._validate('reset', {})
        
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '需要 counter_id 参数' in result.message

    def test_validate_get_requires_id(self):
        """测试 get 需要 id"""
        use_case = CounterUseCase()
        result = use_case._validate('get', {})
        
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '需要 counter_id 参数' in result.message

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    @patch('app.application.use_cases.misc.counter_use_case.transaction')
    def test_execute_increment_new_counter(self, mock_transaction, mock_repo_factory):
        """测试增加新计数器"""
        # Arrange
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_by_id.return_value = None  # 计数器不存在
        mock_counters_repo.save.return_value = MagicMock(id=1, count=1)
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo
        mock_transaction.return_value.__enter__ = MagicMock(return_value=None)
        mock_transaction.return_value.__exit__ = MagicMock(return_value=None)

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('increment', {'counter_id': 1})

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '计数增加成功'
        assert result.data['id'] == 1
        assert result.data['count'] == 1

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    @patch('app.application.use_cases.misc.counter_use_case.transaction')
    def test_execute_increment_existing_counter(self, mock_transaction, mock_repo_factory):
        """测试增加现有计数器"""
        # Arrange
        mock_counter = MagicMock()
        mock_counter.count = 5
        mock_counter.id = 1
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_by_id.return_value = mock_counter
        mock_counters_repo.save.return_value = mock_counter
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo
        mock_transaction.return_value.__enter__ = MagicMock(return_value=None)
        mock_transaction.return_value.__exit__ = MagicMock(return_value=None)

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('increment', {'counter_id': 1})
        
        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['count'] == 6

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    @patch('app.application.use_cases.misc.counter_use_case.transaction')
    def test_execute_reset_success(self, mock_transaction, mock_repo_factory):
        """测试重置计数器成功"""
        # Arrange
        mock_counter = MagicMock()
        mock_counter.count = 10
        mock_counter.id = 1
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_by_id.return_value = mock_counter
        mock_counters_repo.save.return_value = mock_counter
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo
        mock_transaction.return_value.__enter__ = MagicMock(return_value=None)
        mock_transaction.return_value.__exit__ = MagicMock(return_value=None)

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('reset', {'counter_id': 1})

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['count'] == 0

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    def test_execute_reset_not_found(self, mock_repo_factory):
        """测试重置不存在的计数器"""
        # Arrange
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_by_id.return_value = None
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('reset', {'counter_id': 999})

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '不存在' in result.message

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    def test_execute_get_not_found(self, mock_repo_factory):
        """测试获取不存在的计数器"""
        # Arrange
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_by_id.return_value = None
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('get', {'id': 999})

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '不存在' in result.message

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    def test_execute_list_success(self, mock_repo_factory):
        """测试列出所有计数器"""
        # Arrange
        mock_counter1 = MagicMock()
        mock_counter1.id = 1
        mock_counter1.count = 5
        mock_counter2 = MagicMock()
        mock_counter2.id = 2
        mock_counter2.count = 10
        mock_counters_repo = MagicMock()
        mock_counters_repo.find_all.return_value = [mock_counter1, mock_counter2]
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('list', {})

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['counters']) == 2
        assert result.data['counters'][0]['id'] == 1
        assert result.data['counters'][1]['count'] == 10

    @patch('app.application.use_cases.misc.counter_use_case.RepositoryFactory')
    def test_execute_clear_success(self, mock_repo_factory):
        """测试清除所有计数器"""
        # Arrange
        mock_counters_repo = MagicMock()
        mock_repo_factory.get_counters_repository.return_value = mock_counters_repo

        use_case = CounterUseCase()

        # Act
        result = use_case._execute('clear', {})

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert '清除' in result.message
