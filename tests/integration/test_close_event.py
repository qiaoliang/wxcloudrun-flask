from app.application.use_cases.events.create_event_use_case import CreateEventUseCase
from app.application.use_cases.events.close_event_use_case import CloseEventUseCase
"""
关闭事件集成测试
测试事件关闭功能的各种场景
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.integration.conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS
from database.flask_models import db


class TestCloseEvent(IntegrationTestBase):
    """关闭事件集成测试"""

    def test_close_event_by_creator_success(self):
        """测试事件发起者关闭事件成功"""
        creator_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_by_creator')
            manager = self.create_standard_test_user(role=3, test_context='close_by_creator_manager')

            community = self.create_test_community(
                name='测试社区_close_by_creator',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='需要关闭的事件',
                description='这是一个需要关闭的测试事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(creator_phone_number)

        # 发送关闭事件请求
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '问题已解决，可以关闭事件了'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response)
        assert data['data']['event_id'] == event_id
        assert data['data']['closed_by'] > 0
        assert data['data']['closed_at'] is not None
        assert data['data']['closure_type'] == 1  # 用户关闭
        assert data['data']['closure_type_label'] == '用户关闭'

    def test_close_event_by_target_user_success(self):
        """测试目标用户关闭事件成功"""
        creator_phone_number = None
        target_user_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_by_target_creator')
            target_user = self.create_standard_test_user(role=1, test_context='close_by_target')
            manager = self.create_standard_test_user(role=3, test_context='close_by_target_manager')

            community = self.create_test_community(
                name='测试社区_close_by_target',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将用户添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id, target_user.user_id])

            # 创建事件，指定目标用户
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='针对目标用户的事件',
                description='这是一个针对特定用户的事件',
                event_type='call_for_help',
                target_user_id=target_user.user_id
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            target_user_phone_number = target_user.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(target_user_phone_number)

        # 目标用户发送关闭事件请求
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '我已经不需要帮助了，问题已经解决'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 打印响应数据用于调试
        print(f"Response status: {response.status_code}")
        print(f"Response data: {response.data}")

        # 验证响应
        data = self.assert_api_success(response)
        assert data['data']['event_id'] == event_id
        assert data['data']['closed_by'] > 0
        assert data['data']['closure_type'] == 1  # 用户关闭

    def test_close_event_by_staff_success(self):
        """测试社区工作人员关闭事件成功"""
        creator_phone_number = None
        staff_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_by_staff_creator')
            staff = self.create_standard_test_user(role=2, test_context='close_by_staff')
            manager = self.create_standard_test_user(role=3, test_context='close_by_staff_manager')

            community = self.create_test_community(
                name='测试社区_close_by_staff',
                creator=manager
            )

            # 添加主管和工作人员到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)
            self.add_community_staff(community.community_id, staff.user_id, 'staff', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='需要工作人员处理的事件',
                description='这是一个需要工作人员介入的事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            staff_phone_number = staff.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(staff_phone_number)

        # 工作人员发送关闭事件请求
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '工作人员已处理完毕，问题已解决'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response)
        assert data['data']['event_id'] == event_id
        assert data['data']['closed_by'] > 0
        assert data['data']['closed_at'] is not None
        assert data['data']['closure_type'] == 2  # 工作人员关闭
        assert data['data']['closure_type_label'] == '工作人员关闭'

    def test_close_event_by_unauthorized_user_fail(self):
        """测试无权限用户关闭事件失败"""
        creator_phone_number = None
        unauthorized_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_unauthorized_creator')
            unauthorized_user = self.create_standard_test_user(role=1, test_context='close_unauthorized')
            manager = self.create_standard_test_user(role=3, test_context='close_unauthorized_manager')

            community = self.create_test_community(
                name='测试社区_close_unauthorized',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 只将创建者添加到社区，不添加无权限用户
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='无权限用户无法关闭的事件',
                description='这是一个只有特定人员才能关闭的事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            unauthorized_phone_number = unauthorized_user.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(unauthorized_phone_number)

        # 无权限用户发送关闭事件请求
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '我尝试关闭这个事件，但我没有权限'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '只有事件发起者、目标用户或社区工作人员可以关闭事件' in msg

    def test_close_already_closed_event_fail(self):
        """测试关闭已关闭的事件失败"""
        creator_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_already_closed_creator')
            manager = self.create_standard_test_user(role=3, test_context='close_already_closed_manager')

            community = self.create_test_community(
                name='测试社区_close_already_closed',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='已关闭的事件',
                description='这是一个已经关闭的事件',
                event_type='call_for_help'
            )

            # 第一次关闭事件
            close_result = CommunityEventService.close_event(
                event_id=event["event"]["event_id"],
                user_id=creator.user_id,
                closure_reason='第一次关闭，这是一个足够长的关闭原因'
            )

            print(f"第一次关闭结果: {close_result}")

            # 保存需要的值
            creator_phone_number = creator.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(creator_phone_number)

        # 尝试再次关闭已关闭的事件
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '尝试第二次关闭这个已经关闭的事件'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '事件当前状态为' in msg and '无法关闭' in msg

    def test_close_event_with_short_reason_fail(self):
        """测试关闭原因过短失败"""
        creator_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_short_reason_creator')
            manager = self.create_standard_test_user(role=3, test_context='close_short_reason_manager')

            community = self.create_test_community(
                name='测试社区_close_short_reason',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='需要关闭的事件',
                description='这是一个测试事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(creator_phone_number)

        # 发送关闭事件请求，关闭原因少于10个字符
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': '太短'  # 只有4个字符，少于10
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '关闭原因格式错误' in msg or '关闭原因长度' in msg

    def test_close_event_with_long_reason_fail(self):
        """测试关闭原因过长失败"""
        creator_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_long_reason_creator')
            manager = self.create_standard_test_user(role=3, test_context='close_long_reason_manager')

            community = self.create_test_community(
                name='测试社区_close_long_reason',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='需要关闭的事件',
                description='这是一个测试事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(creator_phone_number)

        # 发送关闭事件请求，关闭原因超过500个字符
        long_reason = '这是一个非常长的关闭原因' * 50  # 超过500字符
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({
                'closure_reason': long_reason
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '关闭原因格式错误' in msg or '关闭原因长度' in msg

    def test_close_nonexistent_event_fail(self):
        """测试关闭不存在的事件失败"""
        user_phone_number = None
        nonexistent_event_id = 999999

        with self.app.app_context():
            # 创建用户
            user = self.create_standard_test_user(role=1, test_context='close_nonexistent')

            # 保存需要的值
            user_phone_number = user.phone_number

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(user_phone_number)

        # 尝试关闭不存在的事件
        response = client.put(
            f'/api/events/{nonexistent_event_id}/close',
            data=json.dumps({
                'closure_reason': '尝试关闭不存在的事件'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '不存在' in msg

    def test_close_event_without_reason_fail(self):
        """测试缺少关闭原因失败"""
        creator_phone_number = None
        event_id = None
        community_id = None

        with self.app.app_context():
            # 创建用户和社区
            creator = self.create_standard_test_user(role=1, test_context='close_no_reason_creator')
            manager = self.create_standard_test_user(role=3, test_context='close_no_reason_manager')

            community = self.create_test_community(
                name='测试社区_close_no_reason',
                creator=manager
            )

            # 添加主管到社区
            self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

            # 将创建者添加到社区
            from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
            CommunityService.add_users_to_community(community.community_id, [creator.user_id])

            # 创建事件
                        event = CommunityEventService.create_event(
                user_id=creator.user_id,
                community_id=community.community_id,
                title='需要关闭的事件',
                description='这是一个测试事件',
                event_type='call_for_help'
            )

            # 保存需要的值
            creator_phone_number = creator.phone_number
            event_id = event["event"]["event_id"]
            community_id = community.community_id

            # 显式提交到外层事务
            self.db.session.commit()

        client = self.get_test_client()
        token = self.get_jwt_token(creator_phone_number)

        # 发送关闭事件请求，不提供关闭原因
        response = client.put(
            f'/api/events/{event_id}/close',
            data=json.dumps({}),  # 空的请求体
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应应该失败
        data = self.assert_api_error(response, expected_code=0)
        msg = data['msg'] if isinstance(data['msg'], str) else data['msg'].get('error', '')
        assert '缺少关闭原因' in msg or msg == 'error'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])