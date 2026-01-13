"""
测试社区用户管理的单元测试
验证同一用户不能被添加到同一社区两次的功能
使用真实的数据库会话进行测试
"""

import pytest
import sys
import os
from hashlib import sha256

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User, Community

# 添加上级目录到路径以导入test_data_generator
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname
)

# 添加上级目录到路径以导入test_constants
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from test_constants import TEST_CONSTANTS


class TestCommunityUserConstraints:
    """测试社区用户约束"""

    def test_different_users_can_join_same_community(self, test_session):
        """
        测试不同用户可以加入同一社区
        """
        # 创建测试社区
        community = Community(
            name=generate_unique_nickname('test_different_users'),
            description="用于测试的社区",
            creator_id=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建两个不同的用户
        phone1 = generate_unique_phone_number('test_different_users_1')
        phone2 = generate_unique_phone_number('test_different_users_2')
        user1 = User(
            wechat_openid=generate_unique_openid(phone1, 'test_different_users_1'),
            phone_number=phone1,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone1}".encode('utf-8')).hexdigest(),
            nickname=generate_unique_nickname('test_different_users_1'),
            role=1,
            community_id=community.community_id
        )
        user2 = User(
            wechat_openid=generate_unique_openid(phone2, 'test_different_users_2'),
            phone_number=phone2,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone2}".encode('utf-8')).hexdigest(),
            nickname=generate_unique_nickname('test_different_users_2'),
            role=1,
            community_id=community.community_id
        )
        test_session.add(user1)
        test_session.add(user2)
        test_session.flush()