"""
事件管理集成测试
Happy path: 成功创建事件、获取事件列表、创建应援
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS
from database.flask_models import db


class TestEventsOperations(IntegrationTestBase):
    """事件管理集成测试"""

    def test_create_event_success(self):
        """测试成功创建社区事件"""
        with self.app.app_context():
            # 创建用户和社区
            user = self.create_standard_test_user(role=1, test_context='create_event')
            manager = self.create_standard_test_user(role=3, test_context='create_event_manager')

            community = self.create_test_community(
                name='测试社区_events',
                creator=manager
            )

            # 将用户添加到社区
            from wxcloudrun.community_service import CommunityService
            CommunityService.add_users_to_community(community.community_id, [user.user_id])

            # 获取 phone_number，避免在 app_context 外访问 detached 对象
            phone_number = user.phone_number
            community_id = community.community_id

        client = self.get_test_client()
        token = self.get_jwt_token(phone_number)

        # 发送创建事件请求
        response = client.post(
            '/api/events',
            data=json.dumps({
                'community_id': community.community_id,
                'title': '紧急求助',
                'description': '老人需要帮助',
                'event_type': 'call_for_help',
                'location': 'XX小区3栋201'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['event'])
        assert data['data']['event']['title'] == '紧急求助'
        assert data['data']['event']['event_id'] > 0

    def test_get_community_events_success(self):
        """测试成功获取社区事件列表"""
        with self.app.app_context():
            # 创建用户和社区
            user = self.create_standard_test_user(role=1, test_context='get_events')
            manager = self.create_standard_test_user(role=3, test_context='get_events_manager')

            community = self.create_test_community(
                name='测试社区_get_events',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将用户添加到社区
            user.community_id = community.community_id
            db.session.commit()

            # 创建事件
            from wxcloudrun.community_event_service import CommunityEventService
            CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='测试事件1',
                description='这是一个测试事件',
                event_type='call_for_help'
            )
            CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='测试事件2',
                description='这是另一个测试事件',
                event_type='supporting'
            )

            # 获取 phone_number 和 community_id，避免在 app_context 外访问 detached 对象
            manager_phone_number = manager.phone_number
            community_id = community.community_id

        client = self.get_test_client()
        token = self.get_jwt_token(manager_phone_number)

        # 发送获取社区事件列表请求
        response = client.get(
            f'/api/communities/{community_id}/events',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['events'])
        assert len(data['data']['events']) >= 2

    def test_get_event_detail_success(self):
        """测试成功获取事件详情"""
        with self.app.app_context():
            # 创建用户和社区
            user = self.create_standard_test_user(role=1, test_context='get_event_detail')
            manager = self.create_standard_test_user(role=3, test_context='get_event_detail_manager')

            community = self.create_test_community(
                name='测试社区_event_detail',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将用户添加到社区
            user.community_id = community.community_id
            db.session.commit()

            # 创建事件
            from wxcloudrun.community_event_service import CommunityEventService
            event = CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='详细事件',
                description='这是一个需要详细信息的测试事件',
                event_type='call_for_help',
                location='XX小区5栋101'
            )

            # 获取 phone_number、event_id 和 community_id，避免在 app_context 外访问 detached 对象
            manager_phone_number = manager.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

        client = self.get_test_client()
        token = self.get_jwt_token(manager_phone_number)

        # 发送获取事件详情请求
        response = client.get(
            f'/api/events/{event_id}?community_id={community_id}',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['event'])
        assert data['data']['event']['event_id'] == event['event']['event_id']
        assert data['data']['event']['title'] == '详细事件'

    def test_create_event_support_success(self):
        """测试成功创建事件应援"""
        with self.app.app_context():
            # 创建用户和社区
            user = self.create_standard_test_user(role=1, test_context='create_support')
            supporter = self.create_standard_test_user(role=2, test_context='create_supporter')
            manager = self.create_standard_test_user(role=3, test_context='create_support_manager')

            community = self.create_test_community(
                name='测试社区_support',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)
            self.add_community_staff(community.community_id, supporter.user_id, 'staff', manager.user_id)

            # 将用户添加到社区
            user.community_id = community.community_id
            db.session.commit()

            # 创建事件
            from wxcloudrun.community_event_service import CommunityEventService
            event = CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='需要帮助',
                description='老人需要紧急帮助',
                event_type='call_for_help'
            )

            # 获取 phone_number、event_id 和 community_id，避免在 app_context 外访问 detached 对象
            supporter_phone_number = supporter.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

        client = self.get_test_client()
        token = self.get_jwt_token(supporter_phone_number)

        # 发送创建应援请求
        response = client.post(
            f'/api/events/{event_id}/support',
            data=json.dumps({
                'support_content': '我马上过去帮忙',
                'community_id': community.community_id
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['support'])
        assert data['data']['support']['support_content'] == '我马上过去帮忙'

    def test_get_community_stats_success(self):
        """测试成功获取社区事件统计"""
        with self.app.app_context():
            # 创建用户和社区
            user = self.create_standard_test_user(role=1, test_context='get_stats')
            manager = self.create_standard_test_user(role=3, test_context='get_stats_manager')

            community = self.create_test_community(
                name='测试社区_stats',
                creator=manager
            )

            # 将用户添加到社区
            from wxcloudrun.community_service import CommunityService
            CommunityService.add_users_to_community(community.community_id, [user.user_id])

            # 创建一些事件
            from wxcloudrun.community_event_service import CommunityEventService
            CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='事件1',
                description='描述1',
                event_type='call_for_help'
            )
            CommunityEventService.create_event(
                user_id=user.user_id,
                community_id=community.community_id,
                title='事件2',
                description='描述2',
                event_type='supporting'
            )

            # 获取 phone_number 和 community_id，避免在 app_context 外访问 detached 对象
            user_phone_number = user.phone_number
            community_id = community.community_id

        client = self.get_test_client()
        token = self.get_jwt_token(user_phone_number)

        # 发送获取社区统计请求
        response = client.get(
            f'/api/communities/{community_id}/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['active_events', 'support_count'])
        assert data['data']['active_events'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])