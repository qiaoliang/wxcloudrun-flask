#!/usr/bin/env python3
"""
Test script to verify the SMS service issue when ENV_TYPE is set after import
"""

import os
import sys
sys.path.insert(0, '/Users/qiaoliang/working/code/safeGuard/backend')

# Import first (simulates the test scenario)
from wxcloudrun.services.sms_service import get_sms_service

# Then set environment (this is what the test does)
os.environ['ENV_TYPE'] = 'unit'
os.environ['SMS_PROVIDER'] = 'simulation'
os.environ['PHONE_ENCRYPTION_KEY'] = 'test_key_12345'

def test_sms_service():
    """Test that SMS service uses fakeredis in unit environment"""
    # Reset the global SMS service to force re-initialization
    import wxcloudrun.services.sms_service as sms_module
    sms_module._sms_service = None
    
    service = get_sms_service()
    
    phone = "+8613800138000"
    success, message, code = service.send_verification_code(phone)
    
    print(f"Success: {success}")
    print(f"Message: {message}")
    print(f"Code: {code}")
    
    if success:
        # Try to verify the code
        verify_success, verify_message = service.verify_code(phone, code)
        print(f"Verify Success: {verify_success}")
        print(f"Verify Message: {verify_message}")
    
    return success

if __name__ == "__main__":
    success = test_sms_service()
    sys.exit(0 if success else 1)