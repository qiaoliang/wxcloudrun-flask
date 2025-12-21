"""
社区事件服务单元测试
"""
import pytest
from wxcloudrun.community_event_service import CommunityEventService

class TestCommunityEventService:
    """社区事件服务测试类"""
    
    def test_create_event_invalid_user(self):
        """测试无效用户创建事件"""
        result = CommunityEventService.create_event(
            user_id=9999,
            community_id=1,
            title="测试事件"
        )
        
        assert result['success'] is False
        assert '用户不存在' in result['message']
    
    def test_get_community_stats_empty(self):
        """测试获取空社区统计"""
        result = CommunityEventService.get_community_stats(999)
        
        assert result['success'] is False
    
    def test_create_support_invalid_event(self):
        """测试对不存在的事件创建应援"""
        result = CommunityEventService.create_support(
            event_id=9999,
            supporter_id=1,
            support_content="测试应援"
        )
        
        assert result['success'] is False
        assert '事件不存在' in result['message']