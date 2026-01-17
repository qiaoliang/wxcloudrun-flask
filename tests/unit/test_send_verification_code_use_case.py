"""
SendVerificationCodeUseCase 单元测试
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import select
from app.application.use_cases.sms.send_verification_code_use_case import SendVerificationCodeUseCase
from app.application.use_cases.base import UseCaseStatus
from database.flask_models import db, VerificationCode
from wxcloudrun.utils.validators import _hash_code


class TestSendVerificationCodeUseCase:
    """SendVerificationCodeUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return SendVerificationCodeUseCase()

    @pytest.fixture
    def mock_phone(self):
        """测试手机号"""
        return "13800138000"

    @pytest.fixture
    def mock_purpose(self):
        """测试用途"""
        return "register"

    def test_validate_success(self, use_case, mock_phone, mock_purpose):
        """
        测试验证成功
        Given: 有效的手机号和用途
        When: 调用 _validate 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=True):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch.object(db.session, 'execute', return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))):
                    # Act
                    result = use_case._validate(mock_phone, mock_purpose)

                    # Assert
                    assert result.status == UseCaseStatus.SUCCESS
                    assert result.message == "验证通过"

    def test_validate_rate_limit_exceeded(self, use_case, mock_phone, mock_purpose):
        """
        测试验证失败 - 请求过于频繁
        Given: 手机号在60秒内已发送过验证码
        When: 调用 _validate 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        now = datetime.now()
        mock_vc = Mock()
        mock_vc.last_sent_at = now - timedelta(seconds=30)  # 30秒前发送过

        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=True):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch.object(db.session, 'execute', return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=mock_vc))):
                    # Act
                    result = use_case._validate(mock_phone, mock_purpose)

                    # Assert
                    assert result.status == UseCaseStatus.VALIDATION_ERROR
                    assert "请求过于频繁" in result.message

    def test_execute_success_mock_env(self, use_case, mock_phone, mock_purpose):
        """
        测试执行成功 - Mock 环境
        Given: Mock 环境，手机号未发送过验证码
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，包含验证码
        """
        # Arrange
        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=False):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch('app.application.use_cases.sms.send_verification_code_use_case.generate_code', return_value='123456'):
                    with patch('app.application.use_cases.sms.send_verification_code_use_case.secrets.token_hex', return_value='test_salt'):
                        with patch('app.application.use_cases.sms.send_verification_code_use_case._hash_code', return_value='test_hash'):
                            with patch('app.application.use_cases.sms.send_verification_code_use_case.transaction'):
                                with patch.object(db.session, 'execute', return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))):
                                    # Act
                                    result = use_case.execute(mock_phone, mock_purpose)

                                    # Assert
                                    assert result.status == UseCaseStatus.SUCCESS
                                    assert "验证码发送成功" in result.message
                                    assert result.data['code'] == '123456'

    def test_execute_success_production_env(self, use_case, mock_phone, mock_purpose):
        """
        测试执行成功 - 生产环境
        Given: 生产环境，短信发送成功
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        mock_provider = Mock()
        mock_provider.send_verification_code.return_value = True

        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=True):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch('app.application.use_cases.sms.send_verification_code_use_case.generate_code', return_value='123456'):
                    with patch('app.application.use_cases.sms.send_verification_code_use_case.secrets.token_hex', return_value='test_salt'):
                        with patch('app.application.use_cases.sms.send_verification_code_use_case._hash_code', return_value='test_hash'):
                            with patch('app.application.use_cases.sms.send_verification_code_use_case.create_sms_provider', return_value=mock_provider):
                                with patch('app.application.use_cases.sms.send_verification_code_use_case.transaction'):
                                    with patch.object(db.session, 'execute', return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))):
                                        # Act
                                        result = use_case.execute(mock_phone, mock_purpose)

                                        # Assert
                                        assert result.status == UseCaseStatus.SUCCESS
                                        assert "验证码发送成功" in result.message
                                        assert 'code' not in result.data  # 生产环境不返回验证码

    def test_execute_failure_production_env(self, use_case, mock_phone, mock_purpose):
        """
        测试执行失败 - 生产环境短信发送失败
        Given: 生产环境，短信发送失败
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态
        """
        # Arrange
        mock_provider = Mock()
        mock_provider.send_verification_code.return_value = False

        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=True):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch('app.application.use_cases.sms.send_verification_code_use_case.generate_code', return_value='123456'):
                    with patch('app.application.use_cases.sms.send_verification_code_use_case.secrets.token_hex', return_value='test_salt'):
                        with patch('app.application.use_cases.sms.send_verification_code_use_case._hash_code', return_value='test_hash'):
                            with patch('app.application.use_cases.sms.send_verification_code_use_case.create_sms_provider', return_value=mock_provider):
                                with patch('app.application.use_cases.sms.send_verification_code_use_case.transaction'):
                                    with patch.object(db.session, 'execute', return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))):
                                        # Act
                                        result = use_case.execute(mock_phone, mock_purpose)

                                        # Assert
                                        assert result.status == UseCaseStatus.FAILURE
                                        assert "验证码发送失败" in result.message

    def test_execute_update_existing_record(self, use_case, mock_phone, mock_purpose, test_session):
        """
        测试执行成功 - 更新已有记录
        Given: 手机号已有验证码记录
        When: 调用 execute 方法
        Then: 更新已有记录，返回 SUCCESS 状态
        """
        # Arrange
        now = datetime.now()
        # 创建一个真正的 VerificationCode 对象
        existing_vc = VerificationCode(
            phone_number=mock_phone,
            purpose=mock_purpose,
            code_hash='old_hash',
            salt='old_salt',
            expires_at=now + timedelta(minutes=10),
            last_sent_at=now - timedelta(seconds=120)  # 120秒前发送过，超过60秒限制
        )
        test_session.add(existing_vc)
        test_session.commit()

        with patch('app.application.use_cases.sms.send_verification_code_use_case.should_use_real_sms', return_value=False):
            with patch('app.application.use_cases.sms.send_verification_code_use_case.normalize_phone_number', return_value=mock_phone):
                with patch('app.application.use_cases.sms.send_verification_code_use_case.generate_code', return_value='123456'):
                    with patch('app.application.use_cases.sms.send_verification_code_use_case.secrets.token_hex', return_value='test_salt'):
                        with patch('app.application.use_cases.sms.send_verification_code_use_case._hash_code', return_value='test_hash'):
                            # Act
                            result = use_case.execute(mock_phone, mock_purpose)

                            # Assert
                            assert result.status == UseCaseStatus.SUCCESS
                            # 刷新对象以获取最新值
                            test_session.refresh(existing_vc)
                            assert existing_vc.code_hash == 'test_hash'
                            assert existing_vc.salt == 'test_salt'