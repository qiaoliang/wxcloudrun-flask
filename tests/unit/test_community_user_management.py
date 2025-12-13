"""
测试社区用户管理的单元测试
验证同一用户不能被添加到同一社区两次的功能
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


class TestCommunityUserManagement:
    """测试社区用户管理功能"""
    
    def setup_method(self):
        """测试前准备"""
        from wxcloudrun import app
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_same_user_cannot_be_added_twice_to_same_community(self):
        """
        测试数据库唯一约束防止同一用户被添加到同一社区两次
        验证CommunityMember表的唯一约束 (community_id, user_id)
        """
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 创建用户
        user = User(
            wechat_openid="test_user_123",
            nickname="测试用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 第一次添加用户到社区 - 应该成功
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
        
        # 查询验证记录存在
        existing_member = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert existing_member is not None
        assert existing_member.id == member1.id
        
        # 尝试第二次添加同一用户到同一社区
        # 这应该因为唯一约束而失败
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member2)
        
        # 捕获预期的数据库异常
        with pytest.raises(Exception) as exc_info:
            db.session.commit()
        
        # 验证异常类型（可能是IntegrityError或其他数据库异常）
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚会话
        db.session.rollback()
        
        # 验证数据库中只有一条记录
        count = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 1
    
    def test_can_add_different_users_to_same_community(self):
        """
        测试不同用户可以被添加到同一社区
        这是正面测试用例，确保正常功能不受影响
        """
        # 创建社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 创建两个不同的用户
        user1 = User(
            wechat_openid="test_user_456",
            nickname="测试用户1",
            role=1
        )
        user2 = User(
            wechat_openid="test_user_789",
            nickname="测试用户2",
            role=1
        )
        db.session.add(user1)
        db.session.add(user2)
        db.session.flush()
        
        # 添加第一个用户 - 应该成功
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user1.user_id
        )
        db.session.add(member1)
        db.session.commit()
        assert member1.id is not None
        
        # 添加第二个用户 - 应该成功
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user2.user_id
        )
        db.session.add(member2)
        db.session.commit()
        assert member2.id is not None
        
        # 验证两个用户都在社区中
        members = CommunityMember.query.filter_by(
            community_id=community.community_id
        ).all()
        assert len(members) == 2
        user_ids = [m.user_id for m in members]
        assert user1.user_id in user_ids
        assert user2.user_id in user_ids
    
    def test_can_add_same_user_to_different_communities(self):
        """
        测试同一用户可以被添加到不同的社区
        确保约束只在同一社区内生效
        """
        # 创建两个不同的社区
        community1 = Community(
            name="测试社区1",
            description="测试社区1描述",
            creator_user_id=1
        )
        community2 = Community(
            name="测试社区2",
            description="测试社区2描述",
            creator_user_id=1
        )
        db.session.add(community1)
        db.session.add(community2)
        db.session.flush()
        
        # 创建用户
        user = User(
            wechat_openid="test_user_multi",
            nickname="多社区用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 添加用户到第一个社区 - 应该成功
        member1 = CommunityMember(
            community_id=community1.community_id,
            user_id=user.user_id
        )
        db.session.add(member1)
        db.session.commit()
        assert member1.id is not None
        
        # 添加同一用户到第二个社区 - 应该成功
        member2 = CommunityMember(
            community_id=community2.community_id,
            user_id=user.user_id
        )
        db.session.add(member2)
        db.session.commit()
        assert member2.id is not None
        
        # 验证用户在两个社区中都有记录
        member_from_db1 = CommunityMember.query.filter_by(
            community_id=community1.community_id,
            user_id=user.user_id
        ).first()
        assert member_from_db1 is not None
        
        member_from_db2 = CommunityMember.query.filter_by(
            community_id=community2.community_id,
            user_id=user.user_id
        ).first()
        assert member_from_db2 is not None
        
        # 验证是两条不同的记录
        assert member_from_db1.id != member_from_db2.id