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
from wxcloudrun import dao, app

class TestUserAPI:

    def setup_method(self):
        """每个测试方法前的设置：启动 Flask 应用"""
        import os
        import sys
        import time
        import subprocess
        import requests
        
        # 设置环境变量
        os.environ['ENV_TYPE'] = 'func'
        
        # 确保 src 目录在 Python 路径中
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        # 清理可能存在的进程
        self._cleanup_existing_processes()
        
        # 启动 Flask 应用（在后台运行）
        self.flask_process = subprocess.Popen(
            [sys.executable, 'main.py', '127.0.0.1', '9998'],
            cwd=src_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )
        
        # 等待应用启动
        time.sleep(5)
        
        # 验证应用是否成功启动
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'http://localhost:9998/', timeout=2)
                if response.status_code == 200:
                    print(f"Flask 应用成功启动 (尝试 {attempt + 1}/{max_attempts})")
                    break
            except requests.exceptions.RequestException:
                if attempt == max_attempts - 1:
                    pytest.fail("Flask 应用启动失败")
                time.sleep(1)
        
        # 保存base_url供测试方法使用
        self.base_url = f'http://localhost:9998'

    def teardown_method(self):
        """每个测试方法后的清理：停止 Flask 应用"""
        if hasattr(self, 'flask_process') and self.flask_process:
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
                self.flask_process.wait()
            print("Flask 应用已停止")
        
        # 再次清理可能残留的进程
        self._cleanup_existing_processes()
    
    def _cleanup_existing_processes(self):
        """清理可能存在的 Flask 进程"""
        import subprocess
        try:
            # 查找占用端口 9998 的进程
            result = subprocess.run(['lsof', '-t', '-i:9998'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                        print(f"已终止进程 {pid}")
        except Exception as e:
            print(f"清理进程时出错: {e}")

    """用户搜索API测试类"""

    def test_create_wechat_user(self):
        wechat_code = f"wx_auth_new_user_{uuid_str(5)}"
        nickname =f"wx_auth_new_nickname_{uuid_str(5)}"
        avatar_url=f"{self.base_url}/avatar/{uuid_str(20)}"
        result = create_wx_user(self.base_url, wechat_code,nickname,avatar_url)
        assert result is not None
        assert result['nickname'] == nickname
        assert result['name'] == nickname
        assert result['avatar_url'] == avatar_url

    def test_create_phone_user(self):
        import time
        # 使用时间戳确保唯一性，生成有效的11位手机号
        timestamp = int(time.time() * 1000)
        phone_number = f"139{str(timestamp)[-8:]}"  # 确保139开头，共11位
        nickname =f"phone_user_nickname_{uuid_str(5)}"

        pwd=f"{self.base_url}/avatar/{uuid_str(20)}"
        result = create_phone_user(self.base_url, phone_number, nickname, pwd)
        assert result is not None
        assert result['user_id'] is not None
        assert result['phone_number'] == f"139****{phone_number[-4:]}"
        assert result['name'] == nickname


    def test_search_users_success(self):
        """
        测试用户搜索成功
        应该返回匹配的用户列表

        注意：/api/users/search 要求 super_admin 权限搜索所有用户，
        或者使用 scope='community' 在社区内搜索
        """
        url_env = self.base_url
        # 创建测试用户
        expected_user_nickname= "t张三"
        a_user=create_wx_user(url_env, "wx-code-13812345678", expected_user_nickname)

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

    def test_search_users_by_phone_number(self):
        """
        测试通过手机号搜索用户
        验证API能够正确根据手机号找到对应的用户
        """
        url_env = self.base_url
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
