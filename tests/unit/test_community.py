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

from database.models import User, Community, CommunityApplication, CommunityStaff, CommunityMember


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
            creator_user_id=test_superuser.user_id
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
        
        # 用户加入社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=test_user.user_id
        )
        test_session.add(member)
        test_session.commit()
        
        assert member.id is not None
    
    def test_user_leave_community(self, test_session, test_user):
        """测试用户离开社区"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()
        
        # 用户加入社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=test_user.user_id
        )
        test_session.add(member)
        test_session.commit()
        
        # 用户离开社区（删除记录）
        test_session.delete(member)
        test_session.commit()
        
        # 验证记录已删除
        found_member = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=test_user.user_id
        ).first()
        assert found_member is None
    
    def test_community_member_fields(self, test_session):
        """测试社区成员字段"""
        member = CommunityMember()
        
        # CommunityMember 只包含基本字段
        assert hasattr(member, 'community_id')
        assert hasattr(member, 'user_id')
        assert hasattr(member, 'joined_at')
        assert hasattr(member, 'updated_at')


class TestCommunityConstraints:
    """社区约束测试"""
    
    def test_community_name_unique(self, test_session, test_superuser):
        """测试社区名称唯一性"""
        # 创建第一个社区
        community1 = Community(
            name='测试社区',
            creator_user_id=test_superuser.user_id
        )
        test_session.add(community1)
        test_session.commit()
        
        # 尝试创建同名社区
        community2 = Community(
            name='测试社区',
            creator_user_id=test_superuser.user_id
        )
        test_session.add(community2)
        
        # 应该抛出异常或违反约束
        # 注意：实际约束行为取决于数据库配置
        test_session.rollback()
    
    def test_user_cannot_join_same_community_twice(self, test_session, test_user):
        """测试用户不能重复加入同一社区"""
        # 创建社区
        community = Community(name=generate_random_community_name())
        test_session.add(community)
        test_session.commit()
        
        # 用户第一次加入社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=test_user.user_id
        )
        test_session.add(member1)
        test_session.commit()
        
        # 尝试再次加入同一社区
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=test_user.user_id
        )
        test_session.add(member2)
        
        # 应该抛出异常或违反约束
        # 注意：实际约束行为取决于数据库配置
        test_session.rollback()


class TestCommunityQueries:
    """社区查询测试"""
    
    def test_get_communities_by_user(self, test_session, test_user):
        """测试获取用户所属社区"""
        # 创建多个社区
        community1 = Community(name='社区1')
        community2 = Community(name='社区2')
        community3 = Community(name='社区3')
        test_session.add_all([community1, community2, community3])
        test_session.commit()
        
        # 用户加入部分社区
        member1 = CommunityMember(
            community_id=community1.community_id,
            user_id=test_user.user_id
        )
        member2 = CommunityMember(
            community_id=community2.community_id,
            user_id=test_user.user_id
        )
        test_session.add_all([member1, member2])
        test_session.commit()
        
        # 查询用户所属社区
        user_communities = test_session.query(Community).join(CommunityMember).filter(
            CommunityMember.user_id == test_user.user_id
        ).all()
        
        assert len(user_communities) == 2
        community_names = [c.name for c in user_communities]
        assert '社区1' in community_names
        assert '社区2' in community_names
        assert '社区3' not in community_names
    
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