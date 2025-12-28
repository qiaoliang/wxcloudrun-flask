"""
社区申请集成测试
Happy path: 成功创建、批准和拒绝社区申请
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


class TestCommunityApplications(IntegrationTestBase):
    """社区申请集成测试"""

    def test_create_community_application_success(self):
        """测试成功创建社区申请"""
        with self.app.app_context():
            # 创建用户和社区
            applicant = self.create_standard_test_user(role=1, test_context='create_applicant')
            manager = self.create_standard_test_user(role=3, test_context='create_manager')

            community = self.create_test_community(
                name='测试社区_application',
                creator=manager
            )

            # 必须提交数据才能被 test_client 访问
            self.db.session.commit()

            # 在 app_context 内部提取 phone_number 和 community_id，避免 DetachedInstanceError
            applicant_phone = applicant.phone_number
            community_id = community.community_id

        # 获取申请人的token
        client = self.get_test_client()
        token = self.get_jwt_token(applicant_phone)

        # 发送创建申请请求
        response = client.post(
            '/api/community/applications',
            data=json.dumps({
                'community_id': community_id,
                'message': '我想加入这个社区'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['application_id', 'message'])
        assert data['data']['message'] == '申请提交成功'
        assert data['data']['application_id'] > 0

        def test_get_community_applications_success(self):
            """测试成功获取社区申请列表"""
            with self.app.app_context():
                # 创建用户和社区
                applicant = self.create_standard_test_user(role=1, test_context='get_applicant')
                manager = self.create_standard_test_user(role=3, test_context='get_manager')

                community = self.create_test_community(
                    name='测试社区_get_applications',
                    creator=manager
                )

                # 添加主管到社区
                self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

                # 创建社区申请
                from wxcloudrun.community_service import CommunityService
                application = CommunityService.create_community_application(
                    applicant.user_id,
                    community.community_id,
                    '我想加入这个社区'
                )

                # 必须提交数据才能被 test_client 访问
                self.db.session.commit()

                # 在 app_context 内部提取 phone_number，避免 DetachedInstanceError
                manager_phone = manager.phone_number

            # 获取主管的token
            client = self.get_test_client()
            token = self.get_jwt_token(manager_phone)

            # 发送获取申请列表请求
            response = client.get(
                '/api/community/applications',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['applications', 'total'])
            assert data['data']['total'] >= 1
            assert len(data['data']['applications']) >= 1

            # 验证返回的申请信息
            app_data = data['data']['applications'][0]
            assert app_data['application_id'] == application.application_id
            assert app_data['community_id'] == community.community_id
            assert app_data['applicant_id'] == applicant.user_id

        def test_approve_application_success(self):
            """测试成功批准社区申请"""
            with self.app.app_context():
                # 创建用户和社区
                applicant = self.create_standard_test_user(role=1, test_context='approve_applicant')
                manager = self.create_standard_test_user(role=3, test_context='approve_manager')

                community = self.create_test_community(
                    name='测试社区_approve',
                    creator=manager
                )

                # 添加主管到社区
                self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

                # 创建社区申请
                from wxcloudrun.community_service import CommunityService
                application = CommunityService.create_community_application(
                    applicant.user_id,
                    community.community_id,
                    '我想加入这个社区'
                )

                # 必须提交数据才能被 test_client 访问
                self.db.session.commit()

                # 在 app_context 内部提取 phone_number，避免 DetachedInstanceError
                manager_phone = manager.phone_number

            # 获取主管的token
            client = self.get_test_client()
            token = self.get_jwt_token(manager_phone)

            # 发送批准申请请求
            response = client.put(
                f'/api/community/applications/{application.application_id}/approve',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['message'])
            assert data['data']['message'] == '批准成功'

            # 验证用户已加入社区
            from database.flask_models import User
            with self.app.app_context():
                updated_applicant = self.db.session.get(User, applicant.user_id)
                assert updated_applicant.community_id == community.community_id

        def test_reject_application_success(self):
            """测试成功拒绝社区申请"""
            with self.app.app_context():
                # 创建用户和社区
                applicant = self.create_standard_test_user(role=1, test_context='reject_applicant')
                manager = self.create_standard_test_user(role=3, test_context='reject_manager')

                community = self.create_test_community(
                    name='测试社区_reject',
                    creator=manager
                )

                # 添加主管到社区
                self.add_community_staff(community.community_id, manager.user_id, 'manager', manager.user_id)

                # 创建社区申请
                from wxcloudrun.community_service import CommunityService
                application = CommunityService.create_community_application(
                    applicant.user_id,
                    community.community_id,
                    '我想加入这个社区'
                )

                # 必须提交数据才能被 test_client 访问
                self.db.session.commit()

                # 在 app_context 内部提取 phone_number，避免 DetachedInstanceError
                manager_phone = manager.phone_number

            # 获取主管的token
            client = self.get_test_client()
            token = self.get_jwt_token(manager_phone)

            # 发送拒绝申请请求
            response = client.put(
                f'/api/community/applications/{application.application_id}/reject',
                data=json.dumps({'reason': '社区已满'}),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['message'])
            assert data['data']['message'] == '拒绝成功'

            # 验证用户未加入社区
            from database.flask_models import User
            with self.app.app_context():
                updated_applicant = self.db.session.get(User, applicant.user_id)
                assert updated_applicant.community_id != community.community_id


if __name__ == '__main__':
        pytest.main([__file__, '-v'])