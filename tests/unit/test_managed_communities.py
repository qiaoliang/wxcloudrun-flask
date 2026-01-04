"""
测试获取用户管理的社区列表及返回正确的角色信息
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User, Community, CommunityStaff
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
from test_constants import TEST_CONSTANTS


class TestManagedCommunities:
    """测试用户管理的社区功能"""

    def test_user_as_manager_in_community(self, test_session):
        """测试用户作为社区主管"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_manager")
        openid = generate_unique_openid(phone_number, "test_manager")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_manager"),
            phone_number=phone_number,
            role=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("manager"),
            description=TEST_CONSTANTS.generate_community_description("manager"),
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 设置用户为社区主管
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='manager'
        )
        test_session.add(staff)
        test_session.commit()

        # 查询用户管理的社区（作为主管）
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id,
            CommunityStaff.role == 'manager'
        ).all()

        # 验证结果
        assert len(managed_communities) == 1
        assert managed_communities[0].community_id == community.community_id
        assert managed_communities[0].name == community.name

    def test_user_as_staff_in_community(self, test_session):
        """测试用户作为社区专员"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_staff")
        openid = generate_unique_openid(phone_number, "test_staff")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_staff"),
            phone_number=phone_number,
            role=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("staff"),
            description=TEST_CONSTANTS.generate_community_description("staff"),
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 设置用户为社区专员
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='staff'
        )
        test_session.add(staff)
        test_session.commit()

        # 查询用户管理的社区（作为专员）
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id,
            CommunityStaff.role == 'staff'
        ).all()

        # 验证结果
        assert len(managed_communities) == 1
        assert managed_communities[0].name == community.name

    def test_user_multiple_roles_in_different_communities(self, test_session):
        """测试用户在不同社区中有不同角色"""

        # 创建三个社区
        community1 = Community(
            name=TEST_CONSTANTS.generate_community_name("manager_role"),
            description="用户是主管的社区",
            creator_id=1
        )
        community2 = Community(
            name=TEST_CONSTANTS.generate_community_name("staff_role"),
            description="用户是专员的社区",
            creator_id=1
        )
        community3 = Community(
            name=TEST_CONSTANTS.generate_community_name("member_role"),
            description="用户只是成员的社区",
            creator_id=1
        )
        test_session.add_all([community1, community2, community3])
        test_session.flush()

        # 创建测试用户, 在第三个社区中是普通用户
        phone_number = generate_unique_phone_number("test_multi_role")
        openid = generate_unique_openid(phone_number, "test_multi_role")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_multi_role"),
            phone_number=phone_number,
            role=1,
            community_id=community3.community_id
        )
        test_session.add(user)
        test_session.flush()



        # 设置用户在不同社区中的角色
        # 在第一个社区中为主管
        manager_role = CommunityStaff(
            community_id=community1.community_id,
            user_id=user.user_id,
            role='manager'
        )
        test_session.add(manager_role)

        # 在第二个社区中为专员
        staff_role = CommunityStaff(
            community_id=community2.community_id,
            user_id=user.user_id,
            role='staff'
        )
        test_session.add(staff_role)

        test_session.commit()

        # 查询用户有管理权限的社区（主管或专员）
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id
        ).all()

        # 验证只返回有管理权限的社区
        assert len(managed_communities) == 2

        community_names = [c.name for c in managed_communities]
        assert community1.name in community_names
        assert community2.name in community_names

    def test_get_user_role_in_community(self, test_session):
        """测试获取用户在特定社区中的角色"""
        # 创建社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("role_test"),
            description="用于测试角色的社区",
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建测试用户
        phone_number = generate_unique_phone_number("test_role")
        openid = generate_unique_openid(phone_number, "test_role")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_role"),
            phone_number=phone_number,
            role=1,
            community_id=community.community_id
        )
        test_session.add(user)
        test_session.flush()


        # 设置用户为社区主管
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='manager'
        )
        test_session.add(staff)
        test_session.commit()

        # 查询用户在社区中的角色
        staff_record = test_session.query(CommunityStaff).filter(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.user_id == user.user_id
        ).first()

        # 验证角色
        assert staff_record is not None
        assert staff_record.role == 'manager'

    def test_inactive_communities_not_in_managed_list(self, test_session):
        """测试停用的社区不在管理列表中"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_inactive")
        openid = generate_unique_openid(phone_number, "test_inactive")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_inactive"),
            phone_number=phone_number,
            role=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建两个社区：一个活跃，一个停用
        active_community = Community(
            name=TEST_CONSTANTS.generate_community_name("active"),
            description="活跃的社区",
            creator_id=1,
            status=1  # 活跃
        )
        inactive_community = Community(
            name=TEST_CONSTANTS.generate_community_name("inactive"),
            description="已停用的社区",
            creator_id=1,
            status=0  # 停用
        )
        test_session.add_all([active_community, inactive_community])
        test_session.flush()

        # 在两个社区中都设置用户为主管
        staff1 = CommunityStaff(
            community_id=active_community.community_id,
            user_id=user.user_id,
            role='manager'
        )
        staff2 = CommunityStaff(
            community_id=inactive_community.community_id,
            user_id=user.user_id,
            role='manager'
        )
        test_session.add_all([staff1, staff2])
        test_session.commit()

        # 查询用户管理的活跃社区
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id,
            Community.status == 1  # 只查询活跃社区
        ).all()

        # 验证只返回活跃社区
        assert len(managed_communities) == 1
        assert managed_communities[0].name == active_community.name

    def test_user_with_no_managed_communities(self, test_session):
        """测试用户没有管理任何社区"""
        # 创建社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("no_manage"),
            description=TEST_CONSTANTS.generate_community_description("no_manage"),
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_no_manage")
        openid = generate_unique_openid(phone_number, "test_no_manage")
        
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_no_manage"),
            phone_number=phone_number,
            role=1,
            community_id=community.community_id
        )
        test_session.add(user)
        test_session.flush()


        # 查询用户管理的社区
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id
        ).all()

        # 验证用户没有管理任何社区
        assert len(managed_communities) == 0