"""
认证模块 UseCases 单元测试

测试以下 UseCase：
1. LoginWeChatUseCase - 微信登录
2. RefreshTokenUseCase - 刷新 Token
3. LogoutUseCase - 登出

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from database.flask_models import User, Community
from app.application.use_cases.auth.login_wechat_use_case import LoginWeChatUseCase
from app.application.use_cases.auth.refresh_token_use_case import RefreshTokenUseCase
from app.application.use_cases.auth.logout_use_case import LogoutUseCase
from app.application.use_cases.base import UseCaseStatus


class TestLoginWeChatUseCase:
    """LoginWeChatUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return LoginWeChatUseCase()

    @pytest.fixture
    def mock_openid(self):
        """测试 openid"""
        return "test_openid_12345"

    @pytest.fixture
    def mock_code(self):
        """测试微信授权码"""
        return "test_wx_code_12345"

    @pytest.fixture
    def mock_nickname(self):
        """测试昵称"""
        return "测试用户"

    @pytest.fixture
    def mock_avatar(self):
        """测试头像"""
        return "https://example.com/avatar.jpg"

    def test_validate_success(self, use_case, mock_code):
        """
        测试验证成功
        Given: 有效的微信授权码
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        nickname = "测试用户"
        avatar = "https://example.com/avatar.jpg"

        # Act
        result = use_case._validate(mock_code, nickname, avatar)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == "验证通过"

    def test_validate_missing_code(self, use_case):
        """
        测试验证失败 - 缺少 code 参数
        Given: 缺少微信授权码
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        code = None

        # Act
        result = use_case._validate(code)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "缺少code参数" in result.message

    def test_validate_empty_code(self, use_case):
        """
        测试验证失败 - code 参数为空字符串
        Given: 微信授权码为空字符串
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        code = ""

        # Act
        result = use_case._validate(code)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "缺少code参数" in result.message

    def test_clean_user_info_valid(self, use_case, mock_nickname, mock_avatar):
        """
        测试清理用户信息 - 有效信息
        Given: 有效的昵称和头像（无前后空格）
        When: 调用 _clean_user_info 方法
        Then: 返回清理后的昵称和头像
        """
        # Arrange
        nickname = "  测试用户  "
        avatar = "https://example.com/avatar.jpg"  # 无前后空格

        # Act
        cleaned_nickname, cleaned_avatar = use_case._clean_user_info(nickname, avatar)

        # Assert
        assert cleaned_nickname == "测试用户"
        assert cleaned_avatar == "https://example.com/avatar.jpg"

    def test_clean_user_info_long_nickname(self, use_case):
        """
        测试清理用户信息 - 超长昵称
        Given: 超过50字符的昵称
        When: 调用 _clean_user_info 方法
        Then: 昵称被截断到50字符并添加"..."
        """
        # Arrange
        nickname = "a" * 100
        avatar = "https://example.com/avatar.jpg"

        # Act
        cleaned_nickname, cleaned_avatar = use_case._clean_user_info(nickname, avatar)

        # Assert
        assert len(cleaned_nickname) == 53  # 50 + "..."
        assert cleaned_nickname.endswith("...")
        assert cleaned_avatar == "https://example.com/avatar.jpg"

    def test_clean_user_info_empty_nickname(self, use_case):
        """
        测试清理用户信息 - 空昵称
        Given: 空昵称
        When: 调用 _clean_user_info 方法
        Then: 生成默认昵称
        """
        # Arrange
        nickname = ""
        avatar = "https://example.com/avatar.jpg"

        # Act
        cleaned_nickname, cleaned_avatar = use_case._clean_user_info(nickname, avatar)

        # Assert
        assert cleaned_nickname.startswith("微信用户_")
        assert cleaned_avatar == "https://example.com/avatar.jpg"

    def test_clean_user_info_invalid_avatar(self, use_case):
        """
        测试清理用户信息 - 无效头像
        Given: 无效的头像URL
        When: 调用 _clean_user_info 方法
        Then: 使用默认头像
        """
        # Arrange
        nickname = "测试用户"
        avatar = "invalid_url"

        # Act
        cleaned_nickname, cleaned_avatar = use_case._clean_user_info(nickname, avatar)

        # Assert
        assert cleaned_nickname == "测试用户"
        # 头像URL不为空即可，格式可以多样化
        assert cleaned_avatar is not None
        assert len(cleaned_avatar) > 0
        assert cleaned_avatar.startswith("http")

    def test_execute_success_new_user(self, use_case, mock_code, mock_nickname, mock_avatar):
        """
        测试执行成功 - 新用户登录
        Given: 微信API返回有效openid，用户不存在
        When: 调用 execute 方法
        Then: 创建新用户，返回 SUCCESS 状态和 token
        """
        # Arrange
        mock_wx_data = {
            'openid': 'test_openid_new',
            'session_key': 'test_session_key'
        }

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            with patch('app.application.use_cases.auth.login_wechat_use_case.generate_jwt_token', return_value=('test_token', None)):
                with patch('app.application.use_cases.auth.login_wechat_use_case.generate_refresh_token', return_value='test_refresh_token'):
                    # Act
                    result = use_case.execute(mock_code, mock_nickname, mock_avatar)

                    # Assert
                    assert result.status == UseCaseStatus.SUCCESS
                    assert "登录成功" in result.message
                    assert result.data['token'] == 'test_token'
                    assert result.data['refresh_token'] == 'test_refresh_token'
                    assert result.data['login_type'] == 'new_user'

    def test_execute_success_existing_user(self, use_case, mock_code, test_user):
        """
        测试执行成功 - 已有用户登录
        Given: 微信API返回有效openid，用户已存在
        When: 调用 execute 方法
        Then: 更新用户信息，返回 SUCCESS 状态和 token
        """
        # Arrange
        mock_wx_data = {
            'openid': test_user.wechat_openid,
            'session_key': 'test_session_key'
        }
        new_nickname = "更新后的昵称"

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            with patch('app.application.use_cases.auth.login_wechat_use_case.generate_jwt_token', return_value=('test_token', None)):
                with patch('app.application.use_cases.auth.login_wechat_use_case.generate_refresh_token', return_value='test_refresh_token'):
                    # Act
                    result = use_case.execute(mock_code, new_nickname, test_user.avatar_url)

                    # Assert
                    assert result.status == UseCaseStatus.SUCCESS
                    assert "登录成功" in result.message
                    assert result.data['token'] == 'test_token'
                    assert result.data['refresh_token'] == 'test_refresh_token'
                    assert result.data['login_type'] == 'existing_user'
                    assert result.data['user_id'] == test_user.user_id

    def test_execute_wx_api_error(self, use_case, mock_code):
        """
        测试执行失败 - 微信API返回错误
        Given: 微信API返回错误
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        mock_wx_data = {
            'errcode': 40029,
            'errmsg': 'invalid code'
        }

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            # Act
            result = use_case.execute(mock_code)

            # Assert
            assert result.status == UseCaseStatus.BUSINESS_ERROR
            assert "微信API错误" in result.message

    def test_execute_wx_api_missing_data(self, use_case, mock_code):
        """
        测试执行失败 - 微信API返回数据不完整
        Given: 微信API返回数据缺少 openid 或 session_key
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        mock_wx_data = {
            'openid': 'test_openid'
            # 缺少 session_key
        }

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            # Act
            result = use_case.execute(mock_code)

            # Assert
            assert result.status == UseCaseStatus.BUSINESS_ERROR
            assert "微信API返回数据不完整" in result.message

    def test_execute_token_generation_failure(self, use_case, mock_code):
        """
        测试执行失败 - 生成 token 失败
        Given: 微信API返回有效数据，但生成 token 失败
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        mock_wx_data = {
            'openid': 'test_openid',
            'session_key': 'test_session_key'
        }

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            with patch('app.application.use_cases.auth.login_wechat_use_case.generate_jwt_token', return_value=(None, {'error': 'token generation failed'})):
                # Act
                result = use_case.execute(mock_code)

                # Assert
                assert result.status == UseCaseStatus.FAILURE
                assert "生成token失败" in result.message

    def test_execute_performance(self, use_case, mock_code, mock_nickname, mock_avatar):
        """
        测试登录性能
        Given: 微信API返回有效数据
        When: 调用 execute 方法
        Then: 响应时间应该小于 500ms
        """
        # Arrange
        mock_wx_data = {
            'openid': 'test_openid_perf',
            'session_key': 'test_session_key'
        }

        with patch('app.application.use_cases.auth.login_wechat_use_case.get_user_info_by_code', return_value=mock_wx_data):
            with patch('app.application.use_cases.auth.login_wechat_use_case.generate_jwt_token', return_value=('test_token', None)):
                with patch('app.application.use_cases.auth.login_wechat_use_case.generate_refresh_token', return_value='test_refresh_token'):
                    # Act
                    import time
                    start_time = time.time()
                    result = use_case.execute(mock_code, mock_nickname, mock_avatar)
                    end_time = time.time()

                    # Assert
                    assert result.status == UseCaseStatus.SUCCESS
                    execution_time = (end_time - start_time) * 1000  # 转换为毫秒
                    assert execution_time < 500, f"登录响应时间 {execution_time}ms 超过 500ms 限制"


