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

from database.models import User, Community, CommunityStaff, CommunityMember


class TestUserCommunityRolePermissions:
    """测试用户基于社区角色的权限"""

    def test_super_admin_role(self, test_session):
        """
        测试超级管理员角色
        """
        # 创建超级管理员用户
        super_admin = User(
            wechat_openid="super_admin",
            nickname="超级管理员",
            role=4  # 超级管理员角色
        )
        test_session.add(super_admin)
        test_session.commit()
        
        # 验证超级管理员角色
        assert super_admin.role == 4
        assert super_admin.nickname == "超级管理员"

    def test_community_manager_permissions(self, test_session):
        """
        测试社区主管权限
        """
        # 创建普通用户
        manager = User(
            wechat_openid="manager_user",
            nickname="社区主管",
            role=1  # 普通用户
        )
        test_session.add(manager)
        test_session.flush()
        
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
        test_session.add_all([managed_community, other_community])
        test_session.flush()
        
        # 在第一个社区设置用户为主管
        manager_role = CommunityStaff(
            community_id=managed_community.community_id,
            user_id=manager.user_id,
            role="manager"
        )
        test_session.add(manager_role)
        test_session.commit()
        
        # 验证用户在第一个社区是主管
        staff_record = test_session.query(CommunityStaff).filter_by(
            community_id=managed_community.community_id,
            user_id=manager.user_id
        ).first()
        assert staff_record is not None
        assert staff_record.role == "manager"
        
        # 验证用户在第二个社区没有角色
        other_staff = test_session.query(CommunityStaff).filter_by(
            community_id=other_community.community_id,
            user_id=manager.user_id
        ).first()
        assert other_staff is None

    def test_community_staff_permissions(self, test_session):
        """
        测试社区专员权限
        """
        # 创建专员用户
        staff = User(
            wechat_openid="staff_user",
            nickname="社区专员",
            role=1
        )
        test_session.add(staff)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="专员管理社区",
            description="专员工作的社区",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 设置用户为专员
        staff_role = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role="staff"
        )
        test_session.add(staff_role)
        test_session.commit()
        
        # 验证用户角色
        staff_record = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=staff.user_id
        ).first()
        assert staff_record is not None
        assert staff_record.role == "staff"

    def test_regular_member_permissions(self, test_session):
        """
        测试普通成员权限
        """
        # 创建普通用户
        member = User(
            wechat_openid="member_user",
            nickname="社区成员",
            role=1
        )
        test_session.add(member)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="成员社区",
            description="普通成员的社区",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 用户只作为成员加入社区（没有Staff记录）
        member_role = CommunityMember(
            community_id=community.community_id,
            user_id=member.user_id
        )
        test_session.add(member_role)
        test_session.commit()
        
        # 验证用户是成员
        member_record = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=member.user_id
        ).first()
        assert member_record is not None
        
        # 验证用户没有管理权限
        staff_record = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=member.user_id
        ).first()
        assert staff_record is None

    def test_user_multiple_roles_in_different_communities(self, test_session):
        """
        测试用户在不同社区中有不同角色
        """
        # 创建用户
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
        
        # 设置不同角色
        # 社区1：主管
        manager_role = CommunityStaff(
            community_id=community1.community_id,
            user_id=user.user_id,
            role="manager"
        )
        test_session.add(manager_role)
        
        # 社区2：专员
        staff_role = CommunityStaff(
            community_id=community2.community_id,
            user_id=user.user_id,
            role="staff"
        )
        test_session.add(staff_role)
        
        # 社区3：普通成员
        member_role = CommunityMember(
            community_id=community3.community_id,
            user_id=user.user_id
        )
        test_session.add(member_role)
        test_session.commit()
        
        # 验证角色分配
        roles = {}
        
        # 查询用户在所有社区的角色
        staff_records = test_session.query(CommunityStaff).filter_by(user_id=user.user_id).all()
        for record in staff_records:
            roles[record.community_id] = record.role
        
        member_records = test_session.query(CommunityMember).filter_by(user_id=user.user_id).all()
        for record in member_records:
            if record.community_id not in roles:
                roles[record.community_id] = "member"
        
        assert roles.get(community1.community_id) == "manager"
        assert roles.get(community2.community_id) == "staff"
        assert roles.get(community3.community_id) == "member"

    def test_permission_inheritance(self, test_session):
        """
        测试权限继承关系
        """
        # 在实际应用中，主管可能拥有专员的权限
        # 这里测试权限查询的逻辑
        
        # 创建用户和社区
        user = User(
            wechat_openid="permission_user",
            nickname="权限测试用户",
            role=1
        )
        community = Community(
            name="权限测试社区",
            description="测试权限继承",
            creator_user_id=1
        )
        test_session.add_all([user, community])
        test_session.flush()
        
        # 设置用户为主管
        manager_role = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role="manager"
        )
        test_session.add(manager_role)
        test_session.commit()
        
        # 查询用户在社区中的所有权限
        # 主管应该能够执行所有管理操作
        
        # 验证用户有管理权限（通过Staff记录）
        has_permission = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert has_permission is not None
        assert has_permission.role in ["manager", "staff"]  # 主管和专员都有管理权限

    def test_no_role_user(self, test_session):
        """
        测试没有社区角色的用户
        """
        # 创建用户但不加入任何社区
        user = User(
            wechat_openid="no_role_user",
            nickname="无角色用户",
            role=1
        )
        test_session.add(user)
        test_session.commit()
        
        # 验证用户没有在任何社区中
        member_count = test_session.query(CommunityMember).filter_by(
            user_id=user.user_id
        ).count()
        assert member_count == 0
        
        staff_count = test_session.query(CommunityStaff).filter_by(
            user_id=user.user_id
        ).count()
        assert staff_count == 0
        
        # 验证用户没有管理任何社区
        managed_communities = test_session.query(Community).join(CommunityStaff).filter(
            CommunityStaff.user_id == user.user_id
        ).count()
        assert managed_communities == 0