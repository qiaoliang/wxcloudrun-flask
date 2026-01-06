"""
社区事件服务单元测试
"""
import pytest
from flask import Flask
from database.flask_models import db, CommunityEvent
from wxcloudrun.community_event_service import CommunityEventService

class TestCommunityEventService:
    """社区事件服务测试类"""
    
    def test_create_event_invalid_user(self, test_app):
        """测试无效用户创建事件"""
        with test_app.app_context():
            result = CommunityEventService.create_event(
                user_id=9999,
                community_id=1,
                title="测试事件"
            )
            
            assert result['success'] is False
            assert '用户不存在' in result['message']
    
    def test_get_community_stats_empty(self, test_app):
        """测试获取空社区统计"""
        with test_app.app_context():
            result = CommunityEventService.get_community_stats(999)
            
            assert result['success'] is False
    
    def test_create_support_invalid_event(self, test_app):
        """测试对不存在的事件创建应援"""
        with test_app.app_context():
            result = CommunityEventService.create_support(
                event_id=9999,
                sender_id=1,
                message_content="测试应援"
            )

            assert result['success'] is False
            assert '事件不存在' in result['message']
    
    def test_close_event_by_creator(self, test_app, test_user, test_community):
        """测试事件发起者关闭事件"""
        with test_app.app_context():
            # 创建测试事件
            event = CommunityEvent(
                community_id=test_community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=1,  # 进行中
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 关闭事件
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=test_user.user_id,
                closure_reason="测试关闭原因：用户自己关闭，长度符合要求"
            )
            
            assert result['code'] == 1
            assert result['data']['closure_type'] == 1  # 用户关闭
            assert result['data']['closed_by'] == test_user.user_id
            
            # 验证数据库更新
            db.session.refresh(event)
            assert event.status == 2  # 已完成
            assert event.closed_by == test_user.user_id
            assert event.closure_type == 1
            assert event.closure_reason == "测试关闭原因：用户自己关闭，长度符合要求"
    
    def test_close_event_by_staff(self, test_app, test_user):
        """测试社区工作人员关闭事件"""
        with test_app.app_context():
            from database.flask_models import CommunityStaff
            from test_utils import create_test_user, create_test_community
            
            # 为每个测试创建独立的社区
            community = create_test_community(db.session, name_suffix="test_close_event_by_staff")
            
            # 创建工作人员用户（使用 test_context 确保唯一性）
            staff = create_test_user(db.session, test_context="test_close_event_by_staff")
            
            # 添加工作人员到社区
            staff_relation = CommunityStaff(
                community_id=community.community_id,
                user_id=staff.user_id,
                role='staff'
            )
            db.session.add(staff_relation)
            db.session.flush()
            
            # 创建测试事件
            event = CommunityEvent(
                community_id=community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=1,  # 进行中
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 工作人员关闭事件
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=staff.user_id,
                closure_reason="测试关闭原因：工作人员解决，长度符合要求"
            )
            
            assert result['code'] == 1
            assert result['data']['closure_type'] == 2  # 工作人员关闭
            assert result['data']['closed_by'] == staff.user_id
            
            # 验证数据库更新
            db.session.refresh(event)
            assert event.status == 2  # 已完成
            assert event.closed_by == staff.user_id
            assert event.closure_type == 2
            assert event.closure_reason == "测试关闭原因：工作人员解决，长度符合要求"
    
    def test_close_event_invalid_closure_reason_too_short(self, test_app, test_user):
        """测试关闭原因太短"""
        with test_app.app_context():
            from test_utils import create_test_community
            
            # 为每个测试创建独立的社区
            community = create_test_community(db.session, name_suffix="test_close_event_invalid_closure_reason_too_short")
            
            # 创建测试事件
            event = CommunityEvent(
                community_id=community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=1,
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 关闭原因太短
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=test_user.user_id,
                closure_reason="太短"
            )
            
            assert result['code'] == 0
            assert '关闭原因长度必须在10-500字符之间' in result['data']['error']
    
    def test_close_event_invalid_closure_reason_too_long(self, test_app, test_user):
        """测试关闭原因太长"""
        with test_app.app_context():
            from test_utils import create_test_community
            
            # 为每个测试创建独立的社区
            community = create_test_community(db.session, name_suffix="test_close_event_invalid_closure_reason_too_long")
            
            # 创建测试事件
            event = CommunityEvent(
                community_id=community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=1,
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 关闭原因太长
            long_reason = "a" * 501
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=test_user.user_id,
                closure_reason=long_reason
            )
            
            assert result['code'] == 0
            assert '关闭原因长度必须在10-500字符之间' in result['data']['error']
    
    def test_close_event_already_closed(self, test_app, test_user):
        """测试关闭已关闭的事件"""
        with test_app.app_context():
            from test_utils import create_test_community
            
            # 为每个测试创建独立的社区
            community = create_test_community(db.session, name_suffix="test_close_event_already_closed")
            
            # 创建测试事件（已关闭）
            event = CommunityEvent(
                community_id=community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=2,  # 已完成
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 尝试关闭已关闭的事件
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=test_user.user_id,
                closure_reason="测试关闭原因"
            )
            
            assert result['code'] == 0
            assert '事件已关闭' in result['msg']
    
    def test_close_event_no_permission(self, test_app, test_user):
        """测试无权限关闭事件"""
        with test_app.app_context():
            from test_utils import create_test_user, create_test_community
            
            # 为每个测试创建独立的社区
            community = create_test_community(db.session, name_suffix="test_close_event_no_permission")
            
            # 创建其他用户
            other_user = create_test_user(db.session, test_context="test_close_event_no_permission")
            
            # 创建测试事件
            event = CommunityEvent(
                community_id=community.community_id,
                title="测试事件",
                description="测试描述",
                event_type='call_for_help',
                status=1,  # 进行中
                target_user_id=test_user.user_id,
                created_by=test_user.user_id
            )
            db.session.add(event)
            db.session.flush()
            
            # 其他用户尝试关闭事件（无权限）
            result = CommunityEventService.close_event(
                event_id=event.event_id,
                user_id=other_user.user_id,
                closure_reason="测试关闭原因：无权限用户尝试关闭事件，长度符合要求"
            )
            
            assert result['code'] == 0
            assert '无权限关闭事件' in result['msg']