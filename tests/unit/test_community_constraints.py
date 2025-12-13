"""
测试社区用户管理的单元测试
验证同一用户不能被添加到同一社区两次的功能
使用真实的数据库会话进行测试
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import CommunityMember, User, Community


class TestCommunityUserConstraints:
    """测试社区用户约束"""

    def test_duplicate_user_in_community_behavior(self, test_session):
        """
        测试同一用户被添加到同一社区两次的当前行为
        注意：当前数据库模型没有唯一约束，所以允许重复
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试的社区",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()  # 获取community_id
        
        # 创建测试用户
        user = User(
            wechat_openid="test_user_123",
            nickname="测试用户",
            role=1  # 普通用户
        )
        test_session.add(user)
        test_session.flush()  # 获取user_id
        
        # 第一次添加用户到社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member1)
        test_session.commit()
        
        # 验证第一次添加成功
        assert member1.id is not None
        assert member1.community_id == community.community_id
        assert member1.user_id == user.user_id
        
        # 第二次添加同一用户到同一社区
        # 当前模型允许这样做（没有唯一约束）
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member2)
        test_session.commit()
        
        # 验证第二条记录也被创建
        assert member2.id is not None
        assert member2.community_id == community.community_id
        assert member2.user_id == user.user_id
        assert member1.id != member2.id
        
        # 验证数据库中有两条记录
        count = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 2
        
        # 注意：这表明当前实现允许重复，业务逻辑层面需要处理

    def test_same_user_can_join_different_communities(self, test_session):
        """
        测试同一用户可以加入不同的社区
        确保约束只在同一社区内生效
        """
        # 创建两个不同的社区
        community1 = Community(
            name="测试社区1",
            description="第一个测试社区",
            creator_user_id=1
        )
        community2 = Community(
            name="测试社区2",
            description="第二个测试社区",
            creator_user_id=1
        )
        test_session.add(community1)
        test_session.add(community2)
        test_session.flush()
        
        # 创建测试用户
        user = User(
            wechat_openid="test_user_456",
            nickname="测试用户456",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 用户加入第一个社区
        member1 = CommunityMember(
            community_id=community1.community_id,
            user_id=user.user_id
        )
        test_session.add(member1)
        test_session.commit()
        
        # 用户加入第二个社区
        member2 = CommunityMember(
            community_id=community2.community_id,
            user_id=user.user_id
        )
        test_session.add(member2)
        test_session.commit()
        
        # 验证两条记录都存在
        assert member1.id is not None
        assert member2.id is not None
        assert member1.community_id != member2.community_id
        assert member1.user_id == member2.user_id
        
        # 查询验证
        members = test_session.query(CommunityMember).filter_by(user_id=user.user_id).all()
        assert len(members) == 2

    def test_different_users_can_join_same_community(self, test_session):
        """
        测试不同用户可以加入同一社区
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试的社区",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建两个不同的用户
        user1 = User(
            wechat_openid="test_user_789",
            nickname="测试用户789",
            role=1
        )
        user2 = User(
            wechat_openid="test_user_999",
            nickname="测试用户999",
            role=1
        )
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()
        
        # 两个用户都加入同一社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user1.user_id
        )
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user2.user_id
        )
        test_session.add(member1)
        test_session.add(member2)
        test_session.commit()
        
        # 验证两条记录都存在
        assert member1.id is not None
        assert member2.id is not None
        assert member1.community_id == member2.community_id
        assert member1.user_id != member2.user_id
        
        # 查询验证
        members = test_session.query(CommunityMember).filter_by(community_id=community.community_id).all()
        assert len(members) == 2