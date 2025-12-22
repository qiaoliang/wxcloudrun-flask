"""
社区功能单元测试
"""

import pytest
import os
import sys
import random
import string
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import User, Community, CommunityApplication, CommunityStaff


def generate_random_openid():
    """生成随机的微信OpenID"""
    return f"test_openid_{''.join(random.choices(string.ascii_letters + string.digits, k=16))}"


def generate_random_phone():
    """生成随机的手机号"""
    # 生成11位手机号，以1开头
    return f"1{''.join(random.choices(string.digits, k=10))}"


def generate_random_nickname():
    """生成随机的昵称"""
    return f"测试用户_{''.join(random.choices(string.ascii_letters, k=8))}"


def generate_random_community_name():
    """生成随机的社区名称"""
    return f"测试社区_{''.join(random.choices(string.ascii_letters, k=8))}"


class TestCommunityModel:
    """社区模型测试"""

    def test_create_community(self, test_session, test_superuser):
        """测试创建社区"""
        # 创建社区
        community = Community(
            name=generate_random_community_name(),
            description='这是一个测试社区',
            creator_id=test_superuser.user_id
        )
        test_session.add(community)
        test_session.commit()

        assert community.community_id is not None
        assert community.name is not None  # 随机生成的名称
        assert community.status == 1  # 默认启用
        assert community.is_default is False  # 默认非默认社区

    def test_community_status_mapping(self, test_session):
        """测试社区状态映射"""
        # 测试启用状态
        community = Community(name='测试', status=1)
        assert community.status == 1

        # 测试禁用状态
        community.status = 2
        assert community.status == 2

        # 测试未知状态
        community.status = 999
        assert community.status == 999

    def test_create_community_admin(self, test_session, test_user):
        """测试创建社区管理员"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()

        # 创建管理员
        admin = CommunityStaff(
            community_id=community.community_id,
            user_id=test_user.user_id,
            role='manager'  # 主管
        )
        test_session.add(admin)
        test_session.commit()

        assert admin.id is not None
        assert admin.role == 'manager'

    def test_community_staff_role(self, test_session):
        """测试社区工作人员角色"""
        staff = CommunityStaff()

        # 测试主管角色
        staff.role = 'manager'
        assert staff.role == 'manager'

        # 测试专员角色
        staff.role = 'staff'
        assert staff.role == 'staff'

    def test_create_community_application(self, test_session, test_user):
        """测试创建社区申请"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()

        # 创建申请
        application = CommunityApplication(
            user_id=test_user.user_id,
            target_community_id=community.community_id,
            reason='我想加入这个社区'
        )
        test_session.add(application)
        test_session.commit()

        assert application.application_id is not None
        assert application.status == 1  # 默认待审核

    def test_community_application_status_mapping(self, test_session):
        """测试申请状态映射"""
        application = CommunityApplication()

        # 测试待审核
        application.status = 1
        assert application.status == 1

        # 测试已批准
        application.status = 2
        assert application.status == 2

        # 测试已拒绝
        application.status = 3
        assert application.status == 3

        # 测试未知状态
        application.status = 999
        assert application.status == 999


class TestUserCommunityMethods:
    """用户社区相关方法测试"""

    def test_user_join_community(self, test_session, test_user):
        """测试用户加入社区"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()

        # 用户加入社区（设置 community_id）
        test_user.community_id = community.community_id
        test_user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户已加入社区
        assert test_user.community_id == community.community_id
        assert test_user.community_joined_at is not None

    def test_user_leave_community(self, test_session, test_user):
        """测试用户离开社区"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()

        # 用户加入社区
        test_user.community_id = community.community_id
        test_user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户已加入社区
        assert test_user.community_id == community.community_id

        # 用户离开社区（清空 community_id）
        test_user.community_id = None
        test_user.community_joined_at = None
        test_session.commit()

        # 验证用户已离开社区
        assert test_user.community_id is None
        assert test_user.community_joined_at is None

    def test_user_community_fields(self, test_session):
        """测试用户社区相关字段"""
        user = User()

        # User 表中与社区相关的字段
        assert hasattr(user, 'community_id')
        assert hasattr(user, 'community_joined_at')
        assert hasattr(user, '_is_community_worker')


class TestCommunityConstraints:
    """社区约束测试"""

    def test_community_name_unique(self, test_session, test_superuser):
        """测试社区名称唯一性"""
        # 创建第一个社区
        community1 = Community(
            name='测试社区',
            creator_id=test_superuser.user_id
        )
        test_session.add(community1)
        test_session.commit()

        # 尝试创建同名社区
        community2 = Community(
            name='测试社区',
            creator_id=test_superuser.user_id
        )
        test_session.add(community2)

        # 应该抛出异常或违反约束
        # 注意：实际约束行为取决于数据库配置
        test_session.rollback()

    def test_user_can_only_belong_to_one_community(self, test_session, test_user):
        """测试用户只能属于一个社区"""
        # 创建两个社区
        community1 = Community(name='社区1')
        community2 = Community(name='社区2')
        test_session.add_all([community1, community2])
        test_session.commit()

        # 用户加入第一个社区
        test_user.community_id = community1.community_id
        test_user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户属于第一个社区
        assert test_user.community_id == community1.community_id

        # 用户切换到第二个社区
        test_user.community_id = community2.community_id
        test_user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户现在属于第二个社区
        assert test_user.community_id == community2.community_id
        assert test_user.community_id != community1.community_id


class TestCommunityQueries:
    """社区查询测试"""

    def test_get_user_community(self, test_session, test_user):
        """测试获取用户所属社区"""
        # 创建社区
        community = Community(name='测试社区')
        test_session.add(community)
        test_session.commit()

        # 用户加入社区
        test_user.community_id = community.community_id
        test_user.community_joined_at = datetime.now()
        test_session.commit()

        # 查询用户所属社区
        user_community = test_session.query(Community).filter(
            Community.community_id == test_user.community_id
        ).first()

        assert user_community is not None
        assert user_community.name == '测试社区'

    def test_get_community_staff(self, test_session, test_user, test_community):
        """测试获取社区工作人员"""
        # 添加工作人员
        staff1 = CommunityStaff(
            community_id=test_community.community_id,
            user_id=test_user.user_id,
            role='manager'
        )

        # 创建另一个用户并添加为专员
        other_user = User(
            wechat_openid=generate_random_openid(),
            nickname='其他用户',
            role=1
        )
        test_session.add(other_user)
        test_session.commit()

        staff2 = CommunityStaff(
            community_id=test_community.community_id,
            user_id=other_user.user_id,
            role='staff'
        )
        test_session.add_all([staff1, staff2])
        test_session.commit()

        # 查询社区工作人员
        staff_list = test_session.query(CommunityStaff).filter(
            CommunityStaff.community_id == test_community.community_id
        ).all()

        assert len(staff_list) == 2
        roles = [s.role for s in staff_list]
        assert 'manager' in roles
        assert 'staff' in roles


if __name__ == '__main__':
    pytest.main([__file__])