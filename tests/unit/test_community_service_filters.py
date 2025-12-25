"""
CommunityService.get_communities_with_filters 方法的单元测试
"""

import pytest
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from wxcloudrun.community_service import CommunityService
from database.flask_models import Community, db


class TestCommunityServiceFilters:
    """测试 CommunityService.get_communities_with_filters 方法"""

    def test_get_communities_with_filters_no_filters(self, test_session):
        """测试无筛选条件的社区列表获取"""
        # Arrange
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(None, page, per_page)
        
        # Assert
        assert isinstance(communities, list)
        assert isinstance(total, int)
        assert len(communities) <= per_page

    def test_get_communities_with_filters_with_name_filter(self, test_session):
        """测试按名称筛选社区"""
        # Arrange
        filters = {'name': '测试社区'}
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert
        assert isinstance(communities, list)
        assert isinstance(total, int)
        # 验证筛选结果包含关键词
        for community in communities:
            assert '测试社区' in community.name

    def test_get_communities_with_filters_with_status_filter(self, test_session):
        """测试按状态筛选社区"""
        # Arrange
        filters = {'status': 'active'}
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert
        assert isinstance(communities, list)
        assert isinstance(total, int)
        # 验证筛选结果状态正确
        for community in communities:
            assert community.status == 'active'

    def test_get_communities_with_filters_multiple_filters(self, test_session):
        """测试多个筛选条件"""
        # Arrange
        filters = {
            'name': '测试',
            'status': 'active'
        }
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert
        assert isinstance(communities, list)
        assert isinstance(total, int)
        # 验证筛选结果符合所有条件
        for community in communities:
            assert '测试' in community.name
            assert community.status == 'active'

    def test_get_communities_with_filters_pagination(self, test_session):
        """测试分页功能"""
        # Arrange
        filters = None
        per_page = 5
        
        # Act - 测试第一页
        communities1, total1 = CommunityService.get_communities_with_filters(filters, 1, per_page)
        
        # Assert - 第一页
        assert len(communities1) <= per_page
        assert isinstance(total1, int)
        
        # Act - 测试第二页
        communities2, total2 = CommunityService.get_communities_with_filters(filters, 2, per_page)
        
        # Assert - 第二页
        assert len(communities2) <= per_page
        assert total2 == total1  # 总数应该相同

    def test_get_communities_with_filters_default_parameters(self, test_session):
        """测试默认参数"""
        # Arrange - 不传递任何参数
        filters = None
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters)
        
        # Assert - 应该使用默认值
        assert isinstance(communities, list)
        assert isinstance(total, int)
        assert len(communities) <= 20  # 默认per_page=20

    def test_get_communities_with_filters_empty_filters(self, test_session):
        """测试空筛选条件"""
        # Arrange
        filters = {}
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert
        assert isinstance(communities, list)
        assert isinstance(total, int)
        # 空筛选条件应该返回所有社区

    def test_get_communities_with_filters_response_structure(self, test_session):
        """测试返回数据结构"""
        # Arrange
        filters = {'name': '测试'}
        page = 1
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert - 检查返回类型
        assert isinstance(communities, list)
        assert isinstance(total, int)
        
        # Assert - 检查社区对象结构
        if communities:
            community = communities[0]
            assert hasattr(community, 'community_id')
            assert hasattr(community, 'name')
            assert hasattr(community, 'description')
            assert hasattr(community, 'status')

    def test_get_communities_with_filters_invalid_page(self, test_session):
        """测试无效页码"""
        # Arrange
        filters = None
        page = 0  # 无效页码
        per_page = 10
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert - 应该自动修正为第1页
        assert isinstance(communities, list)
        assert isinstance(total, int)

    def test_get_communities_with_filters_invalid_per_page(self, test_session):
        """测试无效的每页数量"""
        # Arrange
        filters = None
        page = 1
        per_page = 0  # 无效的每页数量
        
        # Act
        communities, total = CommunityService.get_communities_with_filters(filters, page, per_page)
        
        # Assert - 应该使用默认值
        assert isinstance(communities, list)
        assert isinstance(total, int)
        assert len(communities) <= 20  # 默认per_page=20


if __name__ == '__main__':
    pytest.main([__file__])