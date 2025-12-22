"""
简化的手机号搜索测试 - 用于调试
"""

import pytest
import requests
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

class TestPhoneSearchDebug:
    """手机号搜索调试测试"""

    def test_phone_binding_simple(self, test_server):
        """简单的手机号绑定测试"""
        url_env = test_server
        
        # 1. 先登录超级管理员账号
        admin_login = requests.post(
            f"{url_env}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=5
        )
        assert admin_login.status_code == 200
        admin_data = admin_login.json()["data"]
        admin_token = admin_data["token"]
        admin_id = admin_data["user_id"]
        
        # 2. 创建另一个微信用户
        login_data = {
            "code": "wx-code-debug",
            "nickname": "调试用户",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        response = requests.post(
            f"{url_env}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )
        assert response.status_code == 200
        user_data = response.json()["data"]
        user_token = user_data["token"]
        user_id = user_data["user_id"]
        
        print(f"✅ 用户创建成功，ID: {user_id}")
        
        # 2. 尝试不同的验证码绑定手机号
        test_phone = "13888888888"
        
        # 测试不同的验证码
        test_codes = ["666888", "888666", "111111", "999999", "555555"]
        
        for code in test_codes:
            print(f"尝试使用验证码: {code}")
            
            bind_response = requests.post(
                f"{url_env}/api/user/bind_phone",
                json={
                    "phone": test_phone,
                    "code": code
                },
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=5
            )
            
            print(f"响应状态码: {bind_response.status_code}")
            print(f"响应内容: {bind_response.text}")
            
            if bind_response.status_code == 200:
                result = bind_response.json()
                if result.get("code") == 1:
                    print(f"✅ 手机号绑定成功，使用验证码: {code}")
                    
                    # 3. 使用超级管理员token搜索用户
                    # 使用部分手机号搜索（数据库中存储的是部分隐藏的手机号）
                    masked_phone = test_phone[:3] + "****" + test_phone[-4:]
                    print(f"使用部分手机号搜索: {masked_phone}")
                    search_response = requests.get(
                        f"{url_env}/api/users/search",
                        params={"keyword": masked_phone},
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=5
                    )
                    
                    # 4. 搜索用户
                    # 先获取用户详情，确认手机号已绑定
                    user_detail_response = requests.get(
                        f"{url_env}/api/user/info",
                        headers={"Authorization": f"Bearer {user_token}"},
                        timeout=5
                    )
                    print(f"用户详情: {user_detail_response.text}")
                    
                    search_response = requests.get(
                        f"{url_env}/api/users/search",
                        params={"keyword": test_phone},
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=5
                    )
                    
                    print(f"搜索响应: {search_response.text}")
                    
                    # 尝试使用昵称搜索
                    search_by_nick = requests.get(
                        f"{url_env}/api/users/search",
                        params={"keyword": "调试用户"},
                        headers={"Authorization": f"Bearer {admin_token}"},
                        timeout=5
                    )
                    print(f"昵称搜索响应: {search_by_nick.text}")
                    
                    # 手动计算phone_hash看看是否匹配
                    import hashlib
                    phone_secret = "default_secret"  # 默认的phone_secret
                    phone_hash = hashlib.sha256(
                        f"{phone_secret}:{test_phone}".encode('utf-8')).hexdigest()
                    print(f"手动计算的phone_hash: {phone_hash}")
                    
                    if search_response.status_code == 200:
                        search_result = search_response.json()
                        if search_result.get("code") == 1:
                            users = search_result["data"]["users"]
                            found = False
                            for user in users:
                                if user["user_id"] == user_id:
                                    found = True
                                    print(f"✅ 通过手机号找到用户: {user['nickname']}")
                                    break
                            
                            if not found:
                                print(f"❌ 未找到用户 ID {user_id}")
                        else:
                            print(f"❌ 搜索失败: {search_result}")
                    else:
                        print(f"❌ 搜索请求失败: {search_response.status_code}")
                    
                    return  # 成功后退出循环
                else:
                    print(f"❌ 绑定失败: {result}")
            else:
                print(f"❌ 请求失败: {bind_response.status_code}")
        
        print("❌ 所有验证码都失败了")