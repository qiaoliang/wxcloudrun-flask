#!/usr/bin/env python3
"""
Test script to manually run the failing test
"""

import os
import sys
import importlib
from unittest.mock import patch, MagicMock

# Set test environment
os.environ['ENV_TYPE'] = 'unit'
os.environ['SMS_PROVIDER'] = 'simulation'
os.environ['PHONE_ENCRYPTION_KEY'] = 'test_key_12345'

# Reload config
import config
importlib.reload(config)

# Import after setting environment
from wxcloudrun.services.phone_auth_service import PhoneAuthService
from wxcloudrun.services.sms_service import SMSService, SimulationSMSProvider
from tests.base_test import BaseTest

class TestPhoneAuth(BaseTest):
    def setup_method(self):
        # Reset SMS service
        import wxcloudrun.services.sms_service as sms_module
        sms_module._sms_service = None
        self.service = PhoneAuthService()

    @patch('wxcloudrun.services.phone_auth_service.query_user_by_phone')
    @patch('wxcloudrun.services.phone_auth_service.PhoneAuthService._create_phone_user')
    def test_verify_code_and_register_success(self, mock_create_user, mock_query_user):
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
        success, message, sent_code = self.service.send_verification_code(phone)
        print(f"Send verification code - Success: {success}, Message: {message}, Code: {sent_code}")
        
        if not success:
            print(f"Failed to send verification code: {message}")
            return False
        
        # 使用实际发送的验证码
        actual_code = sent_code
        
        # 验证并注册
        success, message, user_info = self.service.verify_code_and_register(
            phone, actual_code, "测试用户"
        )
        
        print(f"Verify and register - Success: {success}, Message: {message}, User info: {user_info}")
        
        assert success, f"Expected success but got: {success}, message: {message}"
        assert "注册成功" in message, f"Expected '注册成功' in message but got: {message}"
        assert user_info is not None, "Expected user_info but got None"
        assert 'tokens' in user_info, f"Expected 'tokens' in user_info but got: {user_info}"
        
        return True

# Run the test
test_instance = TestPhoneAuth()
test_instance.setup_method()
result = test_instance.test_verify_code_and_register_success()
print(f"\nTest result: {'PASSED' if result else 'FAILED'}")
sys.exit(0 if result else 1)