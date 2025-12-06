#!/usr/bin/env python3
"""
简单测试验证码修复
"""
import requests
import time

BASE_URL = "http://localhost:8080"

def test_verification_code_fix():
    """测试验证码修复是否有效"""
    print("=== 测试验证码修复是否有效 ===")
    
    # 使用一个新手机号
    phone = "13800138005"
    
    # 1. 先注册用户（确保用户存在）
    print("\n1. 注册用户...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone,
        "purpose": "register"
    })
    print(f"发送注册验证码响应: {response.status_code}")
    
    # 等待频率限制
    time.sleep(65)
    
    response = requests.post(f"{BASE_URL}/api/auth/register_phone", json={
        "phone": phone,
        "code": "123456",
        "password": "Test123456"
    })
    print(f"注册响应: {response.status_code} - {response.text}")
    
    if response.status_code != 200 or response.json().get('code') != 1:
        print("注册失败，无法继续测试")
        return
    
    # 2. 发送register类型的验证码
    print("\n2. 发送register类型的验证码...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone,
        "purpose": "register"
    })
    print(f"发送register验证码响应: {response.status_code}")
    
    # 等待频率限制
    time.sleep(65)
    
    # 3. 使用register类型的验证码登录（测试修复）
    print("\n3. 使用register类型的验证码登录（测试修复）...")
    response = requests.post(f"{BASE_URL}/api/auth/login_phone", json={
        "phone": phone,
        "code": "123456",
        "password": "Test123456"
    })
    print(f"使用register验证码登录响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("✅ 修复有效！可以使用register类型的验证码登录")
    else:
        print("❌ 修复无效，无法使用register类型的验证码登录")
    
    # 4. 发送login类型的验证码
    print("\n4. 发送login类型的验证码...")
    response = requests.post(f"{BASE_URL}/api/sms/send_code", json={
        "phone": phone,
        "purpose": "login"
    })
    print(f"发送login验证码响应: {response.status_code}")
    
    # 等待频率限制
    time.sleep(65)
    
    # 5. 使用login类型的验证码登录（原本就应该能工作）
    print("\n5. 使用login类型的验证码登录...")
    response = requests.post(f"{BASE_URL}/api/auth/login_phone", json={
        "phone": phone,
        "code": "123456",
        "password": "Test123456"
    })
    print(f"使用login验证码登录响应: {response.status_code} - {response.text}")
    
    if response.status_code == 200 and response.json().get('code') == 1:
        print("✅ login类型的验证码登录正常")
    else:
        print("❌ login类型的验证码登录失败")

if __name__ == "__main__":
    test_verification_code_fix()