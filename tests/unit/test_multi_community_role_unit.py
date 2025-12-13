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

from wxcloudrun.model import User, Community, CommunityApplication
from wxcloudrun.model_community_extensions import CommunityStaff
from wxcloudrun import app, db


class TestMultiCommunityRoleUnit:
    """单元测试：多社区角色分配的核心业务逻辑"""

    def test_user_can_hold_multiple_roles_in_different_communities(self, test_db):
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
        test_db.session.add(user)
        test_db.session.commit()

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
        test_db.session.add_all([community_a, community_b])
        test_db.session.commit()

        # 在社区A中添加用户为专员
        staff_a = CommunityStaff(
            community_id=community_a.community_id,
            user_id=user.user_id,
            role="staff",
            scope="负责区域A"
        )
        test_db.session.add(staff_a)

        # 在社区B中添加同一用户为主管
        staff_b = CommunityStaff(
            community_id=community_b.community_id,
            user_id=user.user_id,
            role="manager"
        )
        test_db.session.add(staff_b)
        test_db.session.commit()

        # 验证用户在两个社区都有角色记录
        user_roles = CommunityStaff.query.filter_by(user_id=user.user_id).all()
        assert len(user_roles) == 2, "用户应该有2个角色记录"

        # 验证角色分配正确
        roles_by_community = {role.community_id: role.role for role in user_roles}
        assert roles_by_community[community_a.community_id] == "staff", "在社区A应该是专员"
        assert roles_by_community[community_b.community_id] == "manager", "在社区B应该是主管"

    def test_get_managed_communities_returns_correct_roles(self, test_db):
        """
        测试获取用户管理的社区返回正确的角色信息
        业务规则：应该准确返回用户在每个社区的角色
        """
        # 清理所有相关数据以确保测试隔离
        CommunityStaff.query.filter(CommunityStaff.user_id.isnot(None)).delete()
        Community.query.filter(Community.creator_user_id.isnot(None)).delete()
        User.query.filter(User.wechat_openid.like("test_managed_user%")).delete()
        test_db.session.commit()
        
        # 创建测试用户
        user = User(
            wechat_openid="test_managed_user_isolated",
            nickname="管理测试用户",
            role=1
        )
        test_db.session.add(user)
        test_db.session.commit()

        # 创建三个社区
        communities = []
        for i in range(3):
            community = Community(
                name=f"社区{i+1}_isolated",
                location=f"测试地址{i+1}",
                creator_user_id=user.user_id,
                status=1
            )
            communities.append(community)
        test_db.session.add_all(communities)
        test_db.session.commit()

        # 设置角色：社区1为staff，社区2为manager，社区3为staff
        role_assignments = [
            (communities[0].community_id, "staff", "区域1"),
            (communities[1].community_id, "manager", None),
            (communities[2].community_id, "staff", "区域2")
        ]

        for community_id, role, scope in role_assignments:
            staff = CommunityStaff(
                community_id=community_id,
                user_id=user.user_id,
                role=role,
                scope=scope
            )
            test_db.session.add(staff)
        test_db.session.commit()

        # 调用get_managed_communities方法
        managed_communities = user.get_managed_communities()
        
        assert len(managed_communities) == 3, "应该管理3个社区"

        # 验证每个社区的角色信息
        community_roles = {c.community_id: c for c in managed_communities}
        
        # 验证社区1的角色
        community_1_info = community_roles[communities[0].community_id]
        assert hasattr(community_1_info, 'name'), "社区应该有name属性"
        assert community_1_info.name == "社区1_isolated"
        
        # 验证CommunityStaff关联
        staff_role_1 = CommunityStaff.query.filter_by(
            community_id=communities[0].community_id,
            user_id=user.user_id
        ).first()
        assert staff_role_1.role == "staff"
        assert staff_role_1.scope == "区域1"

    def test_user_removal_from_single_community(self, test_db):
        """
        测试从单个社区移除用户不影响其他社区的角色
        业务规则：移除操作应该是社区级别的
        """
        # 清理所有相关数据以确保测试隔离
        CommunityStaff.query.filter(CommunityStaff.user_id.isnot(None)).delete()
        Community.query.filter(Community.creator_user_id.isnot(None)).delete()
        User.query.filter(User.wechat_openid.like("test_removal_user%")).delete()
        test_db.session.commit()
        
        # 创建测试用户
        user = User(
            wechat_openid="test_removal_user_isolated",
            nickname="移除测试用户",
            role=1
        )
        test_db.session.add(user)
        test_db.session.commit()

        # 创建三个社区
        communities = []
        for i in range(3):
            community = Community(
                name=f"移除测试社区{i+1}_isolated",
                location=f"移除测试地址{i+1}",
                creator_user_id=user.user_id,
                status=1
            )
            communities.append(community)
        test_db.session.add_all(communities)
        test_db.session.commit()

        # 在所有三个社区添加用户
        for i, community in enumerate(communities):
            role = "manager" if i == 1 else "staff"  # 社区2为主管，其他为专员
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user.user_id,
                role=role
            )
            test_db.session.add(staff)
        test_db.session.commit()

        # 验证初始状态：用户在所有三个社区都有角色
        initial_roles = CommunityStaff.query.filter_by(user_id=user.user_id).all()
        assert len(initial_roles) == 3, "初始应该有3个角色记录"

        # 从社区1移除用户
        staff_to_remove = CommunityStaff.query.filter_by(
            community_id=communities[0].community_id,
            user_id=user.user_id
        ).first()
        test_db.session.delete(staff_to_remove)
        test_db.session.commit()

        # 验证用户已从社区1移除，但在社区2和3仍存在
        remaining_roles = CommunityStaff.query.filter_by(user_id=user.user_id).all()
        assert len(remaining_roles) == 2, "移除后应该还有2个角色记录"

        remaining_community_ids = {role.community_id for role in remaining_roles}
        assert communities[0].community_id not in remaining_community_ids, "社区1应该被移除"
        assert communities[1].community_id in remaining_community_ids, "社区2应该保留"
        assert communities[2].community_id in remaining_community_ids, "社区3应该保留"

        # 验证保留的角色正确
        community_2_role = next(r for r in remaining_roles if r.community_id == communities[1].community_id)
        assert community_2_role.role == "manager", "社区2应该保持manager角色"

    def test_super_admin_manages_all_communities(self, test_db):
        """
        测试超级管理员管理所有社区
        业务规则：超级管理员可以管理所有活跃社区
        """
        # 清理测试特定数据，但保留默认数据
        User.query.filter(User.wechat_openid.like("test_super_admin_isolated")).delete()
        Community.query.filter(Community.name.like("超级管理员测试社区%")).delete()
        test_db.session.commit()
        
        # 使用现有的超级管理员（如果存在）或创建新的
        super_admin = User.query.filter_by(role=4).first()
        if not super_admin:
            super_admin = User(
                wechat_openid="test_super_admin_isolated",
                nickname="超级管理员",
                role=4  # 超级管理员
            )
            test_db.session.add(super_admin)
            test_db.session.commit()

        # 创建多个测试社区（不包括默认社区）
        communities = []
        for i in range(5):
            community = Community(
                name=f"超级管理员测试社区{i+1}_isolated",
                location=f"超级管理员测试地址{i+1}",
                creator_user_id=super_admin.user_id,
                status=1 if i != 3 else 2  # 社区4为禁用状态
            )
            communities.append(community)
        test_db.session.add_all(communities)
        test_db.session.commit()

        # 调用get_managed_communities
        managed_communities = super_admin.get_managed_communities()

        # 超级管理员应该管理所有活跃社区（包括默认社区和测试社区）
        # 默认有1个"安卡大家庭"社区 + 4个测试社区 = 5个活跃社区
        expected_count = 5  # 1个默认社区 + 4个活跃测试社区
        assert len(managed_communities) >= expected_count, f"超级管理员应该至少管理{expected_count}个活跃社区"

        # 验证所有管理的社区都是活跃状态
        for community in managed_communities:
            assert community.status == 1, f"社区{community.name}应该是活跃状态，实际是{community.status}"

    def test_community_staff_role_constraints(self, test_db):
        """
        测试社区工作人员角色的约束
        业务规则：角色只能是manager或staff
        """
        # 创建测试用户和社区
        user = User(
            wechat_openid="test_constraint_user",
            nickname="约束测试用户",
            role=1
        )
        community = Community(
            name="约束测试社区",
            location="约束测试地址",
            creator_user_id=user.user_id,
            status=1
        )
        test_db.session.add_all([user, community])
        test_db.session.commit()

        # 测试有效的角色
        valid_roles = ["manager", "staff"]
        for role in valid_roles:
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user.user_id,
                role=role
            )
            test_db.session.add(staff)
            test_db.session.commit()
            
            # 验证可以成功添加
            assert staff.id is not None, f"角色{role}应该可以成功添加"
            
            # 清理以便下次测试
            test_db.session.delete(staff)
            test_db.session.commit()

    def test_user_role_in_community_property(self, test_db):
        """
        测试用户在社区中的角色属性
        业务规则：应该能够方便地查询用户在特定社区的角色
        """
        # 创建测试用户和社区
        user = User(
            wechat_openid="test_role_property_user",
            nickname="角色属性测试用户",
            role=1
        )
        community = Community(
            name="角色属性测试社区",
            location="角色属性测试地址",
            creator_user_id=user.user_id,
            status=1
        )
        test_db.session.add_all([user, community])
        test_db.session.commit()

        # 添加用户为社区主管
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role="manager",
            scope="全面管理"
        )
        test_db.session.add(staff)
        test_db.session.commit()

        # 验证可以通过CommunityStaff查询用户的角色
        user_role = CommunityStaff.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()

        assert user_role is not None, "应该找到用户的角色记录"
        assert user_role.role == "manager", "用户角色应该是manager"
        assert user_role.scope == "全面管理", "负责范围应该正确设置"
        assert user_role.added_at is not None, "添加时间应该被设置"

    def test_multiple_users_in_same_community_with_different_roles(self, test_db):
        """
        测试同一社区中多个用户担任不同角色
        业务规则：一个社区可以有多个主管和专员
        """
        # 创建多个用户
        users = []
        for i in range(4):
            user = User(
                wechat_openid=f"test_multi_user_{i+1}",
                nickname=f"多用户测试{i+1}",
                role=1
            )
            users.append(user)
        test_db.session.add_all(users)
        test_db.session.commit()

        # 创建社区
        community = Community(
            name="多用户测试社区",
            location="多用户测试地址",
            creator_user_id=users[0].user_id,
            status=1
        )
        test_db.session.add(community)
        test_db.session.commit()

        # 分配角色：2个主管，2个专员
        role_assignments = [
            (users[0].user_id, "manager"),
            (users[1].user_id, "manager"),
            (users[2].user_id, "staff"),
            (users[3].user_id, "staff")
        ]

        for user_id, role in role_assignments:
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user_id,
                role=role
            )
            test_db.session.add(staff)
        test_db.session.commit()

        # 验证角色分配
        all_staff = CommunityStaff.query.filter_by(community_id=community.community_id).all()
        assert len(all_staff) == 4, "应该有4个工作人员"

        managers = [s for s in all_staff if s.role == "manager"]
        staff_members = [s for s in all_staff if s.role == "staff"]

        assert len(managers) == 2, "应该有2个主管"
        assert len(staff_members) == 2, "应该有2个专员"

        # 验证具体用户的角色
        manager_ids = {m.user_id for m in managers}
        staff_ids = {s.user_id for s in staff_members}

        assert users[0].user_id in manager_ids, "用户1应该是主管"
        assert users[1].user_id in manager_ids, "用户2应该是主管"
        assert users[2].user_id in staff_ids, "用户3应该是专员"
        assert users[3].user_id in staff_ids, "用户4应该是专员"