"""
测试工作人员角色管理集成测试
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from app import create_app
from database.flask_models import db, User, Community, CommunityStaff
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from const_default import DEFAULT_COMMUNITY_ID


class TestStaffRoleManagementIntegration:
    """测试工作人员角色管理集成"""

    def test_complete_staff_lifecycle(self):
        """测试完整的工作人员生命周期"""
        test_context = "test_lifecycle"
        app = create_app()
        app.config['TESTING'] = True

        with app.app_context():
            # 1. 创建超级管理员
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}0001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            # 2. 创建社区
            community = Community(
                community_id=800,
                name=f'{test_context}_测试社区',
                description='测试社区',
                creator_id=1
            )

            # 3. 创建普通用户
            user = User(
                wechat_openid=f"openid_{test_context}_user",
                nickname=f"user_{test_context}",
                phone_number=f"138{test_context}0002",
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            db.session.add_all([super_admin, community, user])
            db.session.commit()

        with app.test_client() as client:
            # 先登录获取token
            login_response = client.post('/api/auth/login_phone_password', json={
                'phone': '13900008000',
                'password': 'test123'
            })

            if login_response.status_code == 200:
                login_data = login_response.get_json()
                if login_data.get('code') == 1:
                    token = login_data['data']['token']
                    headers = {'Authorization': f'Bearer {token}'}

                    # 4. 添加为专员
                    response = client.post('/api/community/add-staff',
                        json={
                            'community_id': community.community_id,
                            'user_ids': [user.user_id],
                            'role': 'staff'
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['code'] == 0
                    assert data['data']['added_count'] == 1

                    with app.app_context():
                        db.session.refresh(user)
                        assert user.role == Role.STAFF
                        assert user.community_id == community.community_id

                    # 5. 升级为主管
                    response = client.post('/api/community/add-staff',
                        json={
                            'community_id': community.community_id,
                            'user_ids': [user.user_id],
                            'role': 'manager'
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    with app.app_context():
                        db.session.refresh(user)
                        assert user.role == Role.MANAGER

    def test_set_super_admin_api(self):
        """测试设置超级管理员API"""
        test_context = "test_api_super_admin"
        app = create_app()
        app.config['TESTING'] = True

        with app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}1001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            manager = User(
                wechat_openid=f"openid_{test_context}_manager",
                nickname=f"manager_{test_context}",
                phone_number=f"138{test_context}1002",
                role=Role.MANAGER,
                status=1
            )

            db.session.add_all([super_admin, manager])
            db.session.commit()

        with app.test_client() as client:
            # 先登录获取token
            login_response = client.post('/api/auth/login_phone_password', json={
                'phone': '13900008000',
                'password': 'test123'
            })

            if login_response.status_code == 200:
                login_data = login_response.get_json()
                if login_data.get('code') == 1:
                    token = login_data['data']['token']
                    headers = {'Authorization': f'Bearer {token}'}

                    # 设置为超级管理员
                    response = client.post('/api/community/set-super-admin',
                        json={
                            'target_user_id': manager.user_id,
                            'is_super_admin': True
                        },
                        headers=headers
                    )

                    assert response.status_code == 200
                    data = response.get_json()
                    assert data['code'] == 0

                    with app.app_context():
                        db.session.refresh(manager)
                        assert manager.role == Role.SUPER_ADMIN