class TestRefreshTokenUseCase:
    """RefreshTokenUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return RefreshTokenUseCase()

    @pytest.fixture
    def mock_refresh_token(self):
        """测试 refresh token"""
        return "test_refresh_token_12345"

    def test_validate_success(self, use_case, mock_refresh_token):
        """
        测试验证成功
        Given: 有效的 refresh token
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        refresh_token = mock_refresh_token

        # Act
        result = use_case._validate(refresh_token)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == "验证通过"

    def test_validate_missing_refresh_token(self, use_case):
        """
        测试验证失败 - 缺少 refresh_token 参数
        Given: 缺少 refresh_token
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        refresh_token = None

        # Act
        result = use_case._validate(refresh_token)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "缺少refresh_token参数" in result.message

    def test_validate_empty_refresh_token(self, use_case):
        """
        测试验证失败 - refresh_token 参数为空字符串
        Given: refresh_token 为空字符串
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        refresh_token = ""

        # Act
        result = use_case._validate(refresh_token)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "缺少refresh_token参数" in result.message

    def test_execute_success(self, use_case, test_user, mock_refresh_token):
        """
        测试执行成功 - 刷新 token
        Given: 有效的 refresh token 和用户
        When: 调用 execute 方法
        Then: 生成新的 token，返回 SUCCESS 状态
        """
        # Arrange
        test_user.refresh_token = mock_refresh_token
        test_user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        use_case.user_repository.save(test_user)

        with patch('app.application.use_cases.auth.refresh_token_use_case.generate_jwt_token', return_value=('new_token', None)):
            with patch('app.application.use_cases.auth.refresh_token_use_case.generate_refresh_token', return_value='new_refresh_token'):
                # Act
                result = use_case.execute(mock_refresh_token)

                # Assert
                assert result.status == UseCaseStatus.SUCCESS
                assert "刷新成功" in result.message
                assert result.data['token'] == 'new_token'
                assert result.data['refresh_token'] == 'new_refresh_token'
                assert result.data['expires_in'] == 7200

    def test_execute_user_not_found(self, use_case, mock_refresh_token):
        """
        测试执行失败 - 用户不存在
        Given: refresh token 对应的用户不存在
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态
        """
        # Arrange
        invalid_token = "invalid_refresh_token"

        # Act
        result = use_case.execute(invalid_token)

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "无效的refresh_token" in result.message

    def test_execute_invalid_refresh_token(self, use_case, test_user):
        """
        测试执行失败 - 无效的 refresh token
        Given: 用户存在但 refresh token 不匹配
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态
        """
        # Arrange
        test_user.refresh_token = "correct_token"
        test_user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        use_case.user_repository.save(test_user)

        invalid_token = "wrong_token"

        # Act
        result = use_case.execute(invalid_token)

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "无效的refresh_token" in result.message

    def test_execute_expired_refresh_token(self, use_case, test_user, mock_refresh_token):
        """
        测试执行失败 - refresh token 已过期
        Given: refresh token 已过期
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态，清除过期的 token
        """
        # Arrange
        test_user.refresh_token = mock_refresh_token
        test_user.refresh_token_expire = datetime.datetime.now() - datetime.timedelta(days=1)
        use_case.user_repository.save(test_user)

        # Act
        result = use_case.execute(mock_refresh_token)

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "refresh_token已过期" in result.message

        # 验证过期的 token 已被清除（通过 openid 查找用户）
        updated_user = use_case.user_repository.find_by_openid(test_user.wechat_openid)
        assert updated_user.refresh_token is None
        assert updated_user.refresh_token_expire is None

    def test_execute_token_generation_failure(self, use_case, test_user, mock_refresh_token):
        """
        测试执行失败 - 生成新 token 失败
        Given: refresh token 有效，但生成新 token 失败
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        test_user.refresh_token = mock_refresh_token
        test_user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        use_case.user_repository.save(test_user)

        with patch('app.application.use_cases.auth.refresh_token_use_case.generate_jwt_token', return_value=(None, {'error': 'token generation failed'})):
            # Act
            result = use_case.execute(mock_refresh_token)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert "生成token失败" in result.message


class TestLogoutUseCase:
    """LogoutUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return LogoutUseCase()

    @pytest.fixture
    def mock_openid(self):
        """测试 openid"""
        return "test_openid_12345"

    def test_validate_success(self, use_case, mock_openid):
        """
        测试验证成功
        Given: 有效的 openid
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        openid = mock_openid

        # Act
        result = use_case._validate(openid)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == "验证通过"

    def test_validate_missing_openid(self, use_case):
        """
        测试验证失败 - 缺少 openid 参数
        Given: 缺少 openid
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        openid = None

        # Act
        result = use_case._validate(openid)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "token无效" in result.message

    def test_validate_empty_openid(self, use_case):
        """
        测试验证失败 - openid 参数为空字符串
        Given: openid 为空字符串
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        openid = ""

        # Act
        result = use_case._validate(openid)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "token无效" in result.message

    def test_execute_success(self, use_case, test_user):
        """
        测试执行成功 - 成功登出
        Given: 有效的用户
        When: 调用 execute 方法
        Then: 清除 refresh token，返回 SUCCESS 状态
        """
        # Arrange
        test_user.refresh_token = "test_refresh_token"
        test_user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        use_case.user_repository.save(test_user)

        # Act
        result = use_case.execute(test_user.wechat_openid)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "登出成功" in result.message

        # 验证 refresh token 已被清除
        updated_user = use_case.user_repository.find_by_openid(test_user.wechat_openid)
        assert updated_user.refresh_token is None
        assert updated_user.refresh_token_expire is None

    def test_execute_user_not_found(self, use_case, mock_openid):
        """
        测试执行成功 - 用户不存在
        Given: openid 对应的用户不存在
        When: 调用 execute 方法
        Then: 仍然返回 SUCCESS 状态（幂等操作）
        """
        # Arrange
        invalid_openid = "invalid_openid_12345"

        # Act
        result = use_case.execute(invalid_openid)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "登出成功" in result.message

    def test_execute_without_refresh_token(self, use_case, test_user):
        """
        测试执行成功 - 用户没有 refresh token
        Given: 用户存在但没有 refresh token
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        test_user.refresh_token = None
        test_user.refresh_token_expire = None
        use_case.user_repository.save(test_user)

        # Act
        result = use_case.execute(test_user.wechat_openid)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "登出成功" in result.message

    def test_execute_clears_all_token_data(self, use_case, test_user):
        """
        测试执行成功 - 清除所有 token 数据
        Given: 用户有完整的 token 数据
        When: 调用 execute 方法
        Then: 清除所有 token 相关数据
        """
        # Arrange
        test_user.refresh_token = "test_refresh_token"
        test_user.refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=7)
        use_case.user_repository.save(test_user)

        # Act
        result = use_case.execute(test_user.wechat_openid)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

        # 验证所有 token 数据已被清除
        updated_user = use_case.user_repository.find_by_openid(test_user.wechat_openid)
        assert updated_user.refresh_token is None
        assert updated_user.refresh_token_expire is None