"""
测试 get_manageable_communities 方法的特殊社区逻辑
验证 role == 4 时是否正确包含安卡大家庭和黑屋社区
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
from const_default import DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_ID, DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME

# 导入测试工具
from community_test_utils import (
    get_or_create_special_communities,
    create_normal_community,
    disable_special_community
)


def generate_random_community_name():
    """生成随机的社区名称"""
    return f"测试社区_{''.join(random.choices(string.ascii_letters, k=8))}"


class TestGetManageableCommunitiesSpecialLogic:
    """测试 get_manageable_communities 的特殊社区逻辑"""

    def test_super_admin_includes_special_communities(self, test_session):
        """
        测试超级管理员获取社区列表时包含特殊社区
        验证安卡大家庭和黑屋社区始终包含在结果中
        """
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1
        )
        test_session.add(super_admin)

        # 获取或创建特殊社区
        ankafamily, blackhouse = get_or_create_special_communities(test_session)

        # 创建其他普通社区
        normal_communities = []
        for i in range(5):
            community = create_normal_community(
                test_session,
                name=f"{generate_random_community_name()}_{i}",
                description=f"普通社区{i}"
            )
            normal_communities.append(community)

        test_session.commit()

        # 重新查询用户以避免DetachedInstanceError
        super_admin = test_session.query(User).filter_by(wechat_openid="super_admin_openid").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(super_admin, page=1, per_page=10)

        # 验证结果包含所有社区
        assert total == 7  # 5个普通社区 + 2个特殊社区
        assert len(result_communities) == 7

        # 验证包含安卡大家庭
        ankafamily_found = any(
            comm.community_id == DEFAULT_COMMUNITY_ID and comm.name == DEFAULT_COMMUNITY_NAME
            for comm in result_communities
        )
        assert ankafamily_found, "结果中应该包含安卡大家庭社区"

        # 验证包含黑屋
        blackhouse_found = any(
            comm.community_id == DEFAULT_BLACK_ROOM_ID and comm.name == DEFAULT_BLACK_ROOM_NAME
            for comm in result_communities
        )
        assert blackhouse_found, "结果中应该包含黑屋社区"

        # 验证所有社区都是启用状态
        assert all(comm.status == 1 for comm in result_communities)

    def test_super_admin_special_communities_disabled(self, test_session):
        """
        测试特殊社区被禁用时的情况
        验证只有启用状态的特殊社区才会被包含
        """
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid_2",
            nickname="超级管理员2",
            role=4,
            status=1
        )
        test_session.add(super_admin)

        # 获取或创建特殊社区
        ankafamily, blackhouse = get_or_create_special_communities(test_session)
        
        # 禁用黑屋社区
        disable_special_community(test_session, DEFAULT_BLACK_ROOM_ID)

        # 创建一个普通社区
        normal_community = create_normal_community(test_session)

        test_session.commit()

        # 重新查询用户
        super_admin = test_session.query(User).filter_by(wechat_openid="super_admin_openid_2").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(super_admin, page=1, per_page=10)

        # 验证结果
        assert total == 2  # 只有安卡大家庭 + 1个普通社区（黑屋被禁用）
        assert len(result_communities) == 2

        # 验证包含启用的安卡大家庭
        ankafamily_found = any(
            comm.community_id == DEFAULT_COMMUNITY_ID and comm.name == DEFAULT_COMMUNITY_NAME
            for comm in result_communities
        )
        assert ankafamily_found, "应该包含启用的安卡大家庭"

        # 验证不包含禁用的黑屋
        blackhouse_found = any(
            comm.community_id == DEFAULT_BLACK_ROOM_ID
            for comm in result_communities
        )
        assert not blackhouse_found, "不应该包含禁用的黑屋社区"

    def test_super_admin_pagination_with_special_communities(self, test_session):
        """
        测试分页时特殊社区的包含逻辑
        验证特殊社区在分页结果中的正确处理
        """
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid_3",
            nickname="超级管理员3",
            role=4,
            status=1
        )
        test_session.add(super_admin)

        # 获取或创建特殊社区
        ankafamily, blackhouse = get_or_create_special_communities(test_session)

        # 创建多个普通社区（总数超过分页大小）
        normal_communities = []
        for i in range(8):
            community = create_normal_community(
                test_session,
                name=f"{generate_random_community_name()}_{i}",
                description=f"普通社区{i}"
            )
            normal_communities.append(community)

        test_session.commit()

        # 重新查询用户
        super_admin = test_session.query(User).filter_by(wechat_openid="super_admin_openid_3").first()

        # 测试第一页（per_page=5）
        result_communities_page1, total = CommunityService.get_manageable_communities(
            super_admin, page=1, per_page=5
        )
        
        # 验证总数
        assert total == 10  # 8个普通社区 + 2个特殊社区
        assert len(result_communities_page1) == 5  # 第一页5个

        # 测试第二页
        result_communities_page2, _ = CommunityService.get_manageable_communities(
            super_admin, page=2, per_page=5
        )
        
        # 验证第二页也有5个
        assert len(result_communities_page2) == 5

        # 合并两页结果
        all_communities = result_communities_page1 + result_communities_page2

        # 验证特殊社区包含在合并结果中
        ankafamily_found = any(
            comm.community_id == DEFAULT_COMMUNITY_ID
            for comm in all_communities
        )
        assert ankafamily_found, "分页结果中应该包含安卡大家庭"

        blackhouse_found = any(
            comm.community_id == DEFAULT_BLACK_ROOM_ID
            for comm in all_communities
        )
        assert blackhouse_found, "分页结果中应该包含黑屋社区"

    def test_non_super_admin_no_special_communities(self, test_session):
        """
        测试非超级管理员用户不获取特殊社区
        验证只有超级管理员才会自动包含特殊社区
        """
        # 创建社区主管
        manager = User(
            wechat_openid="manager_openid",
            nickname="社区主管",
            role=3,  # 社区主管
            status=1
        )
        test_session.add(manager)

        # 获取或创建特殊社区（确保它们存在但不应该被返回）
        get_or_create_special_communities(test_session)

        # 创建普通社区
        normal_community = create_normal_community(test_session)

        # 将主管分配到普通社区
        staff = CommunityStaff(
            community_id=normal_community.community_id,
            user_id=manager.user_id,
            role='manager'
        )
        test_session.add(staff)

        test_session.commit()

        # 重新查询用户
        manager = test_session.query(User).filter_by(wechat_openid="manager_openid").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(manager, page=1, per_page=10)

        # 验证结果只包含用户管理的社区，不包含特殊社区
        assert total == 1  # 只有1个管理的社区
        assert len(result_communities) == 1
        # 验证返回的社区确实是分配的社区（不假设顺序）
        result_community_ids = {comm.community_id for comm in result_communities}
        assert normal_community.community_id in result_community_ids, "应该包含分配的社区"

        # 验证不包含特殊社区
        special_community_ids = [DEFAULT_COMMUNITY_ID, DEFAULT_BLACK_ROOM_ID]
        for comm in result_communities:
            assert comm.community_id not in special_community_ids, "非超级管理员不应该看到特殊社区"

    def test_staff_user_only_assigned_communities(self, test_session):
        """
        测试社区专员只能看到分配的社区
        验证普通工作人员的权限限制
        """
        # 创建社区专员
        staff_user = User(
            wechat_openid="staff_openid",
            nickname="社区专员",
            role=2,  # 社区专员
            status=1
        )
        test_session.add(staff_user)

        # 获取或创建特殊社区（确保它们存在但不应该被返回）
        get_or_create_special_communities(test_session)

        # 创建多个普通社区
        normal_communities = []
        for i in range(3):
            community = create_normal_community(
                test_session,
                name=f"{generate_random_community_name()}_{i}",
                description=f"普通社区{i}"
            )
            normal_communities.append(community)

        # 将专员分配到前2个普通社区
        for i in range(2):
            staff = CommunityStaff(
                community_id=normal_communities[i].community_id,
                user_id=staff_user.user_id,
                role='staff'
            )
            test_session.add(staff)

        test_session.commit()

        # 重新查询用户
        staff_user = test_session.query(User).filter_by(wechat_openid="staff_openid").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(staff_user, page=1, per_page=10)

        # 验证结果只包含分配的社区
        assert total == 2  # 只能获取2个分配的社区
        assert len(result_communities) == 2

        # 验证不包含特殊社区
        result_community_ids = [comm.community_id for comm in result_communities]
        assert DEFAULT_COMMUNITY_ID not in result_community_ids, "专员不应该看到安卡大家庭"
        assert DEFAULT_BLACK_ROOM_ID not in result_community_ids, "专员不应该看到黑屋社区"

        # 验证只包含分配的社区（不假设顺序）
        result_community_ids = {comm.community_id for comm in result_communities}
        expected_community_ids = {comm.community_id for comm in normal_communities[:2]}  # 只取前2个分配的社区
        assert result_community_ids == expected_community_ids, "应该只包含分配的社区"

    def test_user_with_no_staff_assignments(self, test_session):
        """
        测试没有工作人员分配的用户
        验证空结果的处理
        """
        # 创建社区主管但没有分配任何社区
        manager = User(
            wechat_openid="manager_openid_2",
            nickname="社区主管2",
            role=3,
            status=1
        )
        test_session.add(manager)

        # 获取或创建特殊社区（确保它们存在但不应该被返回）
        get_or_create_special_communities(test_session)

        test_session.commit()

        # 重新查询用户
        manager = test_session.query(User).filter_by(wechat_openid="manager_openid_2").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(manager, page=1, per_page=10)

        # 验证空结果
        assert total == 0
        assert len(result_communities) == 0

    def test_special_communities_sorting(self, test_session):
        """
        测试特殊社区在结果中的排序
        验证按创建时间倒序排列的逻辑
        """
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin_openid_4",
            nickname="超级管理员4",
            role=4,
            status=1
        )
        test_session.add(super_admin)

        # 获取或创建特殊社区（它们有固定的创建时间）
        ankafamily, blackhouse = get_or_create_special_communities(test_session)

        # 创建最新社区
        latest_community = create_normal_community(
            test_session,
            created_at=datetime(2023, 12, 1)  # 最新的创建时间
        )

        test_session.commit()

        # 重新查询用户
        super_admin = test_session.query(User).filter_by(wechat_openid="super_admin_openid_4").first()

        # 测试获取可管理社区列表
        result_communities, total = CommunityService.get_manageable_communities(super_admin, page=1, per_page=10)

        # 验证排序（按创建时间倒序）
        assert total == 3
        assert len(result_communities) == 3

        # 验证排序顺序
        for i in range(len(result_communities) - 1):
            assert result_communities[i].created_at >= result_communities[i + 1].created_at, \
                "社区应该按创建时间倒序排列"

        # 验证最新社区排在第一位
        assert result_communities[0].community_id == latest_community.community_id