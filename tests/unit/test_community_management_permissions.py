"""
社区管理权限单元测试
测试新增的社区管理业务逻辑方法
"""

import pytest
import os
import sys
import random
import string
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import User, Community, CommunityStaff
from wxcloudrun.community_service import CommunityService
from const_default import DEFUALT_COMMUNITY_NAME


def generate_random_community_name():
    """生成随机的社区名称"""
    return f"测试社区_{''.join(random.choices(string.ascii_letters, k=8))}"


class TestCommunityManagementPermissions:
    """社区管理权限测试"""
    
    def test_get_manageable_communities_super_admin(self, test_session):
        """测试超级管理员获取可管理社区列表"""
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1
        )
        test_session.add(super_admin)
        
        # 创建多个社区
        communities = []
        for i in range(10):
            community = Community(
                name=f"{generate_random_community_name()}_{i}",
                description=f"测试社区{i}",
                status=1  # 启用状态
            )
            test_session.add(community)
            communities.append(community)
        
        test_session.commit()
        
        # 测试超级管理员可以获取所有社区
        result_communities, total = CommunityService.get_manageable_communities(super_admin, page=1, per_page=7)
        
        assert total == 10  # 应该能获取所有社区
        assert len(result_communities) == 7  # 第一页7个
        assert all(comm.status == 1 for comm in result_communities)  # 都是启用状态
    
    def test_get_manageable_communities_community_manager(self, test_session):
        """测试社区主管获取可管理社区列表"""
        # 创建社区主管
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,  # 社区主管
            status=1
        )
        test_session.add(manager)
        
        # 创建多个社区
        communities = []
        for i in range(5):
            community = Community(
                name=f"{generate_random_community_name()}_{i}",
                description=f"测试社区{i}",
                status=1
            )
            test_session.add(community)
            communities.append(community)
        
        test_session.flush()
        
        # 将主管分配到前3个社区
        for i in range(3):
            staff = CommunityStaff(
                community_id=communities[i].community_id,
                user_id=manager.user_id,
                role='manager'
            )
            test_session.add(staff)
        
        test_session.commit()
        
        # 测试主管只能获取自己管理的社区
        result_communities, total = CommunityService.get_manageable_communities(manager, page=1, per_page=7)
        
        assert total == 3  # 只能获取3个自己管理的社区
        assert len(result_communities) == 3
        assert all(comm.status == 1 for comm in result_communities)
    
    def test_get_manageable_communities_community_staff(self, test_session):
        """测试社区专员获取可管理社区列表"""
        # 创建社区专员
        staff_user = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,  # 社区专员
            status=1
        )
        test_session.add(staff_user)
        
        # 创建多个社区
        communities = []
        for i in range(5):
            community = Community(
                name=f"{generate_random_community_name()}_{i}",
                description=f"测试社区{i}",
                status=1
            )
            test_session.add(community)
            communities.append(community)
        
        test_session.flush()
        
        # 将专员分配到前2个社区
        for i in range(2):
            staff = CommunityStaff(
                community_id=communities[i].community_id,
                user_id=staff_user.user_id,
                role='staff'
            )
            test_session.add(staff)
        
        test_session.commit()
        
        # 测试专员只能获取自己工作的社区
        result_communities, total = CommunityService.get_manageable_communities(staff_user, page=1, per_page=7)
        
        assert total == 2  # 只能获取2个自己工作的社区
        assert len(result_communities) == 2
        assert all(comm.status == 1 for comm in result_communities)
    
    def test_get_manageable_communities_no_permission(self, test_session):
        """测试普通用户获取可管理社区列表（无权限）"""
        # 创建普通用户
        normal_user = User(
            wechat_openid="normal_openid",
            nickname="普通用户",
            role=1,  # 普通用户
            status=1
        )
        test_session.add(normal_user)
        
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.commit()
        
        # 测试普通用户无法获取任何社区
        result_communities, total = CommunityService.get_manageable_communities(normal_user, page=1, per_page=7)
        
        assert total == 0
        assert len(result_communities) == 0
    
    def test_search_communities_with_permission_super_admin(self, test_session):
        """测试超级管理员搜索社区"""
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,
            status=1
        )
        test_session.add(super_admin)
        
        # 创建包含特定关键词的社区
        community1 = Community(
            name="北京朝阳社区",
            description="朝阳区社区",
            status=1
        )
        community2 = Community(
            name="上海浦东社区",
            description="浦东新区社区",
            status=1
        )
        community3 = Community(
            name="广州天河社区",
            description="天河区社区",
            status=2  # 停用状态
        )
        
        test_session.add_all([community1, community2, community3])
        test_session.commit()
        
        # 搜索"社区"关键词
        results = CommunityService.search_communities_with_permission(super_admin, "社区")
        
        # 超级管理员应该能看到所有启用状态的社区
        assert len(results) == 2  # 只有2个启用状态的社区
        assert any(comm.name == "北京朝阳社区" for comm in results)
        assert any(comm.name == "上海浦东社区" for comm in results)
    
    def test_search_communities_with_permission_community_manager(self, test_session):
        """测试社区主管搜索社区"""
        # 创建社区主管
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,
            status=1
        )
        test_session.add(manager)
        
        # 创建多个社区
        community1 = Community(
            name="北京朝阳社区",
            description="朝阳区社区",
            status=1
        )
        community2 = Community(
            name="上海浦东社区",
            description="浦东新区社区",
            status=1
        )
        
        test_session.add_all([community1, community2])
        test_session.flush()
        
        # 将主管分配到第一个社区
        staff = CommunityStaff(
            community_id=community1.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        test_session.add(staff)
        test_session.commit()
        
        # 搜索"社区"关键词
        results = CommunityService.search_communities_with_permission(manager, "社区")
        
        # 主管只能看到自己管理的社区
        assert len(results) == 1
        assert results[0].name == "北京朝阳社区"
    
    def test_can_access_community_permissions(self, test_session):
        """测试社区访问权限检查"""
        # 创建不同角色的用户
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,
            status=1
        )
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,
            status=1
        )
        staff = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,
            status=1
        )
        normal_user = User(
            wechat_openid="normal_openid",
            nickname="普通用户",
            role=1,
            status=1
        )
        
        test_session.add_all([super_admin, manager, staff, normal_user])
        
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 将主管和专员分配到社区
        manager_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        staff_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role='staff'
        )
        
        test_session.add_all([manager_staff, staff_staff])
        test_session.commit()
        
        # 测试权限
        assert CommunityService.can_access_community(super_admin, community.community_id) == True
        assert CommunityService.can_access_community(manager, community.community_id) == True
        assert CommunityService.can_access_community(staff, community.community_id) == True
        assert CommunityService.can_access_community(normal_user, community.community_id) == False
    
    def test_can_manage_users_permissions(self, test_session):
        """测试用户管理权限检查"""
        # 创建不同角色的用户
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,
            status=1
        )
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,
            status=1
        )
        staff = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,
            status=1
        )
        normal_user = User(
            wechat_openid="normal_openid",
            nickname="普通用户",
            role=1,
            status=1
        )
        
        test_session.add_all([super_admin, manager, staff, normal_user])
        
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 将主管和专员分配到社区
        manager_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        staff_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role='staff'
        )
        
        test_session.add_all([manager_staff, staff_staff])
        test_session.commit()
        
        # 测试用户管理权限
        assert CommunityService.can_manage_users(super_admin, community.community_id) == True
        assert CommunityService.can_manage_users(manager, community.community_id) == True
        assert CommunityService.can_manage_users(staff, community.community_id) == True
        assert CommunityService.can_manage_users(normal_user, community.community_id) == False
    
    def test_can_manage_staff_permissions(self, test_session):
        """测试工作人员管理权限检查"""
        # 创建不同角色的用户
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,
            status=1
        )
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,
            status=1
        )
        staff = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,
            status=1
        )
        normal_user = User(
            wechat_openid="normal_openid",
            nickname="普通用户",
            role=1,
            status=1
        )
        
        test_session.add_all([super_admin, manager, staff, normal_user])
        
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 将主管和专员分配到社区
        manager_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        staff_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role='staff'
        )
        
        test_session.add_all([manager_staff, staff_staff])
        test_session.commit()
        
        # 测试工作人员管理权限（只有主管和超级管理员可以）
        assert CommunityService.can_manage_staff(super_admin, community.community_id) == True
        assert CommunityService.can_manage_staff(manager, community.community_id) == True
        assert CommunityService.can_manage_staff(staff, community.community_id) == False  # 专员不能管理工作人员
        assert CommunityService.can_manage_staff(normal_user, community.community_id) == False
    
    def test_is_community_manager_permissions(self, test_session):
        """测试社区主管身份检查"""
        # 创建不同角色的用户
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,
            status=1
        )
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,
            status=1
        )
        staff = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,
            status=1
        )
        
        test_session.add_all([super_admin, manager, staff])
        
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 将主管和专员分配到社区
        manager_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        staff_staff = CommunityStaff(
            community_id=community.community_id,
            user_id=staff.user_id,
            role='staff'
        )
        
        test_session.add_all([manager_staff, staff_staff])
        test_session.commit()
        
        # 测试主管身份检查
        assert CommunityService.is_community_manager(super_admin, community.community_id) == True
        assert CommunityService.is_community_manager(manager, community.community_id) == True
        assert CommunityService.is_community_manager(staff, community.community_id) == False  # 专员不是主管
    
    def test_validate_ankafamily_rule_success(self, test_session):
        """测试安卡大家庭规则验证（成功情况）"""
        # 创建安卡大家庭社区
        ankafamily = Community(
            name=DEFUALT_COMMUNITY_NAME,
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(ankafamily)
        
        # 创建普通社区
        target_community = Community(
            name=generate_random_community_name(),
            description="目标社区",
            status=1
        )
        test_session.add(target_community)
        
        # 先flush获取社区ID
        test_session.flush()
        
        # 创建用户（在安卡大家庭）
        user = User(
            wechat_openid="user_openid",
            nickname="测试用户",
            role=1,
            status=1,
            community_id=ankafamily.community_id
        )
        test_session.add(user)
        
        test_session.commit()
        
        # 验证规则应该通过
        result = CommunityService.validate_ankafamily_rule(
            user.user_id,
            target_community.community_id,
            operator=1
        )
        
        assert result == True
    
    def test_validate_ankafamily_rule_user_not_in_ankafamily(self, test_session):
        """测试安卡大家庭规则验证（用户不在安卡大家庭）"""
        # 创建安卡大家庭社区
        ankafamily = Community(
            name=DEFUALT_COMMUNITY_NAME,
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(ankafamily)
        
        # 创建普通社区
        other_community = Community(
            name="其他社区",
            description="其他社区",
            status=1
        )
        test_session.add(other_community)
        
        target_community = Community(
            name=generate_random_community_name(),
            description="目标社区",
            status=1
        )
        test_session.add(target_community)
        
        # 创建用户（在其他社区，不在安卡大家庭）
        user = User(
            wechat_openid="user_openid",
            nickname="测试用户",
            role=1,
            status=1,
            community_id=other_community.community_id
        )
        test_session.add(user)
        
        test_session.commit()
        
        # 验证规则应该失败
        with pytest.raises(ValueError) as exc_info:
            CommunityService.validate_ankafamily_rule(
                user.user_id,
                target_community.community_id,
                operator=1
            )
        
        assert "用户不在安卡大家庭" in str(exc_info.value)
    
    def test_validate_ankafamily_rule_target_is_ankafamily(self, test_session):
        """测试安卡大家庭规则验证（目标社区是安卡大家庭）"""
        # 创建安卡大家庭社区
        ankafamily = Community(
            name=DEFUALT_COMMUNITY_NAME,
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(ankafamily)
        
        # 先flush获取社区ID
        test_session.flush()
        
        # 创建用户（在安卡大家庭）
        user = User(
            wechat_openid="user_openid",
            nickname="测试用户",
            role=1,
            status=1,
            community_id=ankafamily.community_id
        )
        test_session.add(user)
        
        test_session.commit()
        
        # 验证规则应该失败（不能添加到安卡大家庭）
        with pytest.raises(ValueError) as exc_info:
            CommunityService.validate_ankafamily_rule(
                user.user_id,
                ankafamily.community_id,
                operator=1
            )
        
        assert "不能将用户添加到安卡大家庭" in str(exc_info.value)
    
    def test_validate_ankafamily_rule_ankafamily_not_exist(self, test_session):
        """测试安卡大家庭规则验证（安卡大家庭不存在）"""
        # 创建普通社区（不创建安卡大家庭）
        target_community = Community(
            name=generate_random_community_name(),
            description="目标社区",
            status=1
        )
        test_session.add(target_community)
        
        # 创建用户
        user = User(
            wechat_openid="user_openid",
            nickname="测试用户",
            role=1,
            status=1,
            community_id=1  # 任意社区ID
        )
        test_session.add(user)
        
        test_session.commit()
        
        # 验证规则应该失败
        with pytest.raises(ValueError) as exc_info:
            CommunityService.validate_ankafamily_rule(
                user.user_id,
                target_community.community_id,
                operator=1
            )
        
        assert "安卡大家庭社区不存在" in str(exc_info.value)
    
    def test_validate_ankafamily_rule_user_not_exist(self, test_session):
        """测试安卡大家庭规则验证（用户不存在）"""
        # 创建安卡大家庭社区
        ankafamily = Community(
            name=DEFUALT_COMMUNITY_NAME,
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(ankafamily)
        
        # 创建普通社区
        target_community = Community(
            name=generate_random_community_name(),
            description="目标社区",
            status=1
        )
        test_session.add(target_community)
        
        test_session.commit()
        
        # 验证规则应该失败（用户不存在）
        with pytest.raises(ValueError) as exc_info:
            CommunityService.validate_ankafamily_rule(
                99999,  # 不存在的用户ID
                target_community.community_id,
                operator=1
            )
        
        assert "用户不存在" in str(exc_info.value)