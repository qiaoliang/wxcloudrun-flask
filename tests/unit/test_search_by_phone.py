"""
测试通过手机号搜索用户的功能
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.model import User
from wxcloudrun.views.user import _calculate_phone_hash
from wxcloudrun import db


class TestSearchUsersByPhoneNumber:
    """测试通过手机号搜索用户的功能"""

    def test_search_users_by_phone_number(self, test_client):
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
        db.session.add(user)
        db.session.commit()
        
        # 验证用户创建成功
        assert user.user_id is not None
        assert user.phone_hash is not None
        assert user.phone_number == "138****5678"
        
        # 测试通过完整手机号hash查找用户
        phone_hash = _calculate_phone_hash(test_phone)
        found_user = User.query.filter_by(phone_hash=phone_hash).first()
        
        assert found_user is not None
        assert found_user.user_id == user.user_id
        assert found_user.nickname == "手机号测试用户"
        
        # 测试通过错误手机号hash查找用户
        wrong_phone_hash = _calculate_phone_hash("13987654321")
        wrong_user = User.query.filter_by(phone_hash=wrong_phone_hash).first()
        
        assert wrong_user is None
        
        # 测试部分手机号无法匹配（因为存储的是hash）
        # 这验证了安全性：不能通过部分手机号推断完整手机号
        partial_phone_search = User.query.filter(
            User.phone_number.like("%12345678%")
        ).all()
        
        # 应该找不到，因为存储的是部分隐藏的手机号
        assert len(partial_phone_search) == 0
        
        print("✅ 通过手机号hash搜索用户功能正常")

    def test_phone_hash_calculation_consistency(self, test_client):
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
        different_phone = "13812345678"
        different_hash = _calculate_phone_hash(different_phone)
        
        assert hash1 != different_hash
        
        # 验证hash是SHA256格式（64个字符）
        assert len(hash1) == 64
        assert all(c in '0123456789abcdef' for c in hash1.lower())
        
        print("✅ Phone hash计算一致性验证通过")

    def test_search_users_with_multiple_phone_numbers(self, test_client):
        """
        测试搜索多个用户的手机号
        """
        # 创建多个用户，每个都有不同的手机号
        users_data = [
            ("13811111111", "用户1"),
            ("13822222222", "用户2"),
            ("13833333333", "用户3")
        ]
        
        created_users = []
        for phone, nickname in users_data:
            user = User(
                wechat_openid=f"user_{phone}",
                nickname=nickname,
                role=1,
                phone_number=f"{phone[:3]}****{phone[-4:]}",
                phone_hash=_calculate_phone_hash(phone)
            )
            db.session.add(user)
            created_users.append(user)
        
        db.session.commit()
        
        # 测试每个手机号都能找到对应的用户
        for phone, nickname in users_data:
            phone_hash = _calculate_phone_hash(phone)
            found_user = User.query.filter_by(phone_hash=phone_hash).first()
            
            assert found_user is not None
            assert found_user.nickname == nickname
            assert found_user.phone_number == f"{phone[:3]}****{phone[-4:]}"
        
        print("✅ 多个用户手机号搜索功能正常")


@pytest.fixture
def test_client():
    """创建测试客户端和数据库会话"""
    from wxcloudrun import app
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()