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
        # 使用DAO查询登录用户
        with app.app_context():
            queried_user = dao.query_user_by_id(result['user_id'])

            # 验证DAO查询到的用户数据
            assert queried_user is not None
            assert queried_user.user_id == result['user_id']

        return response.json()

    def test_search_users_success(self, test_server, auth_headers):
        """
        测试用户搜索成功
        应该返回匹配的用户列表
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

        # 搜索用户
        params = {"nickname": expected_user_nickname}
        response = requests.get(
            f"{url_env}/api/users/search",
            params=params,
            headers=user_auth_headers,
            timeout=5
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"
        assert "data" in data
        assert "users" in data["data"]
        assert isinstance(data["data"]["users"], list)

        users = data["data"]["users"]
        # TODO: 当前搜索功能可能未完全实现，返回空列表
        # 当搜索功能完善后，应该取消下面的注释
        # # 验证返回的用户包含搜索关键词
        assert len(users) == 1

        print("✅ 用户搜索成功测试通过（搜索功能可能需要完善）")
