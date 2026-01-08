"""
测试工作人员角色管理集成测试
"""
import pytest
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import db, User, Community, CommunityStaff
from .conftest import IntegrationTestBase
from app.shared.constants.roles import Role


class TestStaffRoleManagementIntegration(IntegrationTestBase):
    """测试工作人员角色管理集成"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 获取或创建超级管理员（用于API调用权限）
            super_admin = cls.get_super_admin('staff_role_test')
            cls.super_admin_id = super_admin['user_id']
            cls.super_admin_phone = super_admin['phone_number']

            # 创建测试社区
            community = Community(
                community_id=800,
                name='staff_role_test_测试社区',
                description='测试社区',
                creator_id=cls.super_admin_id
            )
            db.session.add(community)
            db.session.commit()
            cls.community_id = community.community_id

            # 创建普通用户
            test_user = cls.create_standard_test_user(
                role=Role.SOLO,
                test_context='staff_role_test'
            )
            cls.test_user_id = test_user.user_id
            cls.test_user_phone = test_user.phone_number

    def test_add_staff_api(self):
        """测试添加工作人员API"""
        # 添加为专员
        response = self.make_authenticated_request(
            'POST',
            '/api/community/add-staff',
            data={
                'community_id': self.community_id,
                'user_ids': [self.test_user_id],
                'role': 'staff'
            },
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        # API returns code 1 for success
        assert data['code'] == 1
        assert data['data']['added_count'] == 1

    def test_set_super_admin_api(self):
        """测试设置超级管理员API"""
        # 创建一个主管用户
        with self.app.app_context():
            manager = self.create_standard_test_user(
                role=Role.MANAGER,
                test_context='set_super_admin_test'
            )
            manager_id = manager.user_id  # Save the ID before exiting context

        # 设置为超级管理员
        response = self.make_authenticated_request(
            'POST',
            '/api/community/set-super-admin',
            data={
                'target_user_id': manager_id,
                'is_super_admin': True
            },
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        # API returns code 1 for success
        assert data['code'] == 1