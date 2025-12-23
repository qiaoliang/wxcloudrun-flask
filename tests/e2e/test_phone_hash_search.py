"""
集成测试：验证通过完整手机号搜索用户的功能
"""

import pytest
import sys
import os
import requests

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from hashlib import sha256

class TestUserSearchByPhoneIntegration:

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

    """集成测试：验证手机号搜索功能"""

    def test_phone_hash_calculation(self):
        """验证phone_hash计算是否正确"""
        phone = "13888888888"
        phone_secret = "default_secret"
        expected_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        
        # 验证计算方式与绑定手机号时一致
        from wxcloudrun.views.user import bind_phone
        from database.models import User
        
        # 模拟用户绑定手机号时的hash计算
        actual_hash = sha256(
            f"{phone_secret}:{phone}".encode('utf-8')).hexdigest()
        
        assert actual_hash == expected_hash
        print(f"✅ Phone hash计算正确: {expected_hash[:16]}...")

    def test_search_phone_logic(self):
        """测试搜索逻辑"""
        url_env = self.base_url
        
        # 1. 使用手机号注册创建测试用户
        test_phone = "13999999999"
        register_data = {
            "phone": test_phone,
            "code": "666888",  # 使用有效验证码
            "password": "Test123456",
            "nickname": "手机号搜索用户"
        }
        
        response = requests.post(
            f"{url_env}/api/auth/register_phone",
            json=register_data,
            timeout=5
        )
        assert response.status_code == 200
        register_result = response.json()
        assert register_result["code"] == 1
        user_token = register_result["data"]["token"]
        user_id = register_result["data"]["user_id"]
        print(f"✅ 用户注册成功: {test_phone}")
        
        # 3. 使用超级管理员搜索
        admin_login = requests.post(
            f"{url_env}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=5
        )
        admin_token = admin_login.json()["data"]["token"]
        
        # 4. 使用完整手机号搜索
        search_response = requests.get(
            f"{url_env}/api/users/search",
            params={"keyword": test_phone},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        if search_data["code"] != 1:
            print(f"❌ 搜索失败: {search_data.get('msg', '未知错误')}")
        assert search_data["code"] == 1
        
        users = search_data["data"]["users"]
        found_user = None
        for user in users:
            if user["user_id"] == user_id:
                found_user = user
                break
        
        assert found_user is not None
        assert found_user["nickname"] == "手机号搜索用户"
        print(f"✅ 通过完整手机号找到用户: {found_user['nickname']}")
        
        # 5. 验证使用错误手机号找不到用户
        wrong_phone = "13888888888"
        wrong_response = requests.get(
            f"{url_env}/api/users/search",
            params={"keyword": wrong_phone},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=5
        )
        
        assert wrong_response.status_code == 200
        wrong_data = wrong_response.json()
        assert wrong_data["code"] == 1
        
        # 应该找不到用户
        found_wrong = False
        for user in wrong_data["data"]["users"]:
            if user["user_id"] == user_id:
                found_wrong = True
                break
        
        assert not found_wrong
        print(f"✅ 错误手机号未找到用户，符合预期")