"""
测试完整手机号hash搜索的准确性
验证部分手机号不会产生错误匹配
"""

import pytest
import sys
import os
import requests

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

class TestPhoneHashSearchAccuracy:
    """测试手机号hash搜索的准确性"""

    def test_no_false_match_with_partial_phone(self, test_server):
        """
        测试部分手机号不会产生错误匹配
        创建多个用户，它们的前3位和后4位相同，但中间4位不同
        """
        url_env = test_server
        
        # 1. 登录超级管理员
        admin_login = requests.post(
            f"{url_env}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=5
        )
        admin_token = admin_login.json()["data"]["token"]
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
        
        # 2. 创建多个用户，绑定相似的手机号
        # 这些手机号的前3位和后4位相同：138****5678
        phones = [
            "13812345678",
            "13898765678",
            "13811115678",
            "13822225678"
        ]
        
        user_ids = []
        for i, phone in enumerate(phones):
            # 创建用户
            login_data = {
                "code": f"wx-code-{i}",
                "nickname": f"用户{i+1}",
                "avatar_url": "https://example.com/avatar{i+1}.jpg"
            }
            
            response = requests.post(
                f"{url_env}/api/login",
                json=login_data,
                timeout=5
            )
            user_token = response.json()["data"]["token"]
            user_id = response.json()["data"]["user_id"]
            user_ids.append(user_id)
            
            # 绑定手机号
            bind_response = requests.post(
                f"{url_env}/api/user/bind_phone",
                json={
                    "phone": phone,
                    "code": "666888"
                },
                headers={"Authorization": f"Bearer {user_token}"},
                timeout=5
            )
            assert bind_response.json()["code"] == 1
            print(f"✅ 用户{i+1}绑定手机号成功: {phone}")
        
        # 3. 测试使用完整手机号搜索，应该精确匹配
        for i, phone in enumerate(phones):
            response = requests.get(
                f"{url_env}/api/users/search",
                params={"keyword": phone},
                headers=admin_headers,
                timeout=5
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["code"] == 1
            users = data["data"]["users"]
            
            # 应该只找到一个用户
            assert len(users) == 1
            assert users[0]["user_id"] == user_ids[i]
            assert users[0]["nickname"] == f"用户{i+1}"
            print(f"✅ 完整手机号 {phone} 精确匹配到用户{i+1}")
        
        # 4. 测试使用部分手机号（前3位+后4位）搜索，应该找不到任何用户
        partial_phone = "138****5678"
        response = requests.get(
            f"{url_env}/api/users/search",
            params={"keyword": partial_phone},
            headers=admin_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]
        
        # 应该找不到任何用户
        assert len(users) == 0
        print(f"✅ 部分手机号 {partial_phone} 未找到任何用户（正确行为）")
        
        # 5. 测试使用其他部分手机号搜索，也应该找不到
        other_partial = "1381234"  # 前7位
        response = requests.get(
            f"{url_env}/api/users/search",
            params={"keyword": other_partial},
            headers=admin_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]
        
        # 应该找不到任何用户
        assert len(users) == 0
        print(f"✅ 部分手机号 {other_partial} 未找到任何用户（正确行为）")
        
        # 6. 测试使用不存在的完整手机号
        nonexistent_phone = "13800000000"
        response = requests.get(
            f"{url_env}/api/users/search",
            params={"keyword": nonexistent_phone},
            headers=admin_headers,
            timeout=5
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]
        
        # 应该找不到任何用户
        assert len(users) == 0
        print(f"✅ 不存在的手机号 {nonexistent_phone} 未找到用户（正确行为）")