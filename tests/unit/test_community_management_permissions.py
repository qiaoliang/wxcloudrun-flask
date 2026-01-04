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

from database.flask_models import User, Community, CommunityStaff
from wxcloudrun.community_service import CommunityService
from const_default import DEFAULT_COMMUNITY_NAME
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname


def generate_random_community_name():
    """生成随机的社区名称"""
    return f"测试社区_{''.join(random.choices(string.ascii_letters, k=8))}"


class TestCommunityManagementPermissions:
    """社区管理权限测试"""

    def test_get_manageable_communities_super_admin(self, test_session):
        """测试超级管理员获取可管理社区列表"""
        test_context = "test_super_admin"

        # 创建超级管理员
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        super_admin = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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

        # 重新查询用户以避免DetachedInstanceError
        super_admin = test_session.query(User).filter_by(wechat_openid=openid).first()

        # 测试超级管理员可以获取所有社区
        result_communities, total = CommunityService.get_manageable_communities(super_admin, page=1, per_page=7)

        assert total == 10  # 应该能获取所有社区
        assert len(result_communities) == 7  # 第一页7个
        assert all(comm.status == 1 for comm in result_communities)  # 都是启用状态

    def test_get_manageable_communities_community_manager(self, test_session):
        """测试社区主管获取可管理社区列表"""
        test_context = "test_manager_1"

        # 创建社区主管
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        manager = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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

        # 重新查询用户以避免DetachedInstanceError
        manager = test_session.query(User).filter_by(wechat_openid=openid).first()

        # 测试主管只能获取自己管理的社区
        result_communities, total = CommunityService.get_manageable_communities(manager, page=1, per_page=7)

        assert total == 3  # 只能获取3个自己管理的社区
        assert len(result_communities) == 3
        assert all(comm.status == 1 for comm in result_communities)

    def test_get_manageable_communities_community_staff(self, test_session):
        """测试社区专员获取可管理社区列表"""
        test_context = "test_staff_1"

        # 创建社区专员
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        staff_user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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

        # 重新查询用户以避免DetachedInstanceError
        staff_user = test_session.query(User).filter_by(wechat_openid=openid).first()

        # 测试专员只能获取自己工作的社区
        result_communities, total = CommunityService.get_manageable_communities(staff_user, page=1, per_page=7)

        assert total == 2  # 只能获取2个自己工作的社区
        assert len(result_communities) == 2
        assert all(comm.status == 1 for comm in result_communities)

    def test_get_manageable_communities_no_permission(self, test_session):
        """测试普通用户获取可管理社区列表（无权限）"""
        test_context = "test_normal_user"

        # 创建普通用户
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        normal_user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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
        test_context = "test_search_super_admin"

        # 创建超级管理员
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        super_admin = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
            role=4,
            status=1
        )
        test_session.add(super_admin)

        # 创建包含特定关键词的社区
        community1 = Community(
            name=f"{test_context}_北京朝阳社区",
            description="朝阳区社区",
            status=1
        )
        community2 = Community(
            name=f"{test_context}_上海浦东社区",
            description="浦东新区社区",
            status=1
        )
        community3 = Community(
            name=f"{test_context}_广州天河社区",
            description="天河区社区",
            status=2  # 停用状态
        )

        test_session.add_all([community1, community2, community3])
        test_session.commit()

        # 使用test_context作为搜索关键词，确保只匹配当前测试创建的社区
        results = CommunityService.search_communities_with_permission(super_admin, test_context)

        # 超级管理员应该能看到所有启用状态的社区
        assert len(results) == 2  # 只有2个启用状态的社区
        assert any(comm.name == f"{test_context}_北京朝阳社区" for comm in results)
        assert any(comm.name == f"{test_context}_上海浦东社区" for comm in results)

    def test_search_communities_with_permission_community_manager(self, test_session):
        """测试社区主管搜索社区"""
        test_context = "test_search_manager"

        # 创建社区主管
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        manager = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
            role=3,
            status=1
        )
        test_session.add(manager)

        # 创建多个社区
        community1 = Community(
            name=f"{test_context}_北京朝阳社区",
            description="朝阳区社区",
            status=1
        )
        community2 = Community(
            name=f"{test_context}_上海浦东社区",
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
        assert results[0].name == f"{test_context}_北京朝阳社区"

    def test_can_access_community_permissions(self, test_session):
        """测试社区访问权限检查"""
        test_context = "test_access_permissions"

        # 创建超级管理员
        phone_number_super = generate_unique_phone_number(f"{test_context}_super")
        openid_super = generate_unique_openid(phone_number_super, f"{test_context}_super")
        super_admin = User(
            wechat_openid=openid_super,
            nickname=generate_unique_nickname(f"{test_context}_super"),
            phone_number=phone_number_super,
            role=4,
            status=1
        )

        # 创建社区主管
        phone_number_manager = generate_unique_phone_number(f"{test_context}_manager")
        openid_manager = generate_unique_openid(phone_number_manager, f"{test_context}_manager")
        manager = User(
            wechat_openid=openid_manager,
            nickname=generate_unique_nickname(f"{test_context}_manager"),
            phone_number=phone_number_manager,
            role=3,
            status=1
        )

        # 创建社区专员
        phone_number_staff = generate_unique_phone_number(f"{test_context}_staff")
        openid_staff = generate_unique_openid(phone_number_staff, f"{test_context}_staff")
        staff = User(
            wechat_openid=openid_staff,
            nickname=generate_unique_nickname(f"{test_context}_staff"),
            phone_number=phone_number_staff,
            role=2,
            status=1
        )

        # 创建普通用户
        phone_number_normal = generate_unique_phone_number(f"{test_context}_normal")
        openid_normal = generate_unique_openid(phone_number_normal, f"{test_context}_normal")
        normal_user = User(
            wechat_openid=openid_normal,
            nickname=generate_unique_nickname(f"{test_context}_normal"),
            phone_number=phone_number_normal,
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
        test_context = "test_manage_users_permissions"

        # 创建超级管理员
        phone_number_super = generate_unique_phone_number(f"{test_context}_super")
        openid_super = generate_unique_openid(phone_number_super, f"{test_context}_super")
        super_admin = User(
            wechat_openid=openid_super,
            nickname=generate_unique_nickname(f"{test_context}_super"),
            phone_number=phone_number_super,
            role=4,
            status=1
        )

        # 创建社区主管
        phone_number_manager = generate_unique_phone_number(f"{test_context}_manager")
        openid_manager = generate_unique_openid(phone_number_manager, f"{test_context}_manager")
        manager = User(
            wechat_openid=openid_manager,
            nickname=generate_unique_nickname(f"{test_context}_manager"),
            phone_number=phone_number_manager,
            role=3,
            status=1
        )

        # 创建社区专员
        phone_number_staff = generate_unique_phone_number(f"{test_context}_staff")
        openid_staff = generate_unique_openid(phone_number_staff, f"{test_context}_staff")
        staff = User(
            wechat_openid=openid_staff,
            nickname=generate_unique_nickname(f"{test_context}_staff"),
            phone_number=phone_number_staff,
            role=2,
            status=1
        )

        # 创建普通用户
        phone_number_normal = generate_unique_phone_number(f"{test_context}_normal")
        openid_normal = generate_unique_openid(phone_number_normal, f"{test_context}_normal")
        normal_user = User(
            wechat_openid=openid_normal,
            nickname=generate_unique_nickname(f"{test_context}_normal"),
            phone_number=phone_number_normal,
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
        test_context = "test_manage_staff_permissions"

        # 创建超级管理员
        phone_number_super = generate_unique_phone_number(f"{test_context}_super")
        openid_super = generate_unique_openid(phone_number_super, f"{test_context}_super")
        super_admin = User(
            wechat_openid=openid_super,
            nickname=generate_unique_nickname(f"{test_context}_super"),
            phone_number=phone_number_super,
            role=4,
            status=1
        )

        # 创建社区主管
        phone_number_manager = generate_unique_phone_number(f"{test_context}_manager")
        openid_manager = generate_unique_openid(phone_number_manager, f"{test_context}_manager")
        manager = User(
            wechat_openid=openid_manager,
            nickname=generate_unique_nickname(f"{test_context}_manager"),
            phone_number=phone_number_manager,
            role=3,
            status=1
        )

        # 创建社区专员
        phone_number_staff = generate_unique_phone_number(f"{test_context}_staff")
        openid_staff = generate_unique_openid(phone_number_staff, f"{test_context}_staff")
        staff = User(
            wechat_openid=openid_staff,
            nickname=generate_unique_nickname(f"{test_context}_staff"),
            phone_number=phone_number_staff,
            role=2,
            status=1
        )

        # 创建普通用户
        phone_number_normal = generate_unique_phone_number(f"{test_context}_normal")
        openid_normal = generate_unique_openid(phone_number_normal, f"{test_context}_normal")
        normal_user = User(
            wechat_openid=openid_normal,
            nickname=generate_unique_nickname(f"{test_context}_normal"),
            phone_number=phone_number_normal,
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
        test_context = "test_is_manager_permissions"

        # 创建超级管理员
        phone_number_super = generate_unique_phone_number(f"{test_context}_super")
        openid_super = generate_unique_openid(phone_number_super, f"{test_context}_super")
        super_admin = User(
            wechat_openid=openid_super,
            nickname=generate_unique_nickname(f"{test_context}_super"),
            phone_number=phone_number_super,
            role=4,
            status=1
        )

        # 创建社区主管
        phone_number_manager = generate_unique_phone_number(f"{test_context}_manager")
        openid_manager = generate_unique_openid(phone_number_manager, f"{test_context}_manager")
        manager = User(
            wechat_openid=openid_manager,
            nickname=generate_unique_nickname(f"{test_context}_manager"),
            phone_number=phone_number_manager,
            role=3,
            status=1
        )

        # 创建社区专员
        phone_number_staff = generate_unique_phone_number(f"{test_context}_staff")
        openid_staff = generate_unique_openid(phone_number_staff, f"{test_context}_staff")
        staff = User(
            wechat_openid=openid_staff,
            nickname=generate_unique_nickname(f"{test_context}_staff"),
            phone_number=phone_number_staff,
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
        test_context = "test_ankafamily_success"

        # 检查安卡大家庭社区是否已存在，如果不存在则创建
        ankafamily = test_session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()
        if not ankafamily:
            ankafamily = Community(
                name=DEFAULT_COMMUNITY_NAME,
                description="默认社区",
                is_default=True,
                status=1
            )
            test_session.add(ankafamily)
            test_session.flush()

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
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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
        test_context = "test_ankafamily_not_in"

        # 检查安卡大家庭社区是否已存在，如果不存在则创建
        ankafamily = test_session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()
        if not ankafamily:
            ankafamily = Community(
                name=DEFAULT_COMMUNITY_NAME,
                description="默认社区",
                is_default=True,
                status=1
            )
            test_session.add(ankafamily)
            test_session.flush()

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
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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
        test_context = "test_ankafamily_target_is_ankafamily"

        # 检查安卡大家庭社区是否已存在，如果不存在则创建
        ankafamily = test_session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()
        if not ankafamily:
            ankafamily = Community(
                name=DEFAULT_COMMUNITY_NAME,
                description="默认社区",
                is_default=True,
                status=1
            )
            test_session.add(ankafamily)
            test_session.flush()

        # 先flush获取社区ID
        test_session.flush()

        # 创建用户（在安卡大家庭）
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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
        test_context = "test_ankafamily_not_exist"

        # 删除可能存在的安卡大家庭社区
        existing_ankafamily = test_session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()
        if existing_ankafamily:
            test_session.delete(existing_ankafamily)
            test_session.flush()

        # 创建普通社区（不创建安卡大家庭）
        target_community = Community(
            name=generate_random_community_name(),
            description="目标社区",
            status=1
        )
        test_session.add(target_community)

        # 创建用户
        phone_number = generate_unique_phone_number(test_context)
        openid = generate_unique_openid(phone_number, test_context)
        user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname(test_context),
            phone_number=phone_number,
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
        # 检查安卡大家庭社区是否已存在，如果不存在则创建
        ankafamily = test_session.query(Community).filter_by(name=DEFAULT_COMMUNITY_NAME).first()
        if not ankafamily:
            ankafamily = Community(
                name=DEFAULT_COMMUNITY_NAME,
                description="默认社区",
                is_default=True,
                status=1
            )
            test_session.add(ankafamily)
            test_session.flush()

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