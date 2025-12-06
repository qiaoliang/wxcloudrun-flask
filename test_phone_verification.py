#!/usr/bin/env python3
"""
测试手机号注册和登录验证码功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"

def test_phone_registration():
    """测试手机号注册流程"""
    print("=== 测试手机号注册流程 ===")
    
    # 使用不同的手机号进行测试
    phone_register = "13800138003"
    phone_login = "13800138004"
    
    # 1. 注册新用户
    print("\n1. 注册新用户...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone_register,
        "purpose": "register"
    })
    print(f"发送注册验证码响应: {response.status_code} - {response.text}")
    
    # 添加延迟避免频率限制
    time.sleep(2)
    
    response = requests.post(f"{BASE_URL}/api/auth/register_phone", json={
        "phone": phone_register,
        "code": "123456",  # 测试环境固定验证码
        "password": "Test123456"
    })
    print(f"注册响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("注册成功!")
    else:
        print("注册失败")
        return
    
    # 2. 测试使用register类型的验证码登录（修复前会失败）
    print("\n2. 测试使用register类型的验证码登录...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone_register,
        "purpose": "register"  # 注意：这里使用register类型
    })
    print(f"发送register类型验证码响应: {response.status_code} - {response.text}")
    
    # 添加延迟避免频率限制
    time.sleep(2)
    
    response = requests.post(f"{BASE_URL}/api/auth/login_phone", json={
        "phone": phone_register,
        "code": "123456",
        "password": "Test123456"
    })
    print(f"使用register类型验证码登录响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("✅ 使用register类型验证码登录成功! 修复有效!")
    else:
        print("❌ 使用register类型验证码登录失败")
    
    # 3. 测试使用login类型的验证码登录（原本就应该能工作）
    print("\n3. 测试使用login类型的验证码登录...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone_register,
        "purpose": "login"  # 使用login类型
    })
    print(f"发送login类型验证码响应: {response.status_code} - {response.text}")
    
    # 添加延迟避免频率限制
    time.sleep(2)
    
    response = requests.post(f"{BASE_URL}/api/auth/login_phone", json={
        "phone": phone_register,
        "code": "123456",
        "password": "Test123456"
    })
    print(f"使用login类型验证码登录响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("✅ 使用login类型验证码登录成功!")
    else:
        print("❌ 使用login类型验证码登录失败")
    
    # 4. 测试login_phone_code接口也支持两种验证码
    print("\n4. 测试login_phone_code接口支持两种验证码...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone_register,
        "purpose": "register"  # 测试register类型的验证码
    })
    
    # 添加延迟避免频率限制
    time.sleep(2)
    
    response = requests.post(f"{BASE_URL}/api/auth/login_phone_code", json={
        "phone": phone_register,
        "code": "123456"
    })
    print(f"login_phone_code使用register验证码响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("✅ login_phone_code接口支持register类型验证码!")
    else:
        print("❌ login_phone_code接口不支持register类型验证码")

if __name__ == "__main__":
    test_phone_registration()