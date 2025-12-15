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

from .testutil import uuid_str,TEST_DEFAULT_PWD,TEST_DEFAULT_WXCAHT_CODE,TEST_DEFAULT_SMS_CODE,create_phone_user,create_wx_user
# 导入DAO模块和Flask app
from wxcloudrun import dao, app

class TestUserAPI:
    """用户搜索API测试类"""

    def test_create_wechat_user(self,test_server,auto_headers=None):
        wechat_code = f"wx_auth_new_user_{uuid_str(5)}"
        nickname =f"wx_auth_new_nickname_{uuid_str(5)}"
        avatar_url=f"{test_server}/avatar/{uuid_str(20)}"
        result = create_wx_user(test_server, wechat_code,nickname,avatar_url)
        assert result is not None
        assert result['nickname'] == nickname
        assert result['name'] == nickname
        assert result['avatar_url'] == avatar_url

    def test_create_phone_user(self,test_server,auto_headers=None):
        phone_number = f"139{uuid_str(8)}"
        nickname =f"phone_user_nickname_{uuid_str(5)}"

        pwd=f"{test_server}/avatar/{uuid_str(20)}"
        result = create_phone_user(test_server, phone_number, nickname, pwd)
        assert result is not None
        assert result['user']['user_id'] is not None
        assert result['user']['phone_number'] == f"139****{phone_number[-4:]}"
        assert result['user']['name'] == nickname


    def test_search_users_success(self, test_server, auth_headers):
        """
        测试用户搜索成功
        应该返回匹配的用户列表

        注意：/api/users/search 要求 super_admin 权限搜索所有用户，
        或者使用 scope='community' 在社区内搜索
        """
        url_env = test_server
        # 创建测试用户
        expected_user_nickname= "t张三"
        a_user=create_wx_user(url_env, "wx-code-13812345678", expected_user_nickname)

        # 使用创建用户返回的token进行搜索
        user_token = a_user["data"]["token"]
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

    def test_search_users_by_phone_number(self, test_server):
        """
        测试通过手机号搜索用户
        验证API能够正确根据手机号找到对应的用户
        """
        url_env = test_server

        # 1. 创建测试用户 - 使用特定的手机号
        test_phone = "13812345678"
        test_nickname = "手机测试用户"

        # 创建用户并绑定手机号
        user_response = self.create_wechat_user(
            url_env=url_env,
            wechat_code="wx-code-phone-test",
            nickname=test_nickname
        )

        user_token = user_response["data"]["token"]
        user_id = user_response["data"]["user_id"]

        # 绑定手机号
        bind_phone_data = {
            "phone": test_phone,
            "code": "666888"  # 测试环境使用有效验证码（避免使用123456等无效验证码）
        }

        bind_response = requests.post(
            f"{url_env}/api/user/bind_phone",
            json=bind_phone_data,
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=5
        )

        # 验证手机号绑定成功
        assert bind_response.status_code == 200
        bind_result = bind_response.json()
        assert bind_result["code"] == 1

        # 2. 获取超级管理员token（用于搜索所有用户）
        admin_login_response = requests.post(
            f"{url_env}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=5
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
            timeout=5
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

        # 测试3: 社区范围内的手机号搜索
        # 创建测试社区
        community_response = requests.post(
            f"{url_env}/api/communities",
            json={
                "name": "手机搜索测试社区",
                "description": "用于测试手机号搜索的社区",
                "location": "北京市"
            },
            headers=admin_headers,
            timeout=5
        )
        community_id = community_response.json()["data"]["community_id"]

        # 用户申请加入社区
        application_response = requests.post(
            f"{url_env}/api/community/applications",
            json={
                "community_id": community_id,
                "reason": "用于测试手机号搜索"
            },
            headers={"Authorization": f"Bearer {user_token}"},
            timeout=5
        )
        assert application_response.json()["code"] == 1

        # 管理员批准申请
        applications_response = requests.get(
            f"{url_env}/api/community/applications",
            headers=admin_headers,
            timeout=5
        )
        applications = applications_response.json()["data"]
        for app in applications:
            if app["user"]["user_id"] == user_id:
                approve_response = requests.put(
                    f"{url_env}/api/community/applications/{app['application_id']}/approve",
                    headers=admin_headers,
                    timeout=5
                )
                assert approve_response.json()["code"] == 1
                break

        # 在社区范围内搜索
        params = {
            "keyword": test_phone,
            "scope": "community",
            "community_id": community_id
        }
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

        # 应该在社区中找到用户
        found_user = None
        for user in users:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None
        print(f"✅ 社区范围内手机号搜索测试通过：在社区 {community_id} 中找到用户")

        # 测试4: 搜索不存在的手机号
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

        # 空关键词应该返回空列表
        assert len(users) == 0
        print("✅ 空关键词搜索测试通过：返回空列表")

        # 测试6: 权限控制 - 普通用户不能通过手机号搜索所有用户
        normal_user_response = self.create_wechat_user(
            url_env=url_env,
            wechat_code="wx-code-normal-user",
            nickname="普通用户"
        )
        normal_token = normal_user_response["data"]["token"]
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
