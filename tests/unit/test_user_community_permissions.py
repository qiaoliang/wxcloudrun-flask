"""
测试用户基于社区角色的权限
验证用户在不同社区中的权限管理功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.model import User, Community
from wxcloudrun.model_community_extensions import CommunityStaff, CommunityMember
from wxcloudrun import db


class TestUserCommunityRolePermissions:
    """测试用户基于社区角色的权限"""

    def test_super_admin_has_full_permissions(self, test_client):
        """
        RED阶段：测试超级管理员拥有所有社区的完全权限
        """
        # 创建超级管理员用户
        super_admin = User(
            wechat_openid="super_admin",
            nickname="超级管理员",
            role=4  # 超级管理员角色
        )
        db.session.add(super_admin)
        db.session.flush()
        
        # 创建多个社区
        community1 = Community(
            name="社区1",
            description="第一个社区",
            creator_user_id=1
        )
        community2 = Community(
            name="社区2", 
            description="第二个社区",
            creator_user_id=1
        )
        db.session.add(community1)
        db.session.add(community2)
        db.session.flush()
        
        # 验证超级管理员身份
        assert super_admin.is_super_admin() == True
        
        # 验证超级管理员可以管理所有社区
        assert super_admin.can_manage_community(community1.community_id) == True
        assert super_admin.can_manage_community(community2.community_id) == True
        assert super_admin.is_community_admin(community1.community_id) == True
        assert super_admin.is_community_admin(community2.community_id) == True
        assert super_admin.is_primary_admin(community1.community_id) == True
        assert super_admin.is_primary_admin(community2.community_id) == True
        
        # 验证超级管理员管理的社区列表包含所有社区
        managed_communities = super_admin.get_managed_communities()
        assert len(managed_communities) >= 2
        
        community_ids = [c.community_id for c in managed_communities]
        assert community1.community_id in community_ids
        assert community2.community_id in community_ids
        
        print("✅ 超级管理员拥有所有社区的完全权限")

    def test_community_manager_permissions_only_in_managed_community(self, test_client):
        """
        测试社区主管只能管理其被分配的社区
        """
        # 创建普通用户
        manager = User(
            wechat_openid="manager_user",
            nickname="社区主管",
            role=1  # 普通用户
        )
        db.session.add(manager)
        db.session.flush()
        
        # 创建两个社区
        managed_community = Community(
            name="被管理的社区",
            description="主管管理的社区",
            creator_user_id=1
        )
        other_community = Community(
            name="其他社区",
            description="主管不管理的社区",
            creator_user_id=1
        )
        db.session.add(managed_community)
        db.session.add(other_community)
        db.session.flush()
        
        # 将用户设置为被管理社区的主管
        staff_role = CommunityStaff(
            community_id=managed_community.community_id,
            user_id=manager.user_id,
            role='manager'  # 社区主管
        )
        db.session.add(staff_role)
        db.session.commit()
        
        # 验证主管只能管理被分配的社区
        assert manager.can_manage_community(managed_community.community_id) == True
        assert manager.can_manage_community(other_community.community_id) == False
        
        # 验证管理员身份
        assert manager.is_community_admin(managed_community.community_id) == True
        assert manager.is_community_admin(other_community.community_id) == False
        
        # 验证主管身份
        assert manager.is_primary_admin(managed_community.community_id) == True
        assert manager.is_primary_admin(other_community.community_id) == False
        
        # 验证管理的社区列表只包含被分配的社区
        managed_communities = manager.get_managed_communities()
        assert len(managed_communities) == 1
        assert managed_communities[0].community_id == managed_community.community_id
        
        print("✅ 社区主管只能管理被分配的社区")

    def test_community_staff_permissions_only_in_assigned_community(self, test_client):
        """
        测试社区专员只能在其被分配的社区中拥有权限
        """
        # 创建普通用户
        staff = User(
            wechat_openid="staff_user",
            nickname="社区专员",
            role=1  # 普通用户
        )
        db.session.add(staff)
        db.session.flush()
        
        # 创建两个社区
        assigned_community = Community(
            name="分配的社区",
            description="专员工作的社区",
            creator_user_id=1
        )
        other_community = Community(
            name="其他社区",
            description="专员不工作的社区",
            creator_user_id=1
        )
        db.session.add(assigned_community)
        db.session.add(other_community)
        db.session.flush()
        
        # 将用户设置为分配社区的专员
        staff_role = CommunityStaff(
            community_id=assigned_community.community_id,
            user_id=staff.user_id,
            role='staff'  # 社区专员
        )
        db.session.add(staff_role)
        db.session.commit()
        
        # 验证专员只能在其被分配的社区中拥有权限
        assert staff.can_manage_community(assigned_community.community_id) == True
        assert staff.can_manage_community(other_community.community_id) == False
        
        # 验证管理员身份（专员也是管理员）
        assert staff.is_community_admin(assigned_community.community_id) == True
        assert staff.is_community_admin(other_community.community_id) == False
        
        # 验证不是主管
        assert staff.is_primary_admin(assigned_community.community_id) == False
        assert staff.is_primary_admin(other_community.community_id) == False
        
        # 验证管理的社区列表只包含被分配的社区
        managed_communities = staff.get_managed_communities()
        assert len(managed_communities) == 1
        assert managed_communities[0].community_id == assigned_community.community_id
        
        print("✅ 社区专员只能在被分配的社区中拥有权限")

    def test_normal_user_has_no_management_permissions(self, test_client):
        """
        测试普通用户没有任何管理权限
        """
        # 创建普通用户
        normal_user = User(
            wechat_openid="normal_user",
            nickname="普通用户",
            role=1  # 普通用户
        )
        db.session.add(normal_user)
        db.session.flush()
        
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 验证普通用户不是超级管理员
        assert normal_user.is_super_admin() == False
        
        # 验证普通用户没有任何管理权限
        assert normal_user.can_manage_community(community.community_id) == False
        assert normal_user.is_community_admin(community.community_id) == False
        assert normal_user.is_primary_admin(community.community_id) == False
        
        # 验证管理的社区列表为空
        managed_communities = normal_user.get_managed_communities()
        assert len(managed_communities) == 0
        
        print("✅ 普通用户没有任何管理权限")

    def test_user_can_have_different_roles_in_different_communities(self, test_client):
        """
        测试用户可以在不同社区中拥有不同的角色
        """
        # 创建用户
        user = User(
            wechat_openid="multi_role_user",
            nickname="多角色用户",
            role=1  # 普通用户
        )
        db.session.add(user)
        db.session.flush()
        
        # 创建三个社区
        community1 = Community(
            name="社区1",
            description="用户是主管的社区",
            creator_user_id=1
        )
        community2 = Community(
            name="社区2",
            description="用户是专员的社区",
            creator_user_id=1
        )
        community3 = Community(
            name="社区3",
            description="用户无角色的社区",
            creator_user_id=1
        )
        db.session.add(community1)
        db.session.add(community2)
        db.session.add(community3)
        db.session.flush()
        
        # 在社区1中设置为主管
        staff1 = CommunityStaff(
            community_id=community1.community_id,
            user_id=user.user_id,
            role='manager'
        )
        db.session.add(staff1)
        
        # 在社区2中设置为专员
        staff2 = CommunityStaff(
            community_id=community2.community_id,
            user_id=user.user_id,
            role='staff'
        )
        db.session.add(staff2)
        db.session.commit()
        
        # 验证用户在不同社区中的不同权限
        # 社区1：主管权限
        assert user.can_manage_community(community1.community_id) == True
        assert user.is_community_admin(community1.community_id) == True
        assert user.is_primary_admin(community1.community_id) == True
        
        # 社区2：专员权限
        assert user.can_manage_community(community2.community_id) == True
        assert user.is_community_admin(community2.community_id) == True
        assert user.is_primary_admin(community2.community_id) == False
        
        # 社区3：无权限
        assert user.can_manage_community(community3.community_id) == False
        assert user.is_community_admin(community3.community_id) == False
        assert user.is_primary_admin(community3.community_id) == False
        
        # 验证管理的社区列表包含两个社区
        managed_communities = user.get_managed_communities()
        assert len(managed_communities) == 2
        
        community_ids = [c.community_id for c in managed_communities]
        assert community1.community_id in community_ids
        assert community2.community_id in community_ids
        assert community3.community_id not in community_ids
        
        print("✅ 用户可以在不同社区中拥有不同的角色")


@pytest.fixture
def test_client():
    """创建测试客户端和数据库会话"""
    from wxcloudrun import app
    
    # 设置测试环境
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        yield app.test_client()
        
        # 清理
        db.drop_all()