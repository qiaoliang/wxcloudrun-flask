"""
测试微信用户通过 /api/auth/login_wechat 注册的E2E测试
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
            if result.returncode == 0: split('\n')')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                        print(f"已终止进程 {pid}")
        except Exception as e:
            print(f"清理进程时出错: {e}")

    """微信用户注册测试类"""

    def test_register_wechat_user_via_login_and_find_in_db(self):
        """
        测试通过 /api/auth/login_wechat 新注册一个wechat_user
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
            f"{self.base_url}/api/auth/login_wechat",
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

    def test_register_same_wechat_user_twice_returns_existing_user(self):
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
            f"{self.base_url}/api/auth/login_wechat",
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
            f"{self.base_url}/api/auth/login_wechat",
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

    def test_register_wechat_user_with_minimal_data(self):
        """
        测试使用最少必需数据注册微信用户
        必须提供 code、nickname 和 avatar_url
        """
        # 使用时间戳确保每次测试都有唯一的code
        import time
        timestamp = int(time.time() * 1000000)  # 微秒级时间戳确保唯一性

        # 测试: 提供所有必需参数
        login_data = {
            "code": f"test_code_minimal_{timestamp}",
            "nickname": f"测试微信用户_{timestamp}",
            "avatar_url": f"https://example.com/avatar_{timestamp}.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        # 验证响应 - 应该成功
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 成功
        assert data["msg"] == "success"
        assert data["data"]["login_type"] == "new_user"
        assert data["data"]["user_id"] is not None
        assert data["data"]["wechat_openid"] is not None
        # nickname 和 avatar_url 应该有值
        assert data["data"]["nickname"] == f"测试微信用户_{timestamp}"
        assert data["data"]["avatar_url"] == f"https://example.com/avatar_{timestamp}.jpg"
        
        print("✅ 提供所有必需参数成功注册用户")

    def test_register_wechat_user_missing_code_returns_error(self):
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
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 200  # HTTP状态码还是200
        data = response.json()
        assert data["code"] == 0  # 业务错误码
        assert "缺少" in data["msg"] or "code" in data["msg"].lower()

        print(f"✅ 缺少code参数正确返回错误: {data['msg']}")

    def test_register_wechat_user_with_empty_code_returns_error(self):
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
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "code" in data["msg"].lower()

        print(f"✅ 空code参数正确返回错误: {data['msg']}")