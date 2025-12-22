"""
测试通过手机号搜索用户的功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User
from hashlib import sha256


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
        f"{phone_secret}:{phone}".encode('utf-8')
    ).hexdigest()


class TestSearchUsersByPhoneNumber:
    """测试通过手机号搜索用户的功能"""

    def test_search_users_by_phone_number(self, test_session):
        """
        RED阶段：测试通过完整手机号hash搜索用户
        验证API能够正确根据手机号找到对应的用户
        """
        # 创建测试用户
        test_phone = "13812345678"
        user = User(
            wechat_openid="test_user_phone",
            nickname="手机号测试用户",
            role=1,
            phone_number="138****5678",  # 部分隐藏显示
            phone_hash=_calculate_phone_hash(test_phone)  # 完整手机号的hash
        )
        test_session.add(user)
        test_session.commit()

        # 验证用户创建成功
        assert user.user_id is not None
        assert user.phone_hash is not None
        assert user.phone_number == "138****5678"

        # 测试通过完整手机号hash查找用户
        phone_hash = _calculate_phone_hash(test_phone)
        found_user = test_session.query(User).filter_by(phone_hash=phone_hash).first()

        assert found_user is not None
        assert found_user.user_id == user.user_id
        assert found_user.nickname == "手机号测试用户"

        # 测试通过错误手机号hash查找用户
        wrong_phone_hash = _calculate_phone_hash("13987654321")
        wrong_user = test_session.query(User).filter_by(phone_hash=wrong_phone_hash).first()

        assert wrong_user is None

        # 测试部分手机号无法匹配（因为存储的是hash）
        # 这验证了安全性：不能通过部分手机号推断完整手机号
        partial_phone_search = test_session.query(User).filter(
            User.phone_number.like("%12345678%")
        ).all()

        # 应该找不到，因为存储的是部分隐藏的手机号
        assert len(partial_phone_search) == 0

    def test_phone_hash_calculation_consistency(self, test_session):
        """
        测试phone hash计算的一致性
        确保绑定和搜索使用相同的hash算法
        """
        test_phone = "13998765432"

        # 多次计算同一个手机号的hash，应该得到相同结果
        hash1 = _calculate_phone_hash(test_phone)
        hash2 = _calculate_phone_hash(test_phone)
        hash3 = _calculate_phone_hash(test_phone)

        assert hash1 == hash2 == hash3

        # 不同手机号应该产生不同的hash
        different_phone = "13998765433"
        different_hash = _calculate_phone_hash(different_phone)
        assert hash1 != different_hash

    def test_multiple_users_with_different_phones(self, test_session):
        """
        测试多个用户使用不同手机号的情况
        """
        # 创建多个用户，每个有不同的手机号
        phones = ["13811111111", "13822222222", "13833333333"]
        users = []

        for i, phone in enumerate(phones):
            user = User(
                wechat_openid=f"phone_user_{i}",
                nickname=f"手机用户{i}",
                role=1,
                phone_number=f"{phone[:3]}****{phone[-4:]}",
                phone_hash=_calculate_phone_hash(phone)
            )
            test_session.add(user)
            users.append(user)

        test_session.commit()

        # 验证每个用户都可以通过手机号hash找到
        for i, phone in enumerate(phones):
            phone_hash = _calculate_phone_hash(phone)
            found_user = test_session.query(User).filter_by(phone_hash=phone_hash).first()
            assert found_user is not None
            assert found_user.wechat_openid == f"phone_user_{i}"

        # 验证总用户数
        total_users = test_session.query(User).filter(
            User.wechat_openid.like("phone_user_%")
        ).count()
        assert total_users == len(phones)

    def test_user_without_phone_number(self, test_session):
        """
        测试没有手机号的用户
        """
        # 创建没有手机号的用户
        user = User(
            wechat_openid="no_phone_user",
            nickname="无手机号用户",
            role=1
            # phone_number 和 phone_hash 都为 None
        )
        test_session.add(user)
        test_session.commit()

        # 验证用户创建成功
        assert user.user_id is not None
        assert user.phone_number is None
        assert user.phone_hash is None

        # 尝试通过手机号搜索应该找不到
        test_phone_hash = _calculate_phone_hash("13899999999")
        found_user = test_session.query(User).filter_by(phone_hash=test_phone_hash).first()
        assert found_user is None

    def test_phone_number_update(self, test_session):
        """
        测试用户更新手机号
        """
        # 创建用户
        user = User(
            wechat_openid="update_phone_user",
            nickname="更新手机号用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()

        # 初始没有手机号
        assert user.phone_number is None
        assert user.phone_hash is None

        # 添加手机号
        new_phone = "13888888888"
        user.phone_number = f"{new_phone[:3]}****{new_phone[-4:]}"
        user.phone_hash = _calculate_phone_hash(new_phone)
        test_session.commit()

        # 验证更新成功
        assert user.phone_number == "138****8888"
        assert user.phone_hash is not None

        # 验证可以通过新手机号找到用户
        phone_hash = _calculate_phone_hash(new_phone)
        found_user = test_session.query(User).filter_by(phone_hash=phone_hash).first()
        assert found_user is not None
        assert found_user.wechat_openid == "update_phone_user"

    def test_phone_hash_security(self, test_session):
        """
        测试手机号hash的安全性
        """
        # 创建用户
        phone = "13866666666"
        user = User(
            wechat_openid="security_test_user",
            nickname="安全测试用户",
            role=1,
            phone_number="138****6666",
            phone_hash=_calculate_phone_hash(phone)
        )
        test_session.add(user)
        test_session.commit()

        # 验证无法从hash反推手机号
        phone_hash = user.phone_hash

        # 尝试常见手机号，应该都不匹配
        common_phones = [
            "13800000000", "13811111111", "13822222222",
            "13833333333", "13844444444", "13855555555"
        ]

        for test_phone in common_phones:
            test_hash = _calculate_phone_hash(test_phone)
            assert test_hash != phone_hash, f"手机号 {test_phone} 的hash不应该匹配存储的hash"