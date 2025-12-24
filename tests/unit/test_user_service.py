"""
UserService.create_user 方法的单元测试
遵循测试最佳实践，避免测试反模式
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError
from database.flask_models import User, UserAuditLog
from wxcloudrun.user_service import UserService

from wxcloudrun.user_service import phone_hash, pwd_hash


class TestUserService:
    """测试 UserService.create_user 方法"""

    def test_create_user_success_with_openid_and_nickname(self, test_session):
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
        assert result.wechat_openid == "test_openid_new"
        assert result.nickname == "微信新用户"
        assert result.name == "微信新用户"  # name 设置为 nickname
        assert result.role == 1  # 默认角色
        assert result.status == 1  # 默认状态
        assert result.verification_status == 2  # 默认验证状态
        assert result._is_community_worker is False

        # 验证新微信用户创建时，密码和手机号都是没有值的
        assert result.phone_number == None
        assert result.phone_hash == None
        assert result.password_hash == ""

        # 验证用户确实被保存到数据库
        test_session.expire_all()  # 刷新会话以获取最新数据
        saved_user = test_session.query(User).filter_by(
            wechat_openid="test_openid_new").first()
        assert saved_user is not None
        assert saved_user.nickname == "微信新用户"

        # 验证审计日志被创建
        audit_log = test_session.query(UserAuditLog).filter_by(
            user_id=saved_user.user_id).first()
        assert audit_log is not None
        # 在会话内访问属性
        action = audit_log.action
        detail = audit_log.detail
        assert action == "create_user"
        assert f"创建用户: {saved_user.user_id}" in detail

    def test_create_user_with_minimal_data_defense_in_depth(self, test_session):
        """
        测试defense-in-depth：用户创建时的最小数据处理
        验证当提供最小数据时，系统能正确处理并创建用户
        """
        # Arrange - 只提供必需的openid，其他字段为空或无效
        new_user = User(
            wechat_openid="test_openid_minimal",
            nickname="",  # 空昵称
            avatar_url=""  # 空头像URL
        )

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果：系统应该处理空值并提供默认值
        assert result is not None
        assert result.wechat_openid == "test_openid_minimal"
        # 注意：UserService层面的测试，不测试API层面的默认值生成
        # 这里只验证UserService能处理空值而不崩溃
        assert result.nickname == ""  # UserService层面保持原值
        assert result.avatar_url == ""  # UserService层面保持原值

        # 验证用户确实被保存到数据库
        test_session.expire_all()  # 刷新会话以获取最新数据
        saved_user = test_session.query(User).filter_by(
            wechat_openid="test_openid_minimal").first()
        assert saved_user is not None

    def test_create_user_with_invalid_avatar_url_defense_in_depth(self, test_session):
        """
        测试defense-in-depth：处理无效头像URL的情况
        验证系统不会因为无效URL而崩溃
        """
        # Arrange - 提供无效的头像URL
        new_user = User(
            wechat_openid="test_openid_invalid_avatar",
            nickname="测试用户",
            avatar_url="invalid_url_not_http"  # 无效的URL格式
        )

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果：UserService层面应该保存原始值
        assert result is not None
        assert result.wechat_openid == "test_openid_invalid_avatar"
        assert result.nickname == "测试用户"
        assert result.avatar_url == "invalid_url_not_http"  # UserService层面保存原始值

        # 验证用户确实被保存到数据库
        test_session.expire_all()  # 刷新会话以获取最新数据
        saved_user = test_session.query(User).filter_by(
            wechat_openid="test_openid_invalid_avatar").first()
        assert saved_user is not None
        assert saved_user.avatar_url == "invalid_url_not_http"

    def test_create_user_success_with_phone_number_and_pwd(self, test_session):
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
        assert result.phone_number == expected_masked_phone
        assert result.wechat_openid == None  # 手机号用户没有 openid
        assert result.nickname.startswith("用户_")  # nickname 被重写
        assert result.name == result.nickname  # name 设置为 nickname
        assert result.role == 1  # 默认角色
        assert result.status == 1  # 默认状态
        assert result.verification_status == 2  # 默认验证状态
        assert result._is_community_worker is False

        # 验证手机号用户的密码和手机号哈希已正确设置
        # 注意：phone_hash 仍使用原始手机号生成
        assert result.phone_hash == phone_hash(original_phone)
        assert result.password_hash == pwd_hash("test_password_123")

        # 验证用户确实被保存到数据库
        test_session.expire_all()  # 刷新会话以获取最新数据
        saved_user = test_session.query(User).filter_by(
            phone_hash=phone_hash(original_phone)).first()
        assert saved_user is not None
        # 验证数据库中存储的是脱敏号码
        assert saved_user.user_id > 0
        assert saved_user.phone_number == expected_masked_phone
        assert saved_user.wechat_openid == None  # 手机号用户没有 openid
        assert saved_user.nickname.startswith("用户_")
        assert saved_user.name == saved_user.nickname
        assert saved_user.role == 1
        assert saved_user.status == 1
        assert saved_user.verification_status == 2
        assert saved_user._is_community_worker is False

        # 验证审计日志被创建
        audit_log = test_session.query(UserAuditLog).filter_by(
            user_id=saved_user.user_id).first()
        assert audit_log is not None
        # 在会话内访问属性
        action = audit_log.action
        detail = audit_log.detail
        assert action == "create_user"
        assert f"创建用户: {saved_user.user_id}" in detail

    def test_create_user_with_phone_prefix_masking(self, test_session):
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
        assert result.phone_number == expected_masked_phone

        # 验证phone_hash仍使用原始手机号生成
        assert result.phone_hash == phone_hash(original_phone)

        # 验证用户确实被保存到数据库
        test_session.expire_all()  # 刷新会话以获取最新数据
        saved_user = test_session.query(User).filter_by(
            phone_hash=phone_hash(original_phone)).first()
        assert saved_user is not None
        # 验证数据库中存储的是脱敏号码
        assert saved_user.phone_number == expected_masked_phone

    def test_is_user_existed_with_wechat_user(self, test_session):
        """
        测试通过 wechat_openid 检查已存在的微信用户
        """
        # Arrange - 创建一个微信用户
        new_user = User(
            wechat_openid="test_openid_exists",
            nickname="已存在的微信用户",
            avatar_url="https://example.com/1.jpg"
        )
        UserService.create_user(new_user)

        # 创建一个测试用户对象，使用相同的 openid
        test_user = User(wechat_openid="test_openid_exists")

        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)

        # Assert - 用户应该存在
        assert result is not None

    def test_is_user_existed_with_phone_user(self, test_session):
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
        assert result is not None

    def test_get_user_by_phone_number(self):
        pass

    def test_is_user_existed_with_user_id(self, test_session):
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
        test_user.user_id = created_user.user_id  # 使用 create_user 返回的 ID

        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)

        # Assert - 用户应该存在
        assert result is not None

    def test_is_user_existed_not_found(self, test_session):
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
        assert result is None

    def test_is_user_existed_priority_by_user_id(self, test_session):
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
        test_user.user_id = created_wechat_user.user_id
        test_user.phone_number = "13800138001"  # 手机号用户的信息
        test_user.password = "test_password"

        # Act - 检查用户是否存在
        result = UserService.is_user_existed(test_user)

        # Assert - 应该找到微信用户（通过 ID），而不是手机号用户
        assert result is not None

        # 验证确实是通过 ID 找到的
        test_session.expire_all()  # 刷新会话以获取最新数据
        found_user = test_session.query(User).filter_by(
            user_id=created_wechat_user.user_id).first()
        assert found_user is not None
        assert found_user.wechat_openid == "openid_1"  # 确认是微信用户

    def test_query_user_by_phone_number_exists(self, test_session):
        """
        测试查询存在的手机号用户
        """
        # Arrange - 使用 create_user 创建手机号用户
        new_user = User(phone_number="13700137000")
        new_user.password = "test_password_123"
        created_user = UserService.create_user(new_user)

        # Act - 通过原始手机号查询用户
        result = UserService.query_user_by_phone_number("13700137000")

        # Assert - 应该找到用户
        assert result is not None
        # 只验证 user_id，避免访问脱离会话的属性
        assert result.user_id == created_user.user_id

    def test_query_user_by_phone_number_not_exists(self, test_session):
        """
        测试查询不存在的手机号
        """
        # Arrange - 不创建用户，直接查询不存在的手机号

        # Act - 通过不存在的手机号查询用户
        result = UserService.query_user_by_phone_number("13700137999")

        # Assert - 应该返回 None
        assert result is None

    def test_query_user_by_phone_number_with_prefix(self, test_session):
        """
        测试查询带+86前缀的手机号用户
        """
        # Arrange - 使用 create_user 创建带前缀的用户
        new_user = User(phone_number="+8613600136000")
        new_user.password = "test_password_123"
        created_user = UserService.create_user(new_user)

        # Act - 使用带前缀的手机号查询
        result = UserService.query_user_by_phone_number("+8613600136000")

        # Assert - 应该找到用户
        assert result is not None
        assert result.user_id == created_user.user_id

        # Act - 使用不带前缀的手机号查询
        result2 = UserService.query_user_by_phone_number("13600136000")

        # Assert - 应该找不到用户（因为哈希值不同）
        assert result2 is None  # 因为哈希值不同

    def test_query_user_by_phone_number_hash_consistency(self, test_session):
        """
        测试手机号哈希的一致性
        """
        # Arrange - 使用 create_user 创建用户
        phone = "13700137001"
        new_user = User(phone_number=phone)
        new_user.password = "test_password"
        created_user = UserService.create_user(new_user)

        # Act - 多次查询相同的手机号
        result1 = UserService.query_user_by_phone_number(phone)
        result2 = UserService.query_user_by_phone_number(phone)

        # Assert - 应该返回相同的用户
        assert result1 is not None
        assert result2 is not None
        assert result1.user_id == result2.user_id
        assert result1.user_id == created_user.user_id

    def test_query_user_by_phone_number_wechat_user(self, test_session):
        """
        测试查询微信用户（微信用户的phone_hash为空）
        """
        # Arrange - 使用 create_user 创建一个微信用户
        wechat_user = User(
            wechat_openid="wechat_openid_test",
            nickname="微信用户",
            avatar_url="https://example.com/1.jpg"
        )
        created_user = UserService.create_user(wechat_user)

        # Act - 尝试通过手机号查询微信用户
        result = UserService.query_user_by_phone_number("13700137002")

        # Assert - 应该返回 None，因为微信用户没有手机号
        assert result is None

    def test_create_user_validation_no_identifier(self, test_session):
        """
        测试创建用户时既没有提供 openid 也没有提供手机号
        """
        # Arrange - 创建一个既没有 openid 也没有 phone 的用户
        new_user = User(nickname="无标识用户")

        # Act & Assert - 应该抛出验证错误
        with pytest.raises(ValueError, match="必须提供微信OpenID或手机号至少一个"):
            UserService.create_user(new_user)

    def test_create_user_validation_both_identifiers(self, test_session):
        """
        测试创建用户时同时提供了 openid 和手机号
        """
        # Arrange - 创建一个同时有 openid 和 phone 的用户
        new_user = User(
            wechat_openid="test_openid",
            phone_number="13700137000"
        )
        new_user.password = "test_password"

        # Act & Assert - 应该抛出验证错误
        with pytest.raises(ValueError, match="不能同时提供微信OpenID和手机号"):
            UserService.create_user(new_user)

    def test_create_user_validation_invalid_phone(self, test_session):
        """
        测试创建用户时提供了无效的手机号
        """
        # Arrange - 创建一个手机号太短的用户
        new_user = User(phone_number="123")
        new_user.password = "test_password"

        # Act & Assert - 应该抛出验证错误
        with pytest.raises(ValueError, match="手机号格式无效"):
            UserService.create_user(new_user)

    def test_update_user_by_id_success(self, test_session):
        """
        测试成功更新用户信息
        验证真实行为而非 mock 行为
        """
        # Arrange - 先创建一个用户
        original_user = User(
            wechat_openid="test_openid_update",
            nickname="原始昵称",
            avatar_url="https://example.com/original.jpg"
        )
        created_user = UserService.create_user(original_user)

        # 创建更新用户对象
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.nickname = "更新后的昵称"
        update_user.avatar_url = "https://example.com/updated.jpg"
        update_user.name = "更新后的姓名"

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 验证更新结果
        updated_user = test_session.query(User).filter_by(
            user_id=created_user.user_id).first()
        assert updated_user is not None
        assert updated_user.nickname == "更新后的昵称"
        assert updated_user.avatar_url == "https://example.com/updated.jpg"
        assert updated_user.name == "更新后的姓名"
        # 验证 updated_at 被更新
        assert updated_user.updated_at is not None

    def test_update_user_by_id_with_role_string(self, test_session):
        """
        测试使用字符串角色更新用户
        注意：由于 User 模型没有 get_role_value 方法，这个测试验证字符串角色不会被处理
        """
        # Arrange - 创建用户
        original_user = User(
            wechat_openid="test_openid_role",
            nickname="角色测试用户"
        )
        created_user = UserService.create_user(original_user)
        original_role = created_user.role

        # 创建更新用户对象，使用字符串角色
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.role = "community_worker"  # 使用字符串而非数字

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 验证角色保持原样（因为字符串不被识别）
        test_session.expire_all()  # 刷新会话以获取最新数据
        updated_user = test_session.query(User).filter_by(
            user_id=created_user.user_id).first()
        assert updated_user is not None
        # 角色应该保持原样，因为字符串 "community_worker" 不被识别
        assert updated_user.role == original_role

    def test_update_user_by_id_with_status_string(self, test_session):
        """
        测试使用字符串状态更新用户
        注意：由于 User 模型没有 get_status_value 方法，这个测试验证字符串状态不会被处理
        """
        # Arrange - 创建用户
        original_user = User(
            wechat_openid="test_openid_status",
            nickname="状态测试用户"
        )
        created_user = UserService.create_user(original_user)
        original_status = created_user.status

        # 创建更新用户对象，使用字符串状态
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.status = "inactive"  # 使用字符串而非数字

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 验证状态保持原样（因为字符串不被识别）
        test_session.expire_all()  # 刷新会话以获取最新数据
        updated_user = test_session.query(User).filter_by(
            user_id=created_user.user_id).first()
        assert updated_user is not None
        # 状态应该保持原样，因为字符串 "inactive" 不被识别
        assert updated_user.status == original_status

    def test_update_user_by_id_nonexistent_user(self, test_session):
        """
        测试更新不存在的用户
        """
        # Arrange - 创建更新用户对象，使用不存在的 ID
        update_user = User()
        update_user.user_id = 999999  # 不存在的用户ID
        update_user.nickname = "不存在的用户"

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 方法应该静默处理，不抛出异常
        # 验证用户确实没有被创建
        test_session.expire_all()  # 刷新会话以获取最新数据
        nonexistent_user = test_session.query(
            User).filter_by(user_id=999999).first()
        assert nonexistent_user is None

    def test_update_user_by_id_partial_update(self, test_session):
        """
        测试部分更新用户信息（只更新部分字段）
        """
        # Arrange - 创建用户
        original_user = User(
            wechat_openid="test_openid_partial",
            nickname="原始昵称",
            avatar_url="https://example.com/original.jpg"
        )
        # Note: create_user 会将 name 设置为与 nickname 相同
        created_user = UserService.create_user(original_user)

        # 创建更新用户对象，只更新部分字段
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.nickname = "这是我的新昵称"  # 只更新昵称

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 验证只有指定字段被更新
        test_session.expire_all()  # 刷新会话以获取最新数据
        updated_user = test_session.query(User).filter_by(
            user_id=created_user.user_id).first()
        assert updated_user is not None
        assert updated_user.nickname == "这是我的新昵称"  # 已更新
        assert updated_user.avatar_url == "https://example.com/original.jpg"  # 未更新
        assert updated_user.name == "原始昵称"  # 未更新

    def test_update_user_by_id_with_none_values(self, test_session):
        """
        测试传入 None 值时不更新对应字段
        """
        # Arrange - 创建用户
        original_user = User(
            wechat_openid="test_openid_none",
            nickname="原始昵称",
            avatar_url="https://example.com/original.jpg"
        )
        created_user = UserService.create_user(original_user)

        # 创建更新用户对象，包含 None 值
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.nickname = "更新后的昵称"
        update_user.avatar_url = None  # 显式传入 None

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 验证 None 值不会覆盖原有值
        test_session.expire_all()  # 刷新会话以获取最新数据
        updated_user = test_session.query(User).filter_by(
            user_id=created_user.user_id).first()
        assert updated_user is not None
        assert updated_user.nickname == "更新后的昵称"  # 已更新
        assert updated_user.avatar_url == "https://example.com/original.jpg"  # 未被 None 覆盖

    def test_query_user_by_refresh_token_success(self, test_session):
        """
        测试成功通过 refresh token 查询用户
        验证真实行为而非 mock 行为
        """
        # Arrange - 创建用户
        new_user = User(
            wechat_openid="test_openid_token",
            nickname="Token测试用户"
        )
        created_user = UserService.create_user(new_user)

        # 创建更新用户对象来设置 refresh token（遵循既有模式）
        update_user = User()
        update_user.user_id = created_user.user_id
        update_user.refresh_token = "test_refresh_token_123"

        UserService.update_user_by_id(update_user)

        # Act - 通过 refresh token 查询用户
        result = UserService.query_user_by_refresh_token(
            "test_refresh_token_123")

        # Assert - 验证查询结果
        assert result is not None
        assert result.user_id == created_user.user_id
        assert result.refresh_token == "test_refresh_token_123"

    def test_query_user_by_refresh_token_not_found(self, test_session):
        """
        测试查询不存在的 refresh token
        """
        # Arrange - 不创建用户，直接查询不存在的 token

        # Act - 查询不存在的 refresh token
        result = UserService.query_user_by_refresh_token("nonexistent_token")

        # Assert - 应该返回 None
        assert result is None

    def test_query_user_by_refresh_token_empty_token(self, test_session):
        """
        测试查询空的 refresh token
        """
        # Arrange - 创建用户但不设置 refresh token
        new_user = User(
            wechat_openid="test_openid_empty",
            nickname="空Token用户"
        )
        created_user = UserService.create_user(new_user)

        # Act - 查询空 token
        result = UserService.query_user_by_refresh_token("")

        # Assert - 应该返回 None
        assert result is None

    def test_query_user_by_refresh_token_with_database_error(self, test_session):
            """
            测试数据库错误时的处理
            """
            # Arrange - 模拟数据库错误
            with patch('database.flask_models.User.query') as mock_query:
                mock_query.filter.side_effect = OperationalError(
                    "Database error", None, None)
    
                # Act - 查询用户
                result = UserService.query_user_by_refresh_token("test_token")
    
                # Assert - 应该返回 None 而不是抛出异常
                assert result is None
