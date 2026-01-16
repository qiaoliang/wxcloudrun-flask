"""
格式化社区信息用例单元测试
"""
import pytest
from datetime import datetime
from unittest.mock import Mock, patch
from app.application.use_cases.community.format_community_info_use_case import FormatCommunityInfoUseCase
from app.application.use_cases.base import UseCaseStatus


class TestFormatCommunityInfoUseCase:
    """测试FormatCommunityInfoUseCase"""

    @patch('app.application.use_cases.community.format_community_info_use_case.RepositoryFactory')
    def test_should_successfully_format_community_info_without_stats(self, mock_repo_factory):
        """应该成功格式化社区信息（不包含统计）"""
        # Arrange
        mock_user_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        community = Mock()
        community.community_id = 1
        community.name = 'Test Community'
        community.description = 'Test Description'
        community.location = 'Test Location'
        community.location_lat = 40.7128
        community.location_lon = -74.0060
        community.province = 'Test Province'
        community.city = 'Test City'
        community.district = 'Test District'
        community.street = 'Test Street'
        community.creator_id = 100
        community.manager_id = 200
        community.status = 1
        community.is_default = False
        community.is_blackhouse = False
        community.created_at = datetime.now()
        community.updated_at = datetime.now()

        creator_user = Mock()
        creator_user.user_id = 100
        creator_user.nickname = 'Creator'
        creator_user.avatar_url = 'creator.jpg'

        manager_user = Mock()
        manager_user.user_id = 200
        manager_user.nickname = 'Manager'
        manager_user.avatar_url = 'manager.jpg'

        mock_user_repo.find_by_id.side_effect = [creator_user, manager_user]

        use_case = FormatCommunityInfoUseCase()

        # Act
        result = use_case.execute(community, include_worker_stats=False)

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['community_id'] == 1
        assert result.data['name'] == 'Test Community'
        assert result.data['creator']['user_id'] == 100
        assert result.data['manager']['user_id'] == 200
        assert result.data['manager_name'] == 'Manager'
        assert result.data['manager_count'] == 0
        assert result.data['worker_count'] == 0
        assert result.data['staff_count'] == 0
        assert result.data['user_count'] == 0

    @patch('app.application.use_cases.community.format_community_info_use_case.RepositoryFactory')
    def test_should_successfully_format_community_info_with_stats(self, mock_repo_factory):
        """应该成功格式化社区信息（包含统计）"""
        # Arrange
        mock_user_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        community = Mock()
        community.community_id = 1
        community.name = 'Test Community'
        community.description = 'Test Description'
        community.location = 'Test Location'
        community.location_lat = 40.7128
        community.location_lon = -74.0060
        community.province = 'Test Province'
        community.city = 'Test City'
        community.district = 'Test District'
        community.street = 'Test Street'
        community.creator_id = 100
        community.manager_id = 200
        community.status = 1
        community.is_default = False
        community.is_blackhouse = False
        community.created_at = datetime.now()
        community.updated_at = datetime.now()

        creator_user = Mock()
        creator_user.user_id = 100
        creator_user.nickname = 'Creator'
        creator_user.avatar_url = 'creator.jpg'

        manager_user = Mock()
        manager_user.user_id = 200
        manager_user.nickname = 'Manager'
        manager_user.avatar_url = 'manager.jpg'

        mock_user_repo.find_by_id.side_effect = [creator_user, manager_user]

        # 模拟工作人员
        manager_staff = Mock()
        manager_staff.user_id = 200

        staff1 = Mock()
        staff1.user_id = 300

        staff2 = Mock()
        staff2.user_id = 400

        mock_staff_repo.find_by_community_and_role.side_effect = [
            [manager_staff],  # managers
            [staff1, staff2]  # staff
        ]

        all_staff = [manager_staff, staff1, staff2]
        mock_staff_repo.find_by_community_id.return_value = all_staff

        # 模拟社区用户
        user1 = Mock()
        user1.user_id = 500

        user2 = Mock()
        user2.user_id = 600

        mock_user_repo.find_by_community_id.return_value = [user1, user2]

        use_case = FormatCommunityInfoUseCase()

        # Act
        result = use_case.execute(community, include_worker_stats=True)

        # Assert
        assert result.is_success
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['community_id'] == 1
        assert result.data['manager_count'] == 1
        assert result.data['staff_count'] == 2
        assert result.data['worker_count'] == 3
        assert result.data['user_count'] == 2

    @patch('app.application.use_cases.community.format_community_info_use_case.RepositoryFactory')
    def test_should_handle_missing_creator(self, mock_repo_factory):
        """应该处理缺少创建者的情况"""
        # Arrange
        mock_user_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        community = Mock()
        community.community_id = 1
        community.name = 'Test Community'
        community.description = 'Test Description'
        community.location = 'Test Location'
        community.location_lat = 40.7128
        community.location_lon = -74.0060
        community.province = 'Test Province'
        community.city = 'Test City'
        community.district = 'Test District'
        community.street = 'Test Street'
        community.creator_id = None  # 没有创建者
        community.manager_id = 200
        community.status = 1
        community.is_default = False
        community.is_blackhouse = False
        community.created_at = datetime.now()
        community.updated_at = datetime.now()

        manager_user = Mock()
        manager_user.user_id = 200
        manager_user.nickname = 'Manager'
        manager_user.avatar_url = 'manager.jpg'

        mock_user_repo.find_by_id.return_value = manager_user

        use_case = FormatCommunityInfoUseCase()

        # Act
        result = use_case.execute(community, include_worker_stats=False)

        # Assert
        assert result.is_success
        assert result.data['creator'] is None
        assert result.data['manager']['user_id'] == 200

    @patch('app.application.use_cases.community.format_community_info_use_case.RepositoryFactory')
    def test_should_handle_missing_manager(self, mock_repo_factory):
        """应该处理缺少主管的情况"""
        # Arrange
        mock_user_repo = Mock()
        mock_staff_repo = Mock()

        mock_repo_factory.get_user_repository.return_value = mock_user_repo
        mock_repo_factory.get_community_staff_repository.return_value = mock_staff_repo

        community = Mock()
        community.community_id = 1
        community.name = 'Test Community'
        community.description = 'Test Description'
        community.location = 'Test Location'
        community.location_lat = 40.7128
        community.location_lon = -74.0060
        community.province = 'Test Province'
        community.city = 'Test City'
        community.district = 'Test District'
        community.street = 'Test Street'
        community.creator_id = 100
        community.manager_id = None  # 没有主管
        community.status = 1
        community.is_default = False
        community.is_blackhouse = False
        community.created_at = datetime.now()
        community.updated_at = datetime.now()

        creator_user = Mock()
        creator_user.user_id = 100
        creator_user.nickname = 'Creator'
        creator_user.avatar_url = 'creator.jpg'

        mock_user_repo.find_by_id.return_value = creator_user

        use_case = FormatCommunityInfoUseCase()

        # Act
        result = use_case.execute(community, include_worker_stats=False)

        # Assert
        assert result.is_success
        assert result.data['creator']['user_id'] == 100
        assert result.data['manager'] is None
        assert result.data['manager_name'] is None