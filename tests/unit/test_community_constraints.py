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

from database.flask_models import  User, Community


class TestCommunityUserConstraints:
    """测试社区用户约束"""

    def test_different_users_can_join_same_community(self, test_session):
        """
        测试不同用户可以加入同一社区
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试的社区",
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建两个不同的用户
        user1 = User(
            wechat_openid="test_user_789",
            nickname="测试用户789",
            role=1,
            community_id=community.community_id
        )
        user2 = User(
            wechat_openid="test_user_999",
            nickname="测试用户999",
            role=1,
            community_id=community.community_id
        )
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()