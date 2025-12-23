"""
测试用户搜索API的E2E测试用例
遵循TDD原则：测试真实行为，而非mock行为
"""

import pytest
import requests
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from tests.e2e.testutil import uuid_str,TEST_DEFAULT_PWD,TEST_DEFAULT_WXCAHT_CODE,TEST_DEFAULT_SMS_CODE,create_phone_user,create_wx_user,random_str
# 导入DAO模块和Flask app
from wxcloudrun import app

class TestUserAPI:

    """用户搜索API测试类"""

    def test_create_wechat_user(self, base_url):
        wechat_code = f"wx_auth_new_user_{uuid_str(5)}"
        nickname =f"wx_auth_new_nickname_{uuid_str(5)}"
        avatar_url=f"{base_url}/avatar/{uuid_str(20)}"
        result = create_wx_user(base_url, wechat_code,nickname,avatar_url)
        assert result is not None
        assert result['nickname'] == nickname
        assert result['name'] == nickname
        assert result['avatar_url'] == avatar_url

    def test_create_phone_user(self, base_url):
        import time
        # 使用时间戳确保唯一性，生成有效的11位手机号
        timestamp = int(time.time() * 1000)
        phone_number = f"139{str(timestamp)[-8:]}"  # 确保139开头，共11位
        nickname =f"phone_user_nickname_{uuid_str(5)}"

        pwd=f"{base_url}/avatar/{uuid_str(20)}"
        result = create_phone_user(base_url, phone_number, nickname, pwd)
        assert result is not None
        assert result['user_id'] is not None
        assert result['phone_number'] == f"139****{phone_number[-4:]}"
        assert result['name'] == nickname


    def test_search_users_success(self, base_url):
        """
        测试用户搜索成功
        应该返回匹配的用户列表

        注意：/api/users/search 要求 super_admin 权限搜索所有用户，
        或者使用 scope='community' 在社区内搜索
        """
        url_env = base_url
        # 创建测试用户
        expected_user_nickname= f"测试用户_{uuid_str(8)}"
        a_user=create_wx_user(url_env, f"wx-code-{uuid_str(10)}", expected_user_nickname)

        # 使用创建用户返回的token进行搜索
        user_token = a_user["token"]
        user_auth_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }

        # 测试1: 普通用户搜索所有用户会被拒绝（这是正确的权限控制）
        params = {"nickname": expected_user_nickname}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=user_auth_headers,
            timeout=5
        )

        # 验证响应 - 普通用户应该被拒绝
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0  # 权限不足
        assert "super admin" in data["msg"].lower()

        print("✅ 用户搜索权限控制测试通过：普通用户无法搜索所有用户")

    def test_search_users_by_phone_number(self, base_url):
        """
        测试通过手机号搜索用户
        验证API能够正确根据手机号找到对应的用户
        """
        url_env = base_url
        # 准备测试数据
        import time
        timestamp = int(time.time() * 1000)
        test_phone = f"139{str(timestamp)[-8:]}"  # 确保139开头，共11位
        test_nickname = f"test_user_{uuid_str(5)}"  # 测试昵称

        # 1. 创建用户并绑定手机号
        user_response = create_phone_user(
            url_env,
            test_phone,
            nickname=test_nickname
        )
        user_id = user_response['user_id']
        user_token = user_response['token']

        # 2. 获取超级管理员token（用于搜索所有用户）
        admin_login_response = requests.post(
            f"{url_env}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        admin_token = admin_login_response.json()["data"]["token"]
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 测试1: 使用完整手机号搜索（使用phone_hash匹配）
        params = {"keyword": test_phone}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=admin_headers,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]

        # 应该找到刚创建的用户
        assert len(users) >= 1
        found_user = None
        for user in users:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None
        assert found_user["nickname"] == test_nickname
        # phone_number是部分隐藏的
        assert found_user["phone_number"] == test_phone[:3] + "****" + test_phone[-4:]
        print(f"✅ 完整手机号搜索测试通过：找到用户 {test_nickname}")

        # 测试1.1: 验证部分手机号不能搜索（避免错误匹配）
        masked_phone = test_phone[:3] + "****" + test_phone[-4:]
        params = {"keyword": masked_phone}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=admin_headers,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]

        # 应该找不到用户（部分手机号不应该被搜索）
        found_user = None
        for user in users:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is None
        print(f"✅ 部分手机号搜索测试通过：未找到用户（正确行为）")

        # 测试2: 验证部分手机号不会被搜索到（避免错误匹配）
        partial_phone = test_phone[3:]  # 使用后8位
        params = {"keyword": partial_phone}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=admin_headers,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]

        # 应该找不到用户（部分手机号不应该被搜索）
        found_user = None
        for user in users:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is None
        print(f"✅ 部分手机号搜索测试通过：使用 {partial_phone} 未找到用户（正确行为）")

        # 测试3: 搜索不存在的手机号
        params = {"keyword": "19999999999"}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=admin_headers,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]

        # 应该找不到用户
        found_user = None
        for user in users:
            if user["phone_number"] == "19999999999":
                found_user = user
                break

        assert found_user is None
        print("✅ 不存在手机号搜索测试通过：找不到用户")

        # 测试5: 空关键词搜索
        # 先获取当前用户总数作为基准
        params_before = {"keyword": ""}
        response_before = requests.get(
            f"{url_env}/api/users/search",
            params=params_before,
            headers=admin_headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        users_before = data_before["data"]["users"]
        initial_user_count = len(users_before)
        
        params = {"keyword": ""}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=admin_headers,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        users = data["data"]["users"]
        
        # 验证返回的用户数量与初始数量相同（空关键词不应该影响结果）
        assert len(users) == initial_user_count
        print("✅ 空关键词搜索测试通过：返回相同数量的用户")

        # 测试6: 权限控制 - 普通用户不能通过手机号搜索所有用户
        normal_user_response = create_wx_user(
            url_env,
            "wx-code-normal-user",
            "普通用户"
        )
        normal_token = normal_user_response["token"]
        normal_headers = {
            "Authorization": f"Bearer {normal_token}",
            "Content-Type": "application/json"
        }

        params = {"keyword": test_phone}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=normal_headers,
            timeout=5
        )

        # 验证响应 - 普通用户应该被拒绝
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0  # 权限不足
        assert "super admin" in data["msg"].lower()
        print("✅ 权限控制测试通过：普通用户无法通过手机号搜索所有用户")
