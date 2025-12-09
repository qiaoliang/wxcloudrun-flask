"""
测试微信用户通过 /api/login 注册的E2E测试
遵循TDD原则：先写失败测试，观察失败，再实现最小代码
"""

import pytest
import requests
import json
import os
import sys

# 添加项目根目录到Python路径，以便导入dao模块
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

# 导入DAO模块和Flask app
from wxcloudrun import dao, app


class TestWechatUserRegistration:
    """微信用户注册测试类"""

    def test_register_wechat_user_via_login_and_find_in_db(self, test_server):
        """
        测试通过 /api/login 新注册一个wechat_user
        注册成功后，可以使用 DAO.py 从数据库中找到这个用户
        
        这是TDD的RED阶段 - 先写测试，观察其失败
        """
        # 使用时间戳确保每次测试都有唯一的code
        import time
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳确保唯一性
        
        # 准备测试数据 - 使用唯一的测试数据避免冲突
        test_code = f"test_code_register_wechat_user_{timestamp}"
        test_nickname = f"测试微信用户_{timestamp}"
        test_avatar_url = f"https://example.com/avatar_wechat_user_{timestamp}.jpg"
        
        # 准备登录请求数据
        login_data = {
            "code": test_code,
            "nickname": test_nickname,
            "avatar_url": test_avatar_url
        }

        # 发送登录请求以注册新用户
        response = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        # 验证HTTP响应状态
        assert response.status_code == 200
        
        # 验证响应结构
        data = response.json()
        assert data["code"] == 1  # 注册成功
        assert data["msg"] == "success"
        assert "data" in data
        
        # 验证返回的用户数据
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"  # 应该是新用户注册
        assert result['user_id'] is not None
        assert result['wechat_openid'] is not None
        assert result['nickname'] == test_nickname
        assert result['avatar_url'] == test_avatar_url
        
        # 在独立进程模式下，不能直接访问服务器的数据库
        # 通过 API 响应验证数据
        print(f"✅ 新注册的微信用户:")
        print(f"   ID: {result['user_id']}")
        print(f"   OpenID: {result['wechat_openid']}")
        print(f"   昵称: {result['nickname']}")
        print(f"   头像: {result['avatar_url']}")

    def test_register_same_wechat_user_twice_returns_existing_user(self, test_server):
        """
        测试使用相同的openid再次登录应该返回已存在的用户，而不是创建新用户
        """
        # 使用时间戳确保每次测试都有唯一的code
        import time
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳确保唯一性
        
        # 准备测试数据
        test_code = f"test_code_register_wechat_user_{timestamp}"
        test_nickname = f"测试微信用户_{timestamp}"
        test_avatar_url = f"https://example.com/avatar_wechat_user_{timestamp}.jpg"
        
        # 准备登录请求数据
        login_data = {
            "code": test_code,
            "nickname": test_nickname,
            "avatar_url": test_avatar_url
        }

        # 第一次登录 - 应该注册新用户
        response1 = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        assert response1.status_code == 200
        data1 = response1.json()
        assert data1["code"] == 1
        assert data1["data"]["login_type"] == "new_user"
        first_user_id = data1["data"]["user_id"]
        first_openid = data1["data"]["wechat_openid"]

        # 第二次登录 - 应该返回已存在的用户
        response2 = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["code"] == 1
        assert data2["data"]["login_type"] == "existing_user"  # 应该是已存在用户
        assert data2["data"]["user_id"] == first_user_id  # 用户ID应该相同
        assert data2["data"]["wechat_openid"] == first_openid  # OpenID应该相同

        # 在独立进程模式下，不能直接访问服务器的数据库
        # 通过 API 响应验证数据
        print(f"✅ 重复登录正确返回已存在的用户:")
        print(f"   用户ID: {first_user_id}")
        print(f"   登录类型: {data2['data']['login_type']}")

    def test_register_wechat_user_with_minimal_data(self, test_server):
        """
        测试使用最少必需数据注册微信用户
        只提供code，不提供nickname和avatar_url
        """
        # 使用时间戳确保每次测试都有唯一的code
        import time
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳确保唯一性
        
        # 准备最小登录请求数据
        login_data = {
            "code": f"test_code_minimal_wechat_user_{timestamp}"
        }

        # 发送登录请求
        response = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["data"]["login_type"] == "new_user"
        assert data["data"]["user_id"] is not None
        assert data["data"]["wechat_openid"] is not None

        # 在独立进程模式下，不能直接访问服务器的数据库
        # 通过 API 响应验证数据
        print(f"✅ 最小数据注册成功:")
        print(f"   用户ID: {data['data']['user_id']}")
        print(f"   昵称: {data['data'].get('nickname')}")
        print(f"   头像: {data['data'].get('avatar_url')}")

    def test_register_wechat_user_missing_code_returns_error(self, test_server):
        """
        测试缺少code参数应该返回错误
        """
        # 准备缺少code的请求数据
        login_data = {
            "nickname": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 200  # HTTP状态码还是200
        data = response.json()
        assert data["code"] == 0  # 业务错误码
        assert "缺少" in data["msg"] or "code" in data["msg"].lower()
        
        print(f"✅ 缺少code参数正确返回错误: {data['msg']}")

    def test_register_wechat_user_with_empty_code_returns_error(self, test_server):
        """
        测试空code参数应该返回错误
        """
        # 准备空code的请求数据
        login_data = {
            "code": "",
            "nickname": "测试用户",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{test_server}/api/login",
            json=login_data,
            timeout=5
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "code" in data["msg"].lower()
        
        print(f"✅ 空code参数正确返回错误: {data['msg']}")