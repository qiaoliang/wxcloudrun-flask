"""
测试用户重复约束
验证用户模型的唯一约束行为
"""

import pytest
import sys
import os
from datetime import datetime

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User, Community


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

    def test_user_can_change_community(self, test_session):
        """测试用户可以更换社区"""
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
            wechat_openid="test_user_change",
            nickname="更换社区用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()

        # 用户加入第一个社区
        user.community_id = community1.community_id
        user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户在第一个社区
        assert user.community_id == community1.community_id

        # 用户更换到第二个社区
        user.community_id = community2.community_id
        user.community_joined_at = datetime.now()
        test_session.commit()

        # 验证用户在第二个社区
        assert user.community_id == community2.community_id
        assert user.community_id != community1.community_id

    def test_different_users_in_same_community(self, test_session):
        """测试不同用户可以在同一个社区"""
        # 创建社区
        community = Community(
            name="共享社区",
            description="多个用户共享的社区",
            creator_user_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建两个用户
        user1 = User(
            wechat_openid="test_user_1",
            nickname="用户1",
            role=1
        )
        user2 = User(
            wechat_openid="test_user_2",
            nickname="用户2",
            role=1
        )
        test_session.add_all([user1, user2])
        test_session.flush()

        # 两个用户加入同一个社区
        user1.community_id = community.community_id
        user1.community_joined_at = datetime.now()
        user2.community_id = community.community_id
        user2.community_joined_at = datetime.now()
        test_session.commit()

        # 验证两个用户都在同一个社区
        assert user1.community_id == community.community_id
        assert user2.community_id == community.community_id
        assert user1.community_id == user2.community_id

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