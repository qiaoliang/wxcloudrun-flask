"""
多社区角色功能的单元测试
测试用户可以在多个社区担任不同角色的核心业务逻辑
使用真实数据库但不使用HTTP请求
"""

import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import User, Community, CommunityApplication, CommunityStaff, CommunityMember


class TestMultiCommunityRoleUnit:
    """单元测试：多社区角色分配的核心业务逻辑"""

    def test_user_can_hold_multiple_roles_in_different_communities(self, test_session):
        """
        测试用户可以在不同社区担任不同角色
        业务规则：同一个用户可以在A社区担任专员，在B社区担任主管
        """
        # 创建测试用户
        user = User(
            wechat_openid="test_multi_role_user",
            nickname="多角色测试用户",
            role=1  # 普通用户
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建两个社区
        community_a = Community(
            name="社区A",
            location="测试地址A",
            creator_user_id=user.user_id,
            status=1
        )
        community_b = Community(
            name="社区B", 
            location="测试地址B",
            creator_user_id=user.user_id,
            status=1
        )
        test_session.add_all([community_a, community_b])
        test_session.flush()
        
        # 在社区A中添加用户为专员
        staff_a = CommunityStaff(
            community_id=community_a.community_id,
            user_id=user.user_id,
            role="staff",
            scope="负责区域A"
        )
        test_session.add(staff_a)
        
        # 在社区B中添加同一用户为主管
        staff_b = CommunityStaff(
            community_id=community_b.community_id,
            user_id=user.user_id,
            role="manager"
        )
        test_session.add(staff_b)
        test_session.commit()
        
        # 验证用户在两个社区都有角色记录
        user_roles = test_session.query(CommunityStaff).filter_by(user_id=user.user_id).all()
        assert len(user_roles) == 2, "用户应该有2个角色记录"
        
        # 验证角色分配正确
        roles_by_community = {role.community_id: role.role for role in user_roles}
        assert roles_by_community[community_a.community_id] == "staff", "在社区A应该是专员"
        assert roles_by_community[community_b.community_id] == "manager", "在社区B应该是主管"

    def test_get_user_roles_in_communities(self, test_session):
        """
        测试获取用户在所有社区中的角色
        """
        # 创建测试用户
        user = User(
            wechat_openid="test_roles_user",
            nickname="角色查询用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建三个社区
        communities = []
        for i in range(3):
            community = Community(
                name=f"社区{i+1}",
                location=f"地址{i+1}",
                creator_user_id=1,
                status=1
            )
            test_session.add(community)
            communities.append(community)
        test_session.flush()
        
        # 设置用户在不同社区中的角色
        # 社区1：主管
        staff1 = CommunityStaff(
            community_id=communities[0].community_id,
            user_id=user.user_id,
            role="manager"
        )
        test_session.add(staff1)
        
        # 社区2：专员
        staff2 = CommunityStaff(
            community_id=communities[1].community_id,
            user_id=user.user_id,
            role="staff"
        )
        test_session.add(staff2)
        
        # 社区3：普通成员（没有Staff记录）
        member3 = CommunityMember(
            community_id=communities[2].community_id,
            user_id=user.user_id
        )
        test_session.add(member3)
        test_session.commit()
        
        # 查询用户的所有角色
        user_roles = test_session.query(CommunityStaff).filter_by(user_id=user.user_id).all()
        
        # 验证结果
        assert len(user_roles) == 2  # 只有2个Staff记录
        
        role_info = {}
        for role in user_roles:
            community = test_session.query(Community).filter_by(community_id=role.community_id).first()
            role_info[community.name] = role.role
        
        assert role_info.get("社区1") == "manager"
        assert role_info.get("社区2") == "staff"
        assert "社区3" not in role_info  # 没有Staff记录

    def test_user_role_changes(self, test_session):
        """
        测试用户角色变更
        """
        # 创建测试用户和社区
        user = User(
            wechat_openid="test_role_change_user",
            nickname="角色变更用户",
            role=1
        )
        community = Community(
            name="角色变更社区",
            location="测试地址",
            creator_user_id=1,
            status=1
        )
        test_session.add_all([user, community])
        test_session.flush()
        
        # 初始设置：用户为专员
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role="staff"
        )
        test_session.add(staff)
        test_session.commit()
        
        # 验证初始角色
        initial_role = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert initial_role.role == "staff"
        
        # 角色变更：从专员变为主管
        initial_role.role = "manager"
        test_session.commit()
        
        # 验证角色已变更
        updated_role = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert updated_role.role == "manager"

    def test_user_leaves_community(self, test_session):
        """
        测试用户离开社区
        """
        # 创建测试用户和社区
        user = User(
            wechat_openid="test_leave_user",
            nickname="离开社区用户",
            role=1
        )
        community = Community(
            name="离开测试社区",
            location="测试地址",
            creator_user_id=1,
            status=1
        )
        test_session.add_all([user, community])
        test_session.flush()
        
        # 用户加入社区并担任角色
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role="staff"
        )
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add_all([staff, member])
        test_session.commit()
        
        # 验证用户在社区中
        staff_record = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert staff_record is not None
        
        member_record = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert member_record is not None
        
        # 用户离开社区（删除记录）
        test_session.delete(staff)
        test_session.delete(member)
        test_session.commit()
        
        # 验证用户已离开社区
        staff_after = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert staff_after is None
        
        member_after = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert member_after is None

    def test_community_role_permissions(self, test_session):
        """
        测试社区角色权限
        """
        # 创建测试用户
        manager = User(
            wechat_openid="test_manager",
            nickname="主管",
            role=1
        )
        staff = User(
            wechat_openid="test_staff",
            nickname="专员",
            role=1
        )
        member = User(
            wechat_openid="test_member",
            nickname="成员",
            role=1
        )
        test_session.add_all([manager, staff, member])
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="权限测试社区",
            location="测试地址",
            creator_user_id=1,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 分配角色
        manager_role = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role="manager"
        )
        staff_role = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role="staff"
        )
        member_role = CommunityMember(
            community_id=community.community_id,
            user_id=member.user_id
        )
        test_session.add_all([manager_role, staff_role, member_role])
        test_session.commit()
        
        # 查询有管理权限的用户（主管和专员）
        managed_users = test_session.query(User).join(CommunityStaff).filter(
            CommunityStaff.community_id == community.community_id
        ).all()
        
        # 验证结果
        assert len(managed_users) == 2
        managed_openids = [u.wechat_openid for u in managed_users]
        assert "test_manager" in managed_openids
        assert "test_staff" in managed_openids
        assert "test_member" not in managed_openids

    def test_user_application_to_community(self, test_session):
        """
        测试用户申请加入社区
        """
        # 创建测试用户和社区
        user = User(
            wechat_openid="test_apply_user",
            nickname="申请用户",
            role=1
        )
        community = Community(
            name="申请测试社区",
            location="测试地址",
            creator_user_id=1,
            status=1
        )
        test_session.add_all([user, community])
        test_session.flush()
        
        # 用户申请加入社区
        application = CommunityApplication(
            user_id=user.user_id,
            target_community_id=community.community_id,
            status=1,  # 待审核
            reason="我想加入这个社区"
        )
        test_session.add(application)
        test_session.commit()
        
        # 验证申请已创建
        found_application = test_session.query(CommunityApplication).filter_by(
            user_id=user.user_id,
            target_community_id=community.community_id
        ).first()
        assert found_application is not None
        assert found_application.status == 1
        assert found_application.reason == "我想加入这个社区"