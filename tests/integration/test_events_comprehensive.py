"""
事件管理模块集成测试 - 覆盖所有6个API端点
测试事件的创建、查询、应援、回应、位置更新和关闭等功能
"""
import json
import pytest
from datetime import datetime, timedelta
from tests.integration.conftest import IntegrationTestBase


class TestEventsComprehensive(IntegrationTestBase):
    """事件管理模块综合集成测试"""

    # ==================== 1. POST /api/events - 创建社区事件 ====================

    def test_create_event_success_help_type(self):
        """测试创建社区事件 - 求助类型成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_event_help')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_event_help',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_event_help_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 创建求助事件
            response = client.post(
                '/api/events',
                data=json.dumps({
                    'community_id': community.community_id,
                    'event_type': 'call_for_help',
                    'title': '紧急求助',
                    'description': '需要帮助处理紧急情况'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            if response.status_code != 200 or json.loads(response.data).get('code') != 1:
                print(f"API Error: {response.data.decode('utf-8')}")
            data = self.assert_api_success(response)
            # API 返回的数据结构是 {'event': {...}}
            assert 'event' in data['data']
            assert 'event_id' in data['data']['event']
            assert data['data']['event']['event_id'] > 0

    def test_create_event_success_support_type(self):
        """测试创建社区事件 - 应援类型成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_event_support')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_event_support',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_event_support_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 创建应援事件
            response = client.post(
                '/api/events',
                data=json.dumps({
                    'community_id': community.community_id,
                    'event_type': 'supporting',
                    'title': '提供帮助',
                    'description': '我可以提供帮助'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            if response.status_code != 200 or json.loads(response.data).get('code') != 1:
                print(f"API Error: {response.data.decode('utf-8')}")
            data = self.assert_api_success(response)
            # API 返回的数据结构是 {'event': {...}}
            assert 'event' in data['data']
            assert 'event_id' in data['data']['event']

    def test_create_event_missing_required_fields(self):
        """测试创建社区事件 - 缺少必填字段"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_event_missing_fields')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_event_missing',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_event_missing_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 缺少title字段
            response = client.post(
                '/api/events',
                data=json.dumps({
                    'community_id': community.community_id,
                    'event_type': 'call_for_help'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_create_event_not_community_member(self):
        """测试创建社区事件 - 用户不是社区成员"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_event_not_member')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_event_not_member',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户（不添加到社区）
            user = self.create_standard_test_user(role=1, test_context='create_event_not_member_user')

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 尝试创建事件
            response = client.post(
                '/api/events',
                data=json.dumps({
                    'community_id': community.community_id,
                    'event_type': 'call_for_help',
                    'title': '测试事件'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应（用户不是社区成员）
            self.assert_api_error(response, expected_code=0)

    # ==================== 2. GET /api/events/{event_id} - 获取事件详情 ====================

    def test_get_event_detail_success(self):
        """测试获取事件详情 - 成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('get_event_detail_success')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_get_event_detail',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='get_event_detail_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='测试事件',
                description='这是一个测试事件',
                status=1  # pending
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 获取事件详情
            response = client.get(
                f'/api/events/{event.event_id}',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'event' in data['data']
            assert data['data']['event']['event_id'] == event.event_id
            assert 'supports' in data['data']

    def test_get_event_detail_not_found(self):
        """测试获取事件详情 - 事件不存在"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('get_event_detail_not_found')

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 获取不存在的事件
            response = client.get(
                '/api/events/999999',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_get_event_detail_not_staff(self):
        """测试获取事件详情 - 用户不是社区工作人员"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('get_event_detail_not_staff')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_get_event_detail_not_staff',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='get_event_detail_not_staff_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='测试事件',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 普通用户尝试获取事件详情（需要工作人员权限）
            response = client.get(
                f'/api/events/{event.event_id}',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应（权限不足）
            self.assert_api_error(response, expected_code=0)

    # ==================== 3. POST /api/events/{event_id}/support - 创建事件应援 ====================

    def test_create_event_support_success(self):
        """测试创建事件应援 - 成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_event_support_success')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_support',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_support_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                description='紧急情况',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 创建应援
            response = client.post(
                f'/api/events/{event.event_id}/support',
                data=json.dumps({
                    'message_content': '我可以提供帮助'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)

    def test_create_event_support_missing_message(self):
        """测试创建事件应援 - 缺少应援内容"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_support_missing_message')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_support_missing',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_support_missing_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 缺少message_content字段
            response = client.post(
                f'/api/events/{event.event_id}/support',
                data=json.dumps({}),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_create_event_support_empty_message(self):
        """测试创建事件应援 - 应援内容为空"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('create_support_empty_message')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_create_support_empty',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='create_support_empty_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 应援内容为空
            response = client.post(
                f'/api/events/{event.event_id}/support',
                data=json.dumps({
                    'message_content': '   '  # 只有空格
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    # ==================== 4. POST /api/events/{event_id}/respond - 工作人员添加回应 ====================

    def test_add_staff_response_success(self):
        """测试工作人员添加回应 - 成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('add_response_success')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_add_response',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='add_response_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                description='紧急情况',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 添加回应
            response = client.post(
                f'/api/events/{event.event_id}/respond',
                data=json.dumps({
                    'content': '我们正在处理这个问题'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)

    def test_add_staff_response_with_media(self):
        """测试工作人员添加回应 - 带媒体文件"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('add_response_media')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_add_response_media',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='add_response_media_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 添加带媒体的回应
            response = client.post(
                f'/api/events/{event.event_id}/respond',
                data=json.dumps({
                    'content': '问题已解决',
                    'media_url': 'https://example.com/photo.jpg',
                    'message_tags': ['resolved']
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)

    def test_add_staff_response_not_staff(self):
        """测试工作人员添加回应 - 用户不是工作人员"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('add_response_not_staff')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_add_response_not_staff',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='add_response_not_staff_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 普通用户尝试添加回应
            response = client.post(
                f'/api/events/{event.event_id}/respond',
                data=json.dumps({
                    'content': '我可以帮忙'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应（权限不足）
            self.assert_api_error(response, expected_code=0)

    # ==================== 5. PUT /api/events/{event_id}/location - 更新事件位置 ====================

    def test_update_event_location_success_with_address(self):
        """测试更新事件位置 - 带地址描述成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('update_location_address')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_update_location_address',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='update_location_address_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 更新事件位置（带地址）
            response = client.put(
                f'/api/events/{event.event_id}/location',
                data=json.dumps({
                    'location': '北京市朝阳区某某街道123号',
                    'location_lat': 39.9042,
                    'location_lon': 116.4074
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)

    def test_update_event_location_success_with_coordinates(self):
        """测试更新事件位置 - 只提供坐标成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('update_location_coords')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_update_location_coords',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='update_location_coords_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 更新事件位置（只提供坐标）
            response = client.put(
                f'/api/events/{event.event_id}/location',
                data=json.dumps({
                    'location_lat': 39.9042,
                    'location_lon': 116.4074
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)

    def test_update_event_location_missing_location_info(self):
        """测试更新事件位置 - 缺少位置信息"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('update_location_missing')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_update_location_missing',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='update_location_missing_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 不提供任何位置信息
            response = client.put(
                f'/api/events/{event.event_id}/location',
                data=json.dumps({}),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_update_event_location_not_community_member(self):
        """测试更新事件位置 - 用户不是社区成员"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('update_location_not_member')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_update_location_not_member',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户（不添加到社区）
            user = self.create_standard_test_user(role=1, test_context='update_location_not_member_user')

            # 创建求助事件（使用admin用户）
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            from database.flask_models import CommunityEvent
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [admin['user_id']])

            event = CommunityEvent(
                community_id=community.community_id,
                created_by=admin['user_id'],
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 非社区成员尝试更新位置
            response = client.put(
                f'/api/events/{event.event_id}/location',
                data=json.dumps({
                    'location': '测试地址'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应（权限不足）
            self.assert_api_error(response, expected_code=0)

    # ==================== 6. PUT /api/events/{event_id}/close - 关闭事件 ====================

    def test_close_event_success_by_user(self):
        """测试关闭事件 - 用户关闭成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('close_event_user')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_close_event_user',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='close_event_user_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                description='紧急情况',
                status=1  # pending
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 用户关闭事件
            response = client.put(
                f'/api/events/{event.event_id}/close',
                data=json.dumps({
                    'closure_reason': '问题已经解决了，感谢大家的帮助'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'event_id' in data['data']
            assert 'closed_by' in data['data']
            assert 'closure_type' in data['data']
            assert 'closure_reason' in data['data']

    def test_close_event_success_by_staff(self):
        """测试关闭事件 - 工作人员关闭成功场景"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('close_event_staff')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_close_event_staff',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='close_event_staff_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1  # pending
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(admin['phone_number'])

            # 工作人员关闭事件
            response = client.put(
                f'/api/events/{event.event_id}/close',
                data=json.dumps({
                    'closure_reason': '社区工作人员已处理完毕'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'event_id' in data['data']
            assert data['data']['closed_by'] == admin['user_id']

    def test_close_event_missing_reason(self):
        """测试关闭事件 - 缺少关闭原因"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('close_event_missing_reason')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_close_event_missing',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='close_event_missing_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 缺少closure_reason字段
            response = client.put(
                f'/api/events/{event.event_id}/close',
                data=json.dumps({}),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_close_event_empty_reason(self):
        """测试关闭事件 - 关闭原因为空"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('close_event_empty_reason')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_close_event_empty',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='close_event_empty_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=1
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 关闭原因为空
            response = client.put(
                f'/api/events/{event.event_id}/close',
                data=json.dumps({
                    'closure_reason': '   '  # 只有空格
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应
            self.assert_api_error(response, expected_code=0)

    def test_close_event_already_closed(self):
        """测试关闭事件 - 事件已关闭"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('close_event_already_closed')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_close_event_closed',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 添加社区专员
            self.add_community_staff(
                community.community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户
            user = self.create_standard_test_user(role=1, test_context='close_event_closed_user')

            # 添加用户到社区
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community.community_id, [user.user_id])

            # 创建已关闭的求助事件
            from database.flask_models import CommunityEvent
            event = CommunityEvent(
                community_id=community.community_id,
                created_by=user.user_id,
                target_user_id=user.user_id,
                event_type='call_for_help',
                title='需要帮助',
                status=2  # closed
            )
            self.db.session.add(event)
            self.db.session.commit()
            self.db.session.refresh(event)

            client = self.get_test_client()
            token = self.get_jwt_token(user.phone_number)

            # 尝试关闭已关闭的事件
            response = client.put(
                f'/api/events/{event.event_id}/close',
                data=json.dumps({
                    'closure_reason': '再次关闭'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证错误响应（事件已关闭）
            self.assert_api_error(response, expected_code=0)

    # ==================== 7. Deprecated API Tests ====================

    def test_old_community_stats_deprecated_warning(self):
        """测试旧 API: GET /api/communities/<id>/stats - 验证 deprecation 警告和弃用日期"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('old_stats_deprecated')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_old_stats',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 保存社区ID
            community_id = community.community_id

            # 添加社区专员
            self.add_community_staff(
                community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户并添加到社区
            user = self.create_standard_test_user(role=1, test_context='old_stats_user')
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community_id, [user.user_id])

            # 保存用户电话
            user_phone = user.phone_number

        client = self.get_test_client()
        token = self.get_jwt_token(user_phone)

        # 使用旧 API 获取社区统计
        response = client.get(
            f'/api/communities/{community_id}/stats',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应成功
        self.assert_api_success(response)

        # 验证 deprecation 警告头
        assert 'Deprecation' in response.headers
        assert 'Warning' in response.headers
        assert 'X-Deprecated-Since' in response.headers
        assert response.headers['X-Deprecated-Since'] == '2026-01-20'

    def test_old_pending_events_deprecated_warning(self):
        """测试旧 API: GET /api/communities/<id>/pending-events - 验证 deprecation 警告和弃用日期"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('old_pending_deprecated')

            # 创建社区
            from database.flask_models import Community
            community = Community(
                name='测试社区_old_pending',
                description='用于测试的社区',
                creator_id=admin['user_id']
            )
            self.db.session.add(community)
            self.db.session.commit()
            self.db.session.refresh(community)

            # 保存社区ID
            community_id = community.community_id

            # 添加社区专员
            self.add_community_staff(
                community_id,
                admin['user_id'],
                role='staff',
                operator_id=admin['user_id']
            )

            # 创建普通用户并添加到社区
            user = self.create_standard_test_user(role=1, test_context='old_pending_user')
            from app.application.use_cases.community.add_users_to_community_use_case import AddUsersToCommunityUseCase
            add_users_use_case = AddUsersToCommunityUseCase()
            add_users_use_case.execute(community_id, [user.user_id])

            # 保存管理员电话
            admin_phone = admin['phone_number']

        client = self.get_test_client()
        token = self.get_jwt_token(admin_phone)

        # 使用旧 API 获取未处理事件
        response = client.get(
            f'/api/communities/{community_id}/pending-events',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应成功
        self.assert_api_success(response)

        # 验证 deprecation 警告头
        assert 'Deprecation' in response.headers
        assert 'Warning' in response.headers
        assert 'X-Deprecated-Since' in response.headers
        assert response.headers['X-Deprecated-Since'] == '2026-01-20'