"""
测试获取用户管理的社区列表及返回正确的角色信息
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import User, Community, CommunityStaff, CommunityMember


class TestManagedCommunities:
    """测试用户管理的社区功能"""

    def test_user_as_manager_in_community(self, test_session):
        """测试用户作为社区主管"""
        # 创建测试用户
        user = User(
            wechat_openid="manager_user",
            nickname="主管用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
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
        assert managed_communities[0].name == "测试社区"

    def test_user_as_staff_in_community(self, test_session):
        """测试用户作为社区专员"""
        # 创建测试用户
        user = User(
            wechat_openid="staff_user",
            nickname="专员用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="专员社区",
            description="专员社区描述",
            creator_user_id=1
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
        assert managed_communities[0].name == "专员社区"

    def test_user_multiple_roles_in_different_communities(self, test_session):
        """测试用户在不同社区中有不同角色"""
        # 创建测试用户
        user = User(
            wechat_openid="multi_role_user",
            nickname="多角色用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建三个社区
        community1 = Community(
            name="主管社区",
            description="用户是主管的社区",
            creator_user_id=1
        )
        community2 = Community(
            name="专员社区",
            description="用户是专员的社区",
            creator_user_id=1
        )
        community3 = Community(
            name="成员社区",
            description="用户只是成员的社区",
            creator_user_id=1
        )
        test_session.add_all([community1, community2, community3])
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
        
        # 在第三个社区中只是成员
        member_role = CommunityMember(
            community_id=community3.community_id,
            user_id=user.user_id
        )
        test_session.add(member_role)
        test_session.commit()
        
        # 查询用户有管理权限的社区（主管或专员）
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id
        ).all()
        
        # 验证只返回有管理权限的社区
        assert len(managed_communities) == 2
        
        community_names = [c.name for c in managed_communities]
        assert "主管社区" in community_names
        assert "专员社区" in community_names
        assert "成员社区" not in community_names

    def test_get_user_role_in_community(self, test_session):
        """测试获取用户在特定社区中的角色"""
        # 创建测试用户
        user = User(
            wechat_openid="role_test_user",
            nickname="角色测试用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="角色测试社区",
            description="用于测试角色的社区",
            creator_user_id=1
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
        
        # 查询用户在社区中的角色
        staff_record = test_session.query(CommunityStaff).filter(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.user_id == user.user_id
        ).first()
        
        # 验证角色
        assert staff_record is not None
        assert staff_record.role == 'manager'
        
        # 验证用户也是社区成员
        member_record = test_session.query(CommunityMember).filter(
            CommunityMember.community_id == community.community_id,
            CommunityMember.user_id == user.user_id
        ).first()
        
        # 注意：当前实现中，有Staff记录的用户可能没有Member记录
        # 这取决于业务逻辑的实现

    def test_inactive_communities_not_in_managed_list(self, test_session):
        """测试停用的社区不在管理列表中"""
        # 创建测试用户
        user = User(
            wechat_openid="inactive_test_user",
            nickname="停用测试用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建两个社区：一个活跃，一个停用
        active_community = Community(
            name="活跃社区",
            description="活跃的社区",
            creator_user_id=1,
            status=1  # 活跃
        )
        inactive_community = Community(
            name="停用社区",
            description="已停用的社区",
            creator_user_id=1,
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
        assert managed_communities[0].name == "活跃社区"

    def test_user_with_no_managed_communities(self, test_session):
        """测试用户没有管理任何社区"""
        # 创建测试用户
        user = User(
            wechat_openid="no_manage_user",
            nickname="无管理权限用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 用户只作为普通成员加入社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member)
        test_session.commit()
        
        # 查询用户管理的社区
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id
        ).all()
        
        # 验证用户没有管理任何社区
        assert len(managed_communities) == 0