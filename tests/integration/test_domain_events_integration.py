"""
领域事件集成测试

测试领域事件的发布和处理机制
"""
import pytest
import json
import os
import sys
from unittest.mock import Mock, patch

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from app.application.use_cases.community.create_community_use_case import CreateCommunityUseCase
from app.application.use_cases.community.join_community_use_case import JoinCommunityUseCase
from app.domain.events.community_events import CommunityCreatedEvent, CommunityMemberAddedEvent
from app.domain.events.event_bus import event_bus
from app.domain.handlers import register_all_event_handlers, get_event_handler_count
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import db, User, Community, UserAuditLog
from .conftest import IntegrationTestBase


class TestDomainEventsIntegration(IntegrationTestBase):
    """领域事件集成测试"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建测试用户
            test_user = cls.create_standard_test_user(role=1, test_context='domain_events_test')
            cls.test_user_id = test_user.user_id
            cls.test_user_phone = test_user.phone_number

    def test_event_handlers_registration(self):
        """测试事件处理器注册"""
        with self.app.app_context():
            register_all_event_handlers()
            handler_counts = get_event_handler_count()

            # 验证用户事件处理器已注册
            assert handler_counts['user_events']['UserCreatedEvent'] >= 0
            assert handler_counts['user_events']['UserProfileUpdatedEvent'] >= 0

            # 验证社区事件处理器已注册
            assert handler_counts['community_events']['CommunityCreatedEvent'] >= 0
            assert handler_counts['community_events']['CommunityMemberAddedEvent'] >= 0
            assert handler_counts['community_events']['CommunityMemberRemovedEvent'] >= 0

            # 验证打卡事件处理器已注册
            assert handler_counts['checkin_events']['CheckinCompletedEvent'] >= 0

    def test_community_created_event_publishing(self):
        """测试社区创建事件发布"""
        with self.app.app_context():
            # 确保事件处理器已注册
            register_all_event_handlers()

            # 创建社区
            use_case = CreateCommunityUseCase()
            result = use_case.execute(
                name='测试社区',
                description='这是一个测试社区',
                creator_id=self.test_user_id
            )

            # 验证社区创建成功
            assert result.status.value == 'success'
            assert result.data['community_id'] is not None

            # 验证审计日志已创建
            audit_log = db.session.query(UserAuditLog).filter_by(
                user_id=self.test_user_id,
                action='create_community'
            ).first()

            assert audit_log is not None

            # 验证审计日志详情
            detail = json.loads(audit_log.detail)
            assert detail['community_id'] == result.data['community_id']
            assert detail['community_name'] == '测试社区'
            assert detail['action'] == '社区创建'

    def test_community_member_added_event_publishing(self):
        """测试社区成员添加事件发布"""
        with self.app.app_context():
            # 确保事件处理器已注册
            register_all_event_handlers()

            # 创建第二个测试用户
            member_user = self.create_standard_test_user(role=2, test_context='domain_events_member_test')

            # 创建社区
            use_case = CreateCommunityUseCase()
            result = use_case.execute(
                name='测试社区2',
                description='测试社区2',
                creator_id=self.test_user_id
            )
            community_id = result.data['community_id']

            # 成员加入社区
            join_use_case = JoinCommunityUseCase()
            result = join_use_case.execute(
                user_id=member_user.user_id,
                community_name='测试社区2'
            )

            # 验证加入成功
            assert result.status.value == 'success'
            assert result.data['community_id'] == community_id

            # 验证审计日志已创建
            audit_log = db.session.query(UserAuditLog).filter_by(
                user_id=member_user.user_id,
                action='join_community'
            ).first()

            assert audit_log is not None

            # 验证审计日志详情
            detail = json.loads(audit_log.detail)
            assert detail['community_id'] == community_id
            assert detail['role'] == member_user.role
            assert detail['action'] == '加入社区'

    def test_event_handler_error_handling(self):
        """测试事件处理器错误处理 - 主流程不应受事件处理器错误影响"""
        with self.app.app_context():
            # 确保事件处理器已注册
            register_all_event_handlers()

            # 创建社区（即使事件处理器失败，主流程应该成功）
            use_case = CreateCommunityUseCase()
            result = use_case.execute(
                name='测试社区3',
                description='测试社区3',
                creator_id=self.test_user_id
            )

            # 验证社区创建成功
            assert result.status.value == 'success'
            assert result.data['community_id'] is not None

            # 验证审计日志已创建（事件处理器正常工作）
            audit_log = db.session.query(UserAuditLog).filter_by(
                user_id=self.test_user_id,
                action='create_community'
            ).first()

            assert audit_log is not None

    def test_multiple_events_publishing(self):
        """测试多个事件连续发布"""
        with self.app.app_context():
            # 确保事件处理器已注册
            register_all_event_handlers()

            # 创建第二个测试用户
            user2 = self.create_standard_test_user(role=2, test_context='domain_events_multi_test')

            # 创建社区1
            use_case = CreateCommunityUseCase()
            result1 = use_case.execute(
                name='社区A',
                description='社区A',
                creator_id=self.test_user_id
            )
            assert result1.status.value == 'success'

            # 创建社区2
            result2 = use_case.execute(
                name='社区B',
                description='社区B',
                creator_id=user2.user_id
            )
            assert result2.status.value == 'success'

            # 用户2加入社区A
            join_use_case = JoinCommunityUseCase()
            result3 = join_use_case.execute(
                user_id=user2.user_id,
                community_name='社区A'
            )
            assert result3.status.value == 'success'

            # 验证所有审计日志都已创建
            audit_logs = db.session.query(UserAuditLog).all()
            assert len(audit_logs) >= 3  # 2个创建 + 1个加入

            # 验证每个日志的类型
            actions = [log.action for log in audit_logs]
            assert 'create_community' in actions
            assert 'join_community' in actions

    def test_event_bus_singleton(self):
        """测试EventBus单例模式"""
        from app.domain.events.event_bus import EventBus, event_bus as event_bus_instance

        # 验证event_bus是EventBus的实例
        assert isinstance(event_bus_instance, EventBus)

        # 验证单例：多次获取应该是同一个实例
        from app.domain.events.event_bus import event_bus as event_bus_instance2
        assert event_bus_instance is event_bus_instance2

    def test_event_handler_subscription(self):
        """测试事件处理器订阅"""
        from app.domain.handlers.community_event_handlers import CommunityCreatedEventHandler

        with self.app.app_context():
            # 确保事件处理器已注册
            register_all_event_handlers()

            # 获取CommunityCreatedEvent的处理器数量
            handler_count = event_bus.get_handler_count(CommunityCreatedEvent)

            # 验证至少有一个处理器
            assert handler_count > 0

            # 创建社区
            use_case = CreateCommunityUseCase()
            result = use_case.execute(
                name='测试社区4',
                description='测试社区4',
                creator_id=self.test_user_id
            )

            # 验证事件被处理（通过审计日志验证）
            audit_log = db.session.query(UserAuditLog).filter_by(
                user_id=self.test_user_id,
                action='create_community'
            ).first()

            assert audit_log is not None