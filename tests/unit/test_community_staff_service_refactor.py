"""
测试社区工作人员角色管理重构功能
"""
import pytest
from database.flask_models import db, User, Community, CommunityStaff
from wxcloudrun.community_staff_service import CommunityStaffService
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from const_default import DEFAULT_COMMUNITY_ID

class TestRoleRecalculation:
    """测试用户角色重新计算功能"""

    def test_recalculate_role_from_solo_to_staff(self, test_session, test_app):
        """测试从普通用户到专员的role计算"""
        test_context = "test_solo_to_staff"
        with test_app.app_context():
            # 创建测试用户（普通用户）
            phone = f"138{test_context}0001"
            user = User(
                wechat_openid=f"openid_{test_context}_1",
                nickname=f"test_user_{test_context}_1",
                phone_number=phone,
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )
            test_session.add(user)
            test_session.commit()

            # 创建社区
            community = Community(
                name=f'{test_context}_测试社区',
                description='测试',
                creator_id=1
            )
            test_session.add(community)
            test_session.commit()

            # 添加为专员
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_STAFF
            )
            test_session.add(staff)
            test_session.commit()

            # 调用重新计算方法
            CommunityStaffService._recalculate_user_role(user.user_id)

            # 验证角色已更新为专员
            test_session.refresh(user)
            assert user.role == Role.STAFF

    def test_recalculate_role_from_staff_to_manager(self, test_session, test_app):
        """测试从专员到主管的role计算"""
        test_context = "test_staff_to_manager"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0002",
                role=Role.STAFF,
                status=1
            )
            test_session.add(user)

            community_a = Community(name=f'{test_context}_A', description='A', creator_id=1)
            community_b = Community(name=f'{test_context}_B', description='B', creator_id=1)
            test_session.add_all([community_a, community_b])
            test_session.commit()

            # 添加为两个社区的工作人员
            staff_a = CommunityStaff(
                community_id=community_a.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_STAFF
            )
            staff_b = CommunityStaff(
                community_id=community_b.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_MANAGER
            )
            test_session.add_all([staff_a, staff_b])
            test_session.commit()

            # 重新计算
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 应该是主管（取最高角色）
            assert new_role == Role.MANAGER
            test_session.refresh(user)
            assert user.role == Role.MANAGER

    def test_recalculate_role_preserve_super_admin(self, test_session, test_app):
        """测试超级管理员角色不会被降级"""
        test_context = "test_preserve_super_admin"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0003",
                role=Role.SUPER_ADMIN,
                status=1
            )
            test_session.add(user)

            community = Community(name=f'{test_context}', description='test', creator_id=1)
            test_session.add(community)
            test_session.commit()

            # 移除所有工作人员身份（假设有）
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 角色应该保持为超级管理员
            assert new_role == Role.SUPER_ADMIN
            test_session.refresh(user)
            assert user.role == Role.SUPER_ADMIN

    def test_recalculate_role_no_staff_records(self, test_session, test_app):
        """测试无工作人员记录时降级为普通用户"""
        test_context = "test_no_staff_records"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0004",
                role=Role.STAFF,
                status=1
            )
            test_session.add(user)
            test_session.commit()

            # 重新计算（无工作人员记录）
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 应该降级为普通用户
            assert new_role == Role.SOLO
            test_session.refresh(user)
            assert user.role == Role.SOLO
