"""
手机认证功能单元测试
"""

import pytest
import os
import time
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta

from wxcloudrun.services.phone_auth_service import PhoneAuthService
from wxcloudrun.services.sms_service import SMSService, SimulationSMSProvider
from wxcloudrun.utils.phone_encryption import (
    PhoneEncryption, PhoneValidator, 
    validate_and_normalize_phone,
    encrypt_phone_number,
    decrypt_phone_number
)
from wxcloudrun.model import User, PhoneAuth
from wxcloudrun import db


class TestPhoneEncryption:
    """手机号码加密测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 设置测试密钥
        self.test_key = "test_encryption_key_12345"
        self.encryption = PhoneEncryption(self.test_key)
    
    def test_encrypt_decrypt_phone(self):
        """测试手机号码加密和解密"""
        original_phone = "+8613800138000"
        
        # 加密
        encrypted = self.encryption.encrypt_phone(original_phone)
        assert encrypted != original_phone
        assert isinstance(encrypted, str)
        
        # 解密
        decrypted = self.encryption.decrypt_phone(encrypted)
        assert decrypted == original_phone
    
    def test_phone_hash(self):
        """测试手机号码哈希"""
        phone = "+8613800138000"
        hash1 = self.encryption.encrypt_phone_hash(phone)
        hash2 = self.encryption.encrypt_phone_hash(phone)
        
        assert hash1 == hash2  # 相同手机号应该产生相同哈希
        assert len(hash1) == 64  # SHA256哈希长度
    
    def test_mask_phone(self):
        """测试手机号码脱敏"""
        phone = "13800138000"
        masked = self.encryption.mask_phone(phone)
        
        assert masked.startswith("*")  # 应该以星号开头
        assert masked.endswith("8000")  # 应该显示后4位
        assert len(masked) == len(phone)  # 长度应该保持不变
    
    def test_invalid_key(self):
        """测试无效密钥"""
        with pytest.raises(ValueError):
            PhoneEncryption(None)
        
        with pytest.raises(ValueError):
            PhoneEncryption("")
    
    def test_decrypt_invalid_data(self):
        """测试解密无效数据"""
        with pytest.raises(ValueError):
            self.encryption.decrypt_phone("invalid_encrypted_data")


class TestPhoneValidator:
    """手机号码验证测试"""
    
    def test_valid_phone_numbers(self):
        """测试有效手机号码"""
        valid_phones = [
            "13800138000",
            "15012345678",
            "+8613800138000",
            " 13800138000 ",  # 带空格
        ]
        
        for phone in valid_phones:
            is_valid, error_msg = PhoneValidator.validate_phone_number(phone)
            assert is_valid, f"Phone {phone} should be valid"
            assert error_msg == ""
    
    def test_invalid_phone_numbers(self):
        """测试无效手机号码"""
        invalid_phones = [
            "",  # 空号码
            "1234567890",  # 10位
            "123456789012",  # 12位
            "23800138000",  # 不以1开头
            "12800138000",  # 无效号段
            "abc12345678",  # 包含字母
        ]
        
        for phone in invalid_phones:
            is_valid, error_msg = PhoneValidator.validate_phone_number(phone)
            assert not is_valid, f"Phone {phone} should be invalid"
            assert error_msg != ""
    
    def test_normalize_phone_number(self):
        """测试手机号码标准化"""
        test_cases = [
            ("13800138000", "+8613800138000"),
            ("+8613800138000", "+8613800138000"),
            (" 138 0013 8000 ", "+8613800138000"),
        ]
        
        for input_phone, expected in test_cases:
            result = PhoneValidator.normalize_phone_number(input_phone)
            assert result == expected


class TestSMSService:
    """SMS服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        # 使用fakeredis进行测试
        import fakeredis
        redis_client = fakeredis.FakeRedis(decode_responses=True)
        self.sms_service = SMSService(redis_client)
    
    def test_generate_verification_code(self):
        """测试生成验证码"""
        code = self.sms_service.generate_verification_code()
        assert len(code) == 6
        assert code.isdigit()
    
    def test_send_verification_code_simulation(self):
        """测试模拟模式发送验证码"""
        phone = "+8613800138000"
        success, message, code = self.sms_service.send_verification_code(phone)
        
        assert success
        assert message == "验证码发送成功"
        assert code is not None  # 模拟模式应该返回验证码
        assert len(code) == 6
    
    def test_verify_code_success(self):
        """测试验证码验证成功"""
        phone = "+8613800138000"
        
        # 先发送验证码
        success, _, code = self.sms_service.send_verification_code(phone)
        assert success
        
        # 验证正确的验证码
        success, message = self.sms_service.verify_code(phone, code)
        assert success
        assert message == "验证码验证成功"
    
    def test_verify_code_failure(self):
        """测试验证码验证失败"""
        phone = "+8613800138000"
        
        # 先发送验证码
        success, _, code = self.sms_service.send_verification_code(phone)
        assert success
        
        # 验证错误的验证码
        success, message = self.sms_service.verify_code(phone, "000000")
        assert not success
        assert "验证码错误" in message
    
    def test_verify_code_expired(self):
        """测试验证码过期"""
        phone = "+8613800138000"
        
        # 发送验证码
        success, _, code = self.sms_service.send_verification_code(phone)
        assert success
        
        # 手动删除验证码（模拟过期）
        self.sms_service.delete_verification_code(phone)
        
        # 验证已删除的验证码
        success, message = self.sms_service.verify_code(phone, code)
        assert not success
        assert "已过期" in message or "不存在" in message


