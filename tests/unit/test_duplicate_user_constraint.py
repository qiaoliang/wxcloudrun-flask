"""
测试用户重复约束
验证用户模型的唯一约束行为
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.models import User, Community, CommunityMember


class TestDuplicateUserConstraints:
    """测试用户重复约束"""

    def test_duplicate_openid_constraint(self, test_session):
        """测试微信OpenID唯一约束"""
        # 创建第一个用户
        user1 = User(
            wechat_openid="test_openid_unique",
            nickname="用户1",
            role=1
        )
        test_session.add(user1)
        test_session.commit()
        
        # 尝试创建具有相同OpenID的第二个用户
        user2 = User(
            wechat_openid="test_openid_unique",  # 相同的OpenID
            nickname="用户2",
            role=1
        )
        test_session.add(user2)
        
        # 应该抛出异常
        with pytest.raises(Exception) as exc_info:
            test_session.commit()
        
        # 验证是唯一约束错误
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚
        test_session.rollback()
        
        # 验证只有第一个用户存在
        user_count = test_session.query(User).filter_by(wechat_openid="test_openid_unique").count()
        assert user_count == 1

    def test_duplicate_phone_hash_constraint(self, test_session):
        """测试手机号哈希唯一约束"""
        # 创建第一个用户
        user1 = User(
            wechat_openid="test_phone_1",
            nickname="用户1",
            role=1,
            phone_number="138****8888",
            phone_hash="hash_123456"
        )
        test_session.add(user1)
        test_session.commit()
        
        # 尝试创建具有相同手机号哈希的第二个用户
        user2 = User(
            wechat_openid="test_phone_2",
            nickname="用户2",
            role=1,
            phone_number="139****9999",
            phone_hash="hash_123456"  # 相同的哈希
        )
        test_session.add(user2)
        
        # 应该抛出异常
        with pytest.raises(Exception) as exc_info:
            test_session.commit()
        
        # 验证是唯一约束错误
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚
        test_session.rollback()
        
        # 验证只有第一个用户存在
        user_count = test_session.query(User).filter_by(phone_hash="hash_123456").count()
        assert user_count == 1

    def test_same_user_can_be_added_to_community_twice_current_behavior(self, test_session):
        """测试当前行为：同一用户可以被添加到同一社区两次"""
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
            wechat_openid="test_user_duplicate",
            nickname="重复测试用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 第一次添加用户到社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member1)
        test_session.commit()
        
        # 验证第一次添加成功
        assert member1.id is not None
        
        # 第二次添加同一用户到同一社区
        # 当前实现允许这样做
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member2)
        test_session.commit()
        
        # 验证第二条记录也被创建
        assert member2.id is not None
        assert member1.id != member2.id
        
        # 验证数据库中有两条记录
        count = test_session.query(CommunityMember).filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 2

    def test_different_users_with_same_openid_in_different_communities(self, test_session):
        """测试不同用户在不同社区（概念测试）"""
        # 创建两个社区
        community1 = Community(
            name="社区1",
            description="第一个社区",
            creator_user_id=1
        )
        community2 = Community(
            name="社区2",
            description="第二个社区",
            creator_user_id=1
        )
        test_session.add_all([community1, community2])
        test_session.flush()
        
        # 创建用户
        user = User(
            wechat_openid="test_user_multi",
            nickname="多社区用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 用户加入两个社区
        member1 = CommunityMember(
            community_id=community1.community_id,
            user_id=user.user_id
        )
        member2 = CommunityMember(
            community_id=community2.community_id,
            user_id=user.user_id
        )
        test_session.add_all([member1, member2])
        test_session.commit()
        
        # 验证两条记录都存在
        assert member1.id is not None
        assert member2.id is not None
        assert member1.community_id != member2.community_id
        assert member1.user_id == member2.user_id
        
        # 查询验证
        members = test_session.query(CommunityMember).filter_by(user_id=user.user_id).all()
        assert len(members) == 2

    def test_unique_constraint_on_community_name(self, test_session):
        """测试社区名称唯一约束"""
        # 创建第一个社区
        community1 = Community(
            name="唯一社区名称",
            description="第一个社区",
            creator_user_id=1
        )
        test_session.add(community1)
        test_session.commit()
        
        # 尝试创建同名社区
        community2 = Community(
            name="唯一社区名称",  # 相同名称
            description="第二个社区",
            creator_user_id=2
        )
        test_session.add(community2)
        
        # 应该抛出异常
        with pytest.raises(Exception) as exc_info:
            test_session.commit()
        
        # 验证是唯一约束错误
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚
        test_session.rollback()
        
        # 验证只有第一个社区存在
        community_count = test_session.query(Community).filter_by(name="唯一社区名称").count()
        assert community_count == 1