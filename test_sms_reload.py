#!/usr/bin/env python3
"""
Test script to verify if reloading config helps
"""

import os
import sys
import importlib
sys.path.insert(0, '/Users/qiaoliang/working/code/safeGuard/backend')

# Import first
import wxcloudrun.services.sms_service as sms_module
import config

print(f"Initial ENV_TYPE: {config.ENV_TYPE}")

# Set environment
os.environ['ENV_TYPE'] = 'unit'

# Reload config
importlib.reload(config)

print(f"After reload ENV_TYPE: {config.ENV_TYPE}")

# Reset SMS service
sms_module._sms_service = None

# Get service
service = sms_module.get_sms_service()

phone = "+8613800138000"
success, message, code = service.send_verification_code(phone)

print(f"Success: {success}")
print(f"Message: {message}")
print(f"Code: {code}")