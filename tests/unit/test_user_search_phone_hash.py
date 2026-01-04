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
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
from test_constants import TEST_CONSTANTS
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


class TestUserSearchByPhoneHash:
    """测试通过手机号hash搜索用户的功能"""

    def test_phone_hash_calculation_and_search(self, test_session):
        """
        测试手机号hash计算和搜索逻辑
        """
        # 创建目标用户
        full_phone = generate_unique_phone_number("test_phone_hash")
        openid = generate_unique_openid(full_phone, "test_phone_hash")
        phone_hash = _calculate_phone_hash(full_phone)

        target_user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_phone_hash"),
            role=1,
            phone_number=full_phone[:7] + "****" + full_phone[-4:],
            phone_hash=phone_hash
        )
        test_session.add(target_user)
        test_session.commit()

        # 测试通过phone_hash查找用户
        found_user = test_session.query(User).filter(User.phone_hash == phone_hash).first()

        assert found_user is not None
        assert found_user.user_id == target_user.user_id
        assert found_user.nickname == target_user.nickname
        assert found_user.phone_number == full_phone[:7] + "****" + full_phone[-4:]
        assert found_user.phone_hash == phone_hash

    def test_phone_hash_consistency(self, test_session):
        """
        测试相同手机号的hash一致性
        """
        full_phone = generate_unique_phone_number("test_consistency")
        phone_hash1 = _calculate_phone_hash(full_phone)
        phone_hash2 = _calculate_phone_hash(full_phone)

        # 相同手机号应该产生相同的hash
        assert phone_hash1 == phone_hash2

        # 不同手机号应该产生不同的hash
        different_phone = generate_unique_phone_number("test_consistency_diff")
        phone_hash3 = _calculate_phone_hash(different_phone)
        assert phone_hash1 != phone_hash3

    def test_search_by_nickname_fuzzy_match(self, test_session):
        """
        测试昵称模糊匹配
        """
        # 创建测试用户
        phone_number1 = generate_unique_phone_number("test_fuzzy_1")
        openid1 = generate_unique_openid(phone_number1, "test_fuzzy_1")
        
        user1 = User(
            wechat_openid=openid1,
            nickname=generate_unique_nickname("test_fuzzy_1"),
            role=1
        )
        
        phone_number2 = generate_unique_phone_number("test_fuzzy_2")
        openid2 = generate_unique_openid(phone_number2, "test_fuzzy_2")
        
        user2 = User(
            wechat_openid=openid2,
            nickname=generate_unique_nickname("test_fuzzy_2"),
            role=1
        )
        
        phone_number3 = generate_unique_phone_number("test_fuzzy_3")
        openid3 = generate_unique_openid(phone_number3, "test_fuzzy_3")
        
        user3 = User(
            wechat_openid=openid3,
            nickname=generate_unique_nickname("test_fuzzy_3"),
            role=1
        )
        test_session.add_all([user1, user2, user3])
        test_session.commit()

        # 模糊查询 - 使用 LIKE 操作符
        all_users = test_session.query(User).filter(
            User.nickname.like('%nickname%')
        ).all()

        # 验证结果
        assert len(all_users) >= 3, "应该找到至少3个用户"

    def test_search_by_exact_phone_hash(self, test_session):
        """
        测试通过精确的phone_hash搜索用户
        """
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_exact_hash")
        openid = generate_unique_openid(phone_number, "test_exact_hash")
        phone_hash = _calculate_phone_hash(phone_number)

        target_user = User(
            wechat_openid=openid,
            nickname=generate_unique_nickname("test_exact_hash"),
            role=1,
            phone_number=phone_number[:7] + "****" + phone_number[-4:],
            phone_hash=phone_hash
        )
        test_session.add(target_user)
        test_session.commit()

        # 创建其他用户，确保不会误匹配
        other_phone = generate_unique_phone_number("test_exact_hash_other")
        other_openid = generate_unique_openid(other_phone, "test_exact_hash_other")
        other_phone_hash = _calculate_phone_hash(other_phone)
        
        other_user = User(
            wechat_openid=other_openid,
            nickname=generate_unique_nickname("test_exact_hash_other"),
            role=1,
            phone_number=other_phone[:7] + "****" + other_phone[-4:],
            phone_hash=other_phone_hash
        )
        test_session.add(other_user)
        test_session.commit()

        # 精确查询
        found_user = test_session.query(User).filter(User.phone_hash == phone_hash).first()

        # 验证结果
        assert found_user is not None
        assert found_user.user_id == target_user.user_id
        assert found_user.nickname == target_user.nickname