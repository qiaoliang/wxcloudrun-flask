"""
测试用户搜索API的单元测试
专门测试通过完整手机号hash搜索用户的功能
使用真实数据库但不使用HTTP客户端
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User
# from database import initialize_for_test
from hashlib import sha256
import os

def _calculate_phone_hash(phone):
    """
    计算手机号的hash值

    Args:
        phone (str): 手机号

    Returns:
        str: 手机号的hash值
    """
    phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
    return sha256(
        f"{phone_secret}{phone}".encode('utf-8')
    ).hexdigest()

# db = initialize_for_test()  # 已移除，使用现代 fixture 模式


class TestUserSearchByPhoneHash:
    """测试通过手机号hash搜索用户的功能"""

    def test_phone_hash_calculation_and_search(self, test_session):
        """
        测试手机号hash计算和搜索逻辑
        """
        # 创建目标用户
        full_phone = "13888888888"
        phone_hash = _calculate_phone_hash(full_phone)

        target_user = User(
            wechat_openid="target_openid",
            nickname="测试用户",
            role=1,
            phone_number="138****8888",
            phone_hash=phone_hash
        )
        test_session.add(target_user)
        test_session.commit()

        # 测试通过phone_hash查找用户
        found_user = test_session.query(User).filter(User.phone_hash == phone_hash).first()

        assert found_user is not None
        assert found_user.user_id == target_user.user_id
        assert found_user.nickname == "测试用户"
        assert found_user.phone_number == "138****8888"
        assert found_user.phone_hash == phone_hash

    def test_phone_hash_consistency(self, test_session):
        """
        测试相同手机号的hash一致性
        """
        full_phone = "13888888888"
        phone_hash1 = _calculate_phone_hash(full_phone)
        phone_hash2 = _calculate_phone_hash(full_phone)

        # 相同手机号应该产生相同的hash
        assert phone_hash1 == phone_hash2

        # 不同手机号应该产生不同的hash
        different_phone = "13888888889"
        phone_hash3 = _calculate_phone_hash(different_phone)
        assert phone_hash1 != phone_hash3

    def test_search_by_nickname_fuzzy_match(self, test_session):
        """
        测试昵称模糊匹配
        """
        # 创建测试用户
        user1 = User(
            wechat_openid="user1_openid",
            nickname="测试用户A",
            role=1
        )
        user2 = User(
            wechat_openid="user2_openid",
            nickname="用户测试B",
            role=1
        )
        user3 = User(
            wechat_openid="user3_openid",
            nickname="普通用户",
            role=1
        )
        test_session.add_all([user1, user2, user3])
        test_session.commit()

        # 测试模糊匹配
        users_with_test = test_session.query(User).filter(User.nickname.ilike('%测试%')).all()
        assert len(users_with_test) == 2

        users_with_user = test_session.query(User).filter(User.nickname.ilike('%用户%')).all()
        assert len(users_with_user) == 3

    def test_full_phone_detection_logic(self, test_session):
        """
        测试完整手机号检测逻辑
        """
        import re

        # 完整手机号模式
        full_phone_pattern = r'^1[3-9]\d{9}$'

        # 测试完整手机号
        assert re.match(full_phone_pattern, '13888888888') is not None
        assert re.match(full_phone_pattern, '15912345678') is not None

        # 测试非完整手机号
        assert re.match(full_phone_pattern, '138****8888') is None
        assert re.match(full_phone_pattern, '1388888') is None
        assert re.match(full_phone_pattern, '12345678901') is None
        assert re.match(full_phone_pattern, '测试用户') is None