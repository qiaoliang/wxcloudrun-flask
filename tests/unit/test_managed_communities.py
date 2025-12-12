"""
测试获取用户管理的社区列表及返回正确的角色信息
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.model import User, Community
from wxcloudrun.model_community_extensions import CommunityStaff
from wxcloudrun import db


class TestGetManagedCommunitiesReturnsCorrectRoles:
    """测试获取管理的社区列表返回正确的角色信息"""

    def test_get_managed_communities_returns_correct_roles(self, test_client):
        """
        RED阶段：测试get_managed_communities返回正确的角色信息
        验证用户在不同社区中的角色被正确标识
        """
        # 创建测试用户
        user = User(
            wechat_openid="multi_role_user",
            nickname="多角色用户",
            role=1  # 普通用户
        )
        db.session.add(user)
        db.session.flush()
        
        # 创建三个社区
        community_manager = Community(
            name="主管社区",
            description="用户是主管的社区",
            creator_user_id=1,
            status=1
        )
        community_staff = Community(
            name="专员社区",
            description="用户是专员的社区",
            creator_user_id=1,
            status=1
        )
        community_member = Community(
            name="成员社区",
            description="用户只是成员的社区",
            creator_user_id=1,
            status=1
        )
        community_inactive = Community(
            name="停用社区",
            description="已停用的社区",
            creator_user_id=1,
            status=0  # 停用状态
        )
        
        db.session.add_all([community_manager, community_staff, community_member, community_inactive])
        db.session.flush()
        
        # 设置用户在不同社区中的角色
        # 在主管社区中为主管
        manager_role = CommunityStaff(
            community_id=community_manager.community_id,
            user_id=user.user_id,
            role='manager'
        )
        db.session.add(manager_role)
        
        # 在专员社区中为专员
        staff_role = CommunityStaff(
            community_id=community_staff.community_id,
            user_id=user.user_id,
            role='staff'
        )
        db.session.add(staff_role)
        
        # 在成员社区中只是成员（没有Staff记录）
        from wxcloudrun.model_community_extensions import CommunityMember
        member_role = CommunityMember(
            community_id=community_member.community_id,
            user_id=user.user_id
        )
        db.session.add(member_role)
        
        db.session.commit()
        
        # 获取用户管理的社区列表
        managed_communities = user.get_managed_communities()
        
        # 验证返回的社区数量（应该只包含有管理权限的社区）
        assert len(managed_communities) == 2
        
        # 验证返回的社区包含主管社区和专员社区
        managed_community_ids = [c.community_id for c in managed_communities]
        assert community_manager.community_id in managed_community_ids
        assert community_staff.community_id in managed_community_ids
        assert community_member.community_id not in managed_community_ids
        assert community_inactive.community_id not in managed_community_ids
        
        # 验证每个社区的状态都是启用的
        for community in managed_communities:
            assert community.status == 1
        
        # 验证用户在每个管理社区中的角色
        for community in managed_communities:
            if community.community_id == community_manager.community_id:
                # 用户应该是主管
                assert user.is_primary_admin(community.community_id) == True
                assert user.is_community_admin(community.community_id) == True
            elif community.community_id == community_staff.community_id:
                # 用户应该是专员
                assert user.is_primary_admin(community.community_id) == False
                assert user.is_community_admin(community.community_id) == True
        
        print("✅ get_managed_communities返回正确的角色信息")

    def test_super_admin_gets_all_active_communities(self, test_client):
        """
        测试超级管理员获取所有活跃社区
        """
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin",
            nickname="超级管理员",
            role=4  # 超级管理员
        )
        db.session.add(super_admin)
        db.session.flush()
        
        # 创建多个社区，包括活跃和停用的
        active_community1 = Community(
            name="活跃社区1",
            description="活跃的社区1",
            creator_user_id=1,
            status=1
        )
        active_community2 = Community(
            name="活跃社区2",
            description="活跃的社区2",
            creator_user_id=1,
            status=1
        )
        inactive_community = Community(
            name="停用社区",
            description="已停用的社区",
            creator_user_id=1,
            status=0
        )
        
        db.session.add_all([active_community1, active_community2, inactive_community])
        db.session.commit()
        
        # 获取超级管理员管理的社区列表
        managed_communities = super_admin.get_managed_communities()
        
        # 验证只返回活跃社区
        assert len(managed_communities) == 2
        
        community_ids = [c.community_id for c in managed_communities]
        assert active_community1.community_id in community_ids
        assert active_community2.community_id in community_ids
        assert inactive_community.community_id not in community_ids
        
        # 验证超级管理员在所有社区中都有完全权限
        for community in managed_communities:
            assert super_admin.is_super_admin() == True
            assert super_admin.is_primary_admin(community.community_id) == True
            assert super_admin.can_manage_community(community.community_id) == True
        
        print("✅ 超级管理员获取所有活跃社区")

    def test_user_with_no_management_roles(self, test_client):
        """
        测试没有任何管理角色的用户
        """
        # 创建普通用户
        normal_user = User(
            wechat_openid="normal_user",
            nickname="普通用户",
            role=1
        )
        db.session.add(normal_user)
        db.session.flush()
        
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区",
            creator_user_id=1,
            status=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 用户只是社区成员，没有管理权限
        from wxcloudrun.model_community_extensions import CommunityMember
        member = CommunityMember(
            community_id=community.community_id,
            user_id=normal_user.user_id
        )
        db.session.add(member)
        db.session.commit()
        
        # 获取管理的社区列表
        managed_communities = normal_user.get_managed_communities()
        
        # 应该返回空列表
        assert len(managed_communities) == 0
        
        # 验证用户没有任何管理权限
        assert normal_user.can_manage_community(community.community_id) == False
        assert normal_user.is_community_admin(community.community_id) == False
        assert normal_user.is_primary_admin(community.community_id) == False
        
        print("✅ 无管理角色用户返回空列表")

    def test_role_priority_in_community_management(self, test_client):
        """
        测试社区管理中的角色优先级
        主管 > 专员 > 普通成员
        """
        # 创建用户
        user = User(
            wechat_openid="role_test_user",
            nickname="角色测试用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 创建社区
        community = Community(
            name="角色测试社区",
            description="用于测试角色优先级",
            creator_user_id=1,
            status=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 先设置为专员
        staff_role = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='staff'
        )
        db.session.add(staff_role)
        db.session.commit()
        
        # 验证专员权限
        assert user.is_community_admin(community.community_id) == True
        assert user.is_primary_admin(community.community_id) == False
        assert user.can_manage_community(community.community_id) == True
        
        # 升级为主管
        staff_role.role = 'manager'
        db.session.commit()
        
        # 验证主管权限（更高权限）
        assert user.is_community_admin(community.community_id) == True
        assert user.is_primary_admin(community.community_id) == True
        assert user.can_manage_community(community.community_id) == True
        
        # 移除管理角色
        db.session.delete(staff_role)
        db.session.commit()
        
        # 验证无管理权限
        assert user.is_community_admin(community.community_id) == False
        assert user.is_primary_admin(community.community_id) == False
        assert user.can_manage_community(community.community_id) == False
        
        print("✅ 角色优先级测试通过")


@pytest.fixture
def test_client():
    """创建测试客户端和数据库会话"""
    from wxcloudrun import app
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()