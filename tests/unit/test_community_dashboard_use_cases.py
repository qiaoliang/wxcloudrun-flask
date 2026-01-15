"""
Community Dashboard UseCases 单元测试
"""
import pytest
from unittest.mock import Mock, patch
from app.application.use_cases.community_dashboard.get_trend_data_use_case import GetTrendDataUseCase
from app.application.use_cases.community_dashboard.get_user_abnormality_detail_use_case import GetUserAbnormalityDetailUseCase
from app.application.use_cases.community_dashboard.get_abnormal_users_use_case import GetAbnormalUsersUseCase
from app.application.use_cases.community_dashboard.get_community_stats_use_case import GetCommunityStatsUseCase
from app.application.use_cases.community_dashboard.get_pending_events_use_case import GetPendingEventsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetTrendDataUseCase:
    """GetTrendDataUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetTrendDataUseCase()

    def test_validate_success(self, use_case):
        """测试验证成功"""
        with patch('app.application.use_cases.community_dashboard.get_trend_data_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, days=7)
            assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_days(self, use_case):
        """测试验证失败 - 无效的天数"""
        with patch('app.application.use_cases.community_dashboard.get_trend_data_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, days=15)
            assert result.status == UseCaseStatus.VALIDATION_ERROR
            assert "天数参数" in result.message

    def test_validate_no_permission(self, use_case):
        """测试验证失败 - 无权限"""
        with patch('app.application.use_cases.community_dashboard.get_trend_data_use_case.CommunityDashboardService.has_permission', return_value=False):
            result = use_case._validate(community_id=1, user_id=123, days=7)
            assert result.status == UseCaseStatus.VALIDATION_ERROR
            assert "无权限" in result.message

    def test_execute_success(self, use_case):
        """测试执行成功"""
        mock_trends = {'data': []}
        with patch('app.application.use_cases.community_dashboard.get_trend_data_use_case.CommunityDashboardService.get_trend_data', return_value=mock_trends):
            result = use_case._execute(community_id=1, user_id=123, days=7)
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_trends


class TestGetUserAbnormalityDetailUseCase:
    """GetUserAbnormalityDetailUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserAbnormalityDetailUseCase()

    def test_validate_success(self, use_case):
        """测试验证成功"""
        with patch('app.application.use_cases.community_dashboard.get_user_abnormality_detail_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, request_user_id=456)
            assert result.status == UseCaseStatus.SUCCESS

    def test_execute_success(self, use_case):
        """测试执行成功"""
        mock_detail = {'user_id': 123, 'abnormalities': []}
        with patch('app.application.use_cases.community_dashboard.get_user_abnormality_detail_use_case.CommunityDashboardService.get_user_abnormality_detail', return_value=mock_detail):
            result = use_case._execute(community_id=1, user_id=123, request_user_id=456)
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_detail


class TestGetAbnormalUsersUseCase:
    """GetAbnormalUsersUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetAbnormalUsersUseCase()

    def test_validate_success(self, use_case):
        """测试验证成功"""
        with patch('app.application.use_cases.community_dashboard.get_abnormal_users_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, page=1, page_size=20)
            assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_page_size(self, use_case):
        """测试验证失败 - 无效的每页数量"""
        with patch('app.application.use_cases.community_dashboard.get_abnormal_users_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, page=1, page_size=150)
            assert result.status == UseCaseStatus.VALIDATION_ERROR
            assert "每页数量" in result.message

    def test_execute_success(self, use_case):
        """测试执行成功"""
        mock_result = {'users': [], 'total': 0}
        with patch('app.application.use_cases.community_dashboard.get_abnormal_users_use_case.CommunityDashboardService.get_abnormal_users', return_value=mock_result):
            result = use_case._execute(community_id=1, user_id=123, page=1, page_size=20)
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_result


class TestGetCommunityStatsUseCase:
    """GetCommunityStatsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityStatsUseCase()

    def test_validate_success(self, use_case):
        """测试验证成功"""
        with patch('app.application.use_cases.community_dashboard.get_community_stats_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123)
            assert result.status == UseCaseStatus.SUCCESS

    def test_execute_success(self, use_case):
        """测试执行成功"""
        mock_stats = {'total_users': 100, 'active_users': 80}
        with patch('app.application.use_cases.community_dashboard.get_community_stats_use_case.CommunityDashboardService.get_community_stats', return_value=mock_stats):
            result = use_case._execute(community_id=1, user_id=123)
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_stats


class TestGetPendingEventsUseCase:
    """GetPendingEventsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetPendingEventsUseCase()

    def test_validate_success(self, use_case):
        """测试验证成功"""
        with patch('app.application.use_cases.community_dashboard.get_pending_events_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, limit=3)
            assert result.status == UseCaseStatus.SUCCESS

    def test_validate_invalid_limit(self, use_case):
        """测试验证失败 - 无效的限制数量"""
        with patch('app.application.use_cases.community_dashboard.get_pending_events_use_case.CommunityDashboardService.has_permission', return_value=True):
            result = use_case._validate(community_id=1, user_id=123, limit=150)
            assert result.status == UseCaseStatus.VALIDATION_ERROR
            assert "限制数量" in result.message

    def test_execute_success(self, use_case):
        """测试执行成功"""
        mock_events = {'events': [], 'total': 0}
        with patch('app.application.use_cases.community_dashboard.get_pending_events_use_case.CommunityDashboardService.get_pending_events', return_value=mock_events):
            result = use_case._execute(community_id=1, user_id=123, limit=3)
            assert result.status == UseCaseStatus.SUCCESS
            assert result.data == mock_events