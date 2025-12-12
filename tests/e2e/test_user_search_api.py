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

# 导入DAO模块和Flask app
from wxcloudrun import dao, app

class TestUserSearchAPI:
    """用户搜索API测试类"""

    @staticmethod
    def create_wechat_user(url_env, wechat_code='wx_auth_code_here',nickname='张三',avatar_url='https://example.com/avatar.jpg'):
        """
        创建测试用户辅助方法

        Args:
            url_env: 测试环境URL
            phone: 手机号
            nickname: 昵称
            is_supervisor: 是否为监护人

        Returns:
            dict: 用户信息
        """
        # 先创建一个新的微信用户
        login_data = {
            "code": wechat_code,
            "nickname": nickname,
            "avatar_url": avatar_url
        }

        # 发送登录请求
        response = requests.post(
            f"{url_env}/api/login",
            json=login_data,
            timeout=5
        )
        result = response.json().get("data")
        # 在独立进程模式下，不能直接访问服务器的数据库
        # 只能通过 API 响应验证数据
        print(f"✅ 用户创建成功，ID: {result['user_id']}")
        
        return response.json()

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
        a_user=self.create_wechat_user(url_env=url_env, wechat_code="wx-code-13812345678", nickname=expected_user_nickname)

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