class TestPhoneAuthService:
    """手机认证服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.service = PhoneAuthService()
        
        # 设置测试环境变量
        os.environ['PHONE_ENCRYPTION_KEY'] = 'test_key_12345'
        os.environ['SMS_PROVIDER'] = 'simulation'
    
    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    def test_send_verification_code_success(self, mock_query_user):
        """测试发送验证码成功"""
        mock_query_user.return_value = None  # 用户不存在
        
        phone = "13800138000"
        success, message, code = self.service.send_verification_code(phone)
        
        assert success
        assert "发送成功" in message
        assert code is not None
    
    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    def test_send_verification_code_user_exists(self, mock_query_user):
        """测试发送验证码 - 用户已存在"""
        mock_user = MagicMock()
        mock_query_user.return_value = mock_user  # 用户已存在
        
        phone = "13800138000"
        success, message, code = self.service.send_verification_code(phone)
        
        assert not success
        assert "已注册" in message
        assert code is None
    
    def test_send_verification_code_invalid_phone(self):
        """测试发送验证码 - 无效手机号"""
        phone = "1234567890"  # 无效手机号
        
        success, message, code = self.service.send_verification_code(phone)
        
        assert not success
        assert message != ""
        assert code is None
    
    @patch('wxcloudrun.services.phone_auth_service.PhoneAuthService._create_phone_user')
    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    def test_verify_code_and_register_success(self, mock_query_user, mock_create_user):
        """测试验证码并注册成功"""
        mock_query_user.return_value = None  # 用户不存在
        
        # 模拟创建用户
        mock_user = MagicMock()
        mock_user.user_id = 1
        mock_user.nickname = "测试用户"
        mock_user.auth_type = "phone"
        mock_create_user.return_value = mock_user
        
        phone = "13800138000"
        code = "123456"  # 模拟验证码
        
        # 先发送验证码
        self.service.send_verification_code(phone)
        
        # 验证并注册
        success, message, user_info = self.service.verify_code_and_register(
            phone, code, "测试用户"
        )
        
        assert success
        assert "注册成功" in message
        assert user_info is not None
        assert 'tokens' in user_info
    
    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    def test_verify_code_and_register_user_exists(self, mock_query_user):
        """测试验证码并注册 - 用户已存在"""
        mock_user = MagicMock()
        mock_query_user.return_value = mock_user  # 用户已存在
        
        phone = "13800138000"
        code = "123456"
        
        success, message, user_info = self.service.verify_code_and_register(phone, code)
        
        assert not success
        assert "已注册" in message
        assert user_info is None
    
    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    def test_verify_code_and_register_invalid_code(self, mock_query_user):
        """测试验证码并注册 - 验证码错误"""
        mock_query_user.return_value = None  # 用户不存在
        
        phone = "13800138000"
        wrong_code = "000000"
        
        success, message, user_info = self.service.verify_code_and_register(phone, wrong_code)
        
        assert not success
        assert message != ""
        assert user_info is None


class TestPhoneAuthModel:
    """PhoneAuth模型测试"""
    
    def test_phone_auth_creation(self, client):
        """测试PhoneAuth模型创建"""
        from wxcloudrun import app
        with app.app_context():
            phone_auth = PhoneAuth(
                user_id=1,
                phone_number="encrypted_phone",
                auth_methods="sms",
                is_verified=True
            )
            
            assert phone_auth.user_id == 1
            assert phone_auth.auth_methods == "sms"
            assert phone_auth.is_verified is True
            assert phone_auth.is_active is True  # 默认值应该是True
        assert phone_auth.failed_attempts == 0  # 默认值应该是0
    
    def test_phone_auth_lock_account(self, client):
        """测试账户锁定"""
        from wxcloudrun import app
        with app.app_context():
            phone_auth = PhoneAuth(
                user_id=1,
                phone_number="encrypted_phone",
                auth_methods="sms"
            )
            
            # 锁定账户1小时
            phone_auth.lock_account(1)
            
            assert phone_auth.is_locked is True
            assert phone_auth.failed_attempts == 0
            assert phone_auth.locked_until is not None
    
    def test_phone_auth_increment_failed_attempts(self, client):
        """测试增加失败次数"""
        from wxcloudrun import app
        with app.app_context():
            phone_auth = PhoneAuth(
                user_id=1,
                phone_number="encrypted_phone",
                auth_methods="sms"
            )
            
            # 增加4次失败
            for _ in range(4):
                phone_auth.increment_failed_attempts()
            
            assert phone_auth.failed_attempts == 4
            assert phone_auth.is_locked is False
            
            # 第5次失败应该锁定账户
            phone_auth.increment_failed_attempts()
            assert phone_auth.failed_attempts == 0  # 重置为0
            assert phone_auth.is_locked is True
    
    def test_phone_auth_to_dict(self, client):
        """测试转换为字典"""
        from wxcloudrun import app
        with app.app_context():
            phone_auth = PhoneAuth(
                user_id=1,
                phone_number="encrypted_phone",
                auth_methods="both",
                is_verified=True
            )
            
            data = phone_auth.to_dict()
            
            assert 'phone_auth_id' in data
            assert 'user_id' in data
            assert 'auth_methods' in data
            assert 'is_verified' in data
            assert 'phone_number' not in data  # 默认不包含敏感信息
            
            # 包含敏感信息
            sensitive_data = phone_auth.to_dict(include_sensitive=True)
            assert 'phone_number' in sensitive_data


class TestPhoneAuthIntegration:
    """手机认证集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        os.environ['PHONE_ENCRYPTION_KEY'] = 'test_integration_key_12345'
        os.environ['SMS_PROVIDER'] = 'simulation'
    
    def test_complete_registration_flow(self):
        """测试完整注册流程"""
        service = PhoneAuthService()
        
        phone = "13800138000"
        nickname = "集成测试用户"
        
        # 1. 发送验证码
        success, message, code = service.send_verification_code(phone)
        assert success
        assert code is not None
        
        # 2. 验证码并注册
        success, message, user_info = service.verify_code_and_register(
            phone, code, nickname
        )
        assert success
        assert user_info is not None
        assert 'tokens' in user_info
        assert user_info['nickname'] == nickname
    
    def test_phone_encryption_integration(self):
        """测试手机加密集成"""
        phone = "13800138000"
        
        # 加密
        encrypted = encrypt_phone_number(phone)
        assert encrypted != phone
        
        # 解密
        decrypted = decrypt_phone_number(encrypted)
        assert decrypted == phone
        
        # 验证和标准化
        is_valid, error_msg, normalized = validate_and_normalize_phone(phone)
        assert is_valid
        assert normalized == "+8613800138000"


if __name__ == '__main__':
    pytest.main([__file__])