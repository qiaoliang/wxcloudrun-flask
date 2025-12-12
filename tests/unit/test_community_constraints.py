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

from wxcloudrun.model_community_extensions import CommunityMember
from wxcloudrun.model import User, Community
from wxcloudrun import db


class TestCommunityUserConstraints:
    """测试社区用户约束"""

    def test_unique_constraint_prevents_duplicate_user_in_community(self, test_client):
        """
        测试数据库唯一约束防止同一用户被添加到同一社区两次
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试的社区",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()  # 获取community_id
        
        # 创建测试用户
        user = User(
            wechat_openid="test_user_123",
            nickname="测试用户",
            role=1  # 普通用户
        )
        db.session.add(user)
        db.session.flush()  # 获取user_id
        
        # 第一次添加用户到社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member1)
        db.session.commit()
        
        # 验证第一次添加成功
        assert member1.id is not None
        assert member1.community_id == community.community_id
        assert member1.user_id == user.user_id
        
        # 尝试第二次添加同一用户到同一社区
        # 这应该因为唯一约束而失败
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        
        # 捕获预期的数据库异常
        with pytest.raises(Exception) as exc_info:
            db.session.add(member2)
            db.session.commit()
        
        # 验证异常类型（可能是IntegrityError或其他数据库异常）
        assert "unique" in str(exc_info.value).lower() or "constraint" in str(exc_info.value).lower()
        
        # 回滚会话
        db.session.rollback()
        
        # 验证数据库中只有一条记录
        count = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 1
        
        print("✅ 唯一约束成功防止了重复添加用户到同一社区")

    def test_same_user_can_join_different_communities(self, test_client):
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
        db.session.add(community1)
        db.session.add(community2)
        db.session.flush()
        
        # 创建测试用户
        user = User(
            wechat_openid="test_user_456",
            nickname="测试用户456",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 用户加入第一个社区
        member1 = CommunityMember(
            community_id=community1.community_id,
            user_id=user.user_id
        )
        db.session.add(member1)
        db.session.commit()
        
        # 用户加入第二个社区
        member2 = CommunityMember(
            community_id=community2.community_id,
            user_id=user.user_id
        )
        db.session.add(member2)
        db.session.commit()
        
        # 验证两条记录都存在
        assert member1.id is not None
        assert member2.id is not None
        assert member1.community_id != member2.community_id
        assert member1.user_id == member2.user_id
        
        # 查询验证
        members = CommunityMember.query.filter_by(user_id=user.user_id).all()
        assert len(members) == 2
        
        print("✅ 同一用户成功加入了两个不同的社区")

    def test_different_users_can_join_same_community(self, test_client):
        """
        测试不同用户可以加入同一社区
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试的社区",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
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
        db.session.add(user1)
        db.session.add(user2)
        db.session.flush()
        
        # 两个用户都加入同一社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user1.user_id
        )
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user2.user_id
        )
        db.session.add(member1)
        db.session.add(member2)
        db.session.commit()
        
        # 验证两条记录都存在
        assert member1.id is not None
        assert member2.id is not None
        assert member1.community_id == member2.community_id
        assert member1.user_id != member2.user_id
        
        # 查询验证
        members = CommunityMember.query.filter_by(community_id=community.community_id).all()
        assert len(members) == 2
        
        print("✅ 两个不同用户成功加入了同一社区")


@pytest.fixture
def test_client():
    """创建测试客户端和数据库会话"""
    from wxcloudrun import app
    
    # 设置测试环境
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        # 创建所有表
        db.create_all()
        
        yield app.test_client()
        
        # 清理
        db.drop_all()