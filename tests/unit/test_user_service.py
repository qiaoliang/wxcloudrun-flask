"""
UserService.create_user 方法的单元测试
遵循测试最佳实践，避免测试反模式
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError
from database.models import User, UserAuditLog
from wxcloudrun.user_service import UserService
from wxcloudrun.dao import get_db  # 使用与 UserService 相同的数据库获取方式
from hashutil import phone_hash, pwd_hash


class TestUserService:
    """测试 UserService.create_user 方法"""

    def test_create_user_success_with_openid_and_nickname(self, test_db, test_session):
        """
        测试成功创建用户的情况
        验证真实行为而非 mock 行为
        """
        # Arrange - 只有openid 和 nickname, avatar_url
        new_user = User(
            wechat_openid="test_openid_new",
            nickname="微信新用户",
            avatar_url="https://example.com/1.jpg"
        )

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果
        assert result is not None
        assert result['wechat_openid'] == "test_openid_new"
        assert result['nickname'] == "微信新用户"
        assert result['name'] == "微信新用户"  # name 设置为 nickname
        assert result['role'] == 1  # 默认角色
        assert result['status'] == 1  # 默认状态
        assert result['verification_status'] == 2  # 默认验证状态
        assert result['_is_community_worker'] is False

        # 验证新微信用户创建时，密码和手机号都是没有值的
        assert result['phone_number'] == ""
        assert result['phone_hash'] == ""
        assert result['password_hash'] ==""

        # 验证用户确实被保存到数据库 - 使用相同的数据库获取方式
        with get_db().get_session() as verify_session:
            saved_user = verify_session.query(User).filter_by(wechat_openid="test_openid_new").first()
            assert saved_user is not None
            assert saved_user.nickname == "微信新用户"

            # 验证审计日志被创建
            audit_log = verify_session.query(UserAuditLog).filter_by(user_id=saved_user.user_id).first()
            assert audit_log is not None
            # 在会话内访问属性
            action = audit_log.action
            detail = audit_log.detail
            assert action == "create_user"
            assert f"创建用户: {saved_user.user_id}" in detail

    def test_create_user_success_with_phone_number_and_pwd(self, test_db, test_session):
        """
        测试使用手机号和密码成功创建用户的情况
        验证真实行为而非 mock 行为
        """
        # Arrange - 手机号注册用户，只有 phone_number 和 password
        original_phone = "13800138000"
        expected_masked_phone = "138****8000"  # 预期的脱敏号码
        new_user = User(
            phone_number=original_phone
        )
        # 动态添加 password 属性（create_user 方法需要它，但它不是数据库字段）
        new_user.password = "test_password_123"

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果
        assert result is not None
        # 验证存储的是脱敏后的手机号
        assert result['phone_number'] == expected_masked_phone
        assert result['wechat_openid'] == ""  # 手机号用户没有 openid
        assert result['nickname'].startswith("用户_")  # nickname 被重写
        assert result['name'] == result['nickname']  # name 设置为 nickname
        assert result['role'] == 1  # 默认角色
        assert result['status'] == 1  # 默认状态
        assert result['verification_status'] == 2  # 默认验证状态
        assert result['_is_community_worker'] is False

        # 验证手机号用户的密码和手机号哈希已正确设置
        # 注意：phone_hash 仍使用原始手机号生成
        assert result['phone_hash'] == phone_hash(original_phone)
        assert result['password_hash'] == pwd_hash("test_password_123")

        # 验证用户确实被保存到数据库
        with get_db().get_session() as verify_session:
            saved_user = verify_session.query(User).filter_by(phone_hash=phone_hash(original_phone)).first()
            assert saved_user is not None
            # 验证数据库中存储的是脱敏号码
            assert saved_user.user_id > 0
            assert saved_user.phone_number == expected_masked_phone
            assert saved_user.wechat_openid == ""  # 手机号用户没有 openid
            assert saved_user.nickname.startswith("用户_")
            assert saved_user.name == saved_user.nickname
            assert saved_user.role == 1
            assert saved_user.status == 1
            assert saved_user.verification_status == 2
            assert saved_user._is_community_worker is False

            # 验证审计日志被创建
            audit_log = verify_session.query(UserAuditLog).filter_by(user_id=saved_user.user_id).first()
            assert audit_log is not None
            # 在会话内访问属性
            action = audit_log.action
            detail = audit_log.detail
            assert action == "create_user"
            assert f"创建用户: {saved_user.user_id}" in detail

    def test_create_user_with_phone_prefix_masking(self, test_db, test_session):
        """
        测试创建带+86前缀的手机号用户时的脱敏功能
        """
        # Arrange - 带+86前缀的手机号
        original_phone = "+8613912345678"
        expected_masked_phone = "139****5678"  # 预期的脱敏号码（前缀被移除）
        new_user = User(
            phone_number=original_phone
        )
        # 动态添加 password 属性（create_user 方法需要它，但它不是数据库字段）
        new_user.password = "test_password_456"

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果
        assert result is not None
        # 验证存储的是脱敏后的手机号（不带+86前缀）
        assert result['phone_number'] == expected_masked_phone

        # 验证phone_hash仍使用原始手机号生成
        assert result['phone_hash'] == phone_hash(original_phone)

        # 验证用户确实被保存到数据库
        with get_db().get_session() as verify_session:
            saved_user = verify_session.query(User).filter_by(phone_hash=phone_hash(original_phone)).first()
            assert saved_user is not None
            # 验证数据库中存储的是脱敏号码
            assert saved_user.phone_number == expected_masked_phone

    def test_is_user_existed_with_wechat_user(self, test_db, test_session):
        """
        测试通过 wechat_openid 检查已存在的微信用户
        """
        # Arrange - 创建一个微信用户
        new_user = User(
            wechat_openid="test_openid_exists",
            nickname="已存在的微信用户",
            avatar_url="https://example.com/1.jpg"
        )
        created_user = UserService.create_user(new_user)
        
        # 创建一个测试用户对象，使用相同的 openid
        test_user = User(wechat_openid="test_openid_exists")
        
        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)
        
        # Assert - 用户应该存在
        assert result is True

    def test_is_user_existed_with_phone_user(self, test_db, test_session):
        """
        测试通过 phone_number 检查已存在的手机号用户
        """
        # Arrange - 创建一个手机号用户
        new_user = User(phone_number="13900139000")
        new_user.password = "test_password_123"
        created_user = UserService.create_user(new_user)
        
        # 创建一个测试用户对象，使用相同的手机号
        test_user = User(phone_number="13900139000")
        test_user.password = "test_password_123"
        
        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)
        
        # Assert - 用户应该存在
        assert result is True

    def test_is_user_existed_with_user_id(self, test_db, test_session):
        """
        测试通过 user_id 检查已存在的用户
        """
        # Arrange - 创建一个用户
        new_user = User(
            wechat_openid="test_openid_for_id",
            nickname="用于ID测试的用户",
            avatar_url="https://example.com/1.jpg"
        )
        created_user = UserService.create_user(new_user)
        
        # 创建一个测试用户对象，设置相同的 user_id
        test_user = User()
        test_user.user_id = created_user['user_id']  # 使用 create_user 返回的 ID
        
        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)
        
        # Assert - 用户应该存在
        assert result is True

    def test_is_user_existed_not_found(self, test_db, test_session):
        """
        测试检查不存在的用户
        """
        # Arrange - 创建一个不存在的用户对象
        test_user = User(
            wechat_openid="nonexistent_openid",
            phone_number="13800138000"
        )
        test_user.password = "test_password"
        
        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)
        
        # Assert - 用户不应该存在
        assert result is False

    def test_is_user_existed_priority_by_user_id(self, test_db, test_session):
        """
        测试当同时有 user_id 和 openid 时，优先使用 user_id 查询
        """
        # Arrange - 创建一个微信用户和一个手机号用户
        wechat_user = User(
            wechat_openid="openid_1",
            nickname="微信用户",
            avatar_url="https://example.com/1.jpg"
        )
        created_wechat_user = UserService.create_user(wechat_user)
        
        phone_user = User(phone_number="13800138001")
        phone_user.password = "test_password"
        created_phone_user = UserService.create_user(phone_user)
        
        # 创建测试用户，使用微信用户的 ID 和手机号
        test_user = User()
        test_user.user_id = created_wechat_user['user_id']
        test_user.phone_number = "13800138001"  # 手机号用户的信息
        test_user.password = "test_password"
        
        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)
        
        # Assert - 应该找到微信用户（通过 ID），而不是手机号用户
        assert result is True
        
        # 验证确实是通过 ID 找到的
        with get_db().get_session() as verify_session:
            found_user = verify_session.query(User).filter_by(user_id=created_wechat_user['user_id']).first()
            assert found_user is not None
            assert found_user.wechat_openid == "openid_1"  # 确认是微信用户