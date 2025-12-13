"""
测试社区用户管理的单元测试
验证社区用户管理功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import CommunityStaff, CommunityMember, User, Community


class TestCommunityUserManagement:
    """测试社区用户管理功能"""
    
    def test_add_user_to_community(self, test_session):
        """
        测试添加用户到社区
        """
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建用户
        user = User(
            wechat_openid="test_user_123",
            nickname="测试用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 添加用户到社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member)
        test_session.commit()
        
        # 验证添加成功
        assert member.id is not None
        assert member.community_id == community.community_id
        assert member.user_id == user.user_id
        
        # 查询验证记录存在
        existing_member = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert existing_member is not None
        assert existing_member.id == member.id
    
    def test_remove_user_from_community(self, test_session):
        """
        测试从社区移除用户
        """
        # 创建社区和用户
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        user = User(
            wechat_openid="test_user_456",
            nickname="测试用户456",
            role=1
        )
        test_session.add(community)
        test_session.add(user)
        test_session.flush()
        
        # 添加用户到社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member)
        test_session.commit()
        
        # 验证用户在社区中
        assert member.id is not None
        
        # 从社区移除用户
        test_session.delete(member)
        test_session.commit()
        
        # 验证用户已不在社区中
        removed_member = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert removed_member is None
    
    def test_add_staff_to_community(self, test_session):
        """
        测试添加工作人员到社区
        """
        # 创建社区和用户
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        user = User(
            wechat_openid="staff_user_123",
            nickname="工作人员",
            role=1
        )
        test_session.add(community)
        test_session.add(user)
        test_session.flush()
        
        # 添加工作人员到社区
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='manager',
            scope='全面管理'
        )
        test_session.add(staff)
        test_session.commit()
        
        # 验证添加成功
        assert staff.id is not None
        assert staff.community_id == community.community_id
        assert staff.user_id == user.user_id
        assert staff.role == 'manager'
        assert staff.scope == '全面管理'
        
        # 查询验证记录存在
        existing_staff = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert existing_staff is not None
        assert existing_staff.id == staff.id
    
    def test_remove_staff_from_community(self, test_session):
        """
        测试从社区移除工作人员
        """
        # 创建社区和用户
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        user = User(
            wechat_openid="staff_user_456",
            nickname="工作人员456",
            role=1
        )
        test_session.add(community)
        test_session.add(user)
        test_session.flush()
        
        # 添加工作人员到社区
        staff = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='staff',
            scope='部分管理'
        )
        test_session.add(staff)
        test_session.commit()
        
        # 验证工作人员在社区中
        assert staff.id is not None
        
        # 从社区移除工作人员
        test_session.delete(staff)
        test_session.commit()
        
        # 验证工作人员已不在社区中
        removed_staff = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert removed_staff is None
    
    def test_list_community_members(self, test_session):
        """
        测试列出社区成员
        """
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                wechat_openid=f"user_{i}",
                nickname=f"用户{i}",
                role=1
            )
            test_session.add(user)
            users.append(user)
        test_session.flush()
        
        # 添加用户到社区
        members = []
        for user in users:
            member = CommunityMember(
                community_id=community.community_id,
                user_id=user.user_id
            )
            test_session.add(member)
            members.append(member)
        test_session.commit()
        
        # 查询社区成员
        community_members = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id
        ).all()
        
        # 验证成员数量
        assert len(community_members) == 3
        
        # 验证成员信息
        member_user_ids = [m.user_id for m in community_members]
        for user in users:
            assert user.user_id in member_user_ids
    
    def test_list_community_staff(self, test_session):
        """
        测试列出社区工作人员
        """
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建多个用户
        users = []
        for i in range(2):
            user = User(
                wechat_openid=f"staff_{i}",
                nickname=f"工作人员{i}",
                role=1
            )
            test_session.add(user)
            users.append(user)
        test_session.flush()
        
        # 添加工作人员到社区
        staff_members = []
        roles = ['manager', 'staff']
        for i, user in enumerate(users):
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user.user_id,
                role=roles[i]
            )
            test_session.add(staff)
            staff_members.append(staff)
        test_session.commit()
        
        # 查询社区工作人员
        community_staff = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id
        ).all()
        
        # 验证工作人员数量
        assert len(community_staff) == 2
        
        # 验证工作人员信息
        staff_roles = [s.role for s in community_staff]
        assert 'manager' in staff_roles
        assert 'staff' in staff_roles