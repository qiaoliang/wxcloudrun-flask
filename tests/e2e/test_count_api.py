"""
测试计数器API的E2E测试用例
"""

import pytest
import requests
import json


class TestCountAPI:

    def setup_method(self):
        """每个测试方法前的设置：启动 Flask 应用"""
        import os
        import sys
        import time
        import subprocess
        import requests
        
        # 设置环境变量
        os.environ['ENV_TYPE'] = 'unit'
        
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

    """计数器API测试类"""

    def test_get_count_initial_value(self):
        """
        测试获取计数器初始值
        验证新启动的环境计数器值为0
        """
        response = requests.get(f"{self.base_url}/api/count", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert "data" in data
        assert data["data"] == 0
        print("✅ 初始计数器值为0")





    def test_post_count_clear(self):
        """
        测试清零计数器
        """
        # 先递增几次
        for _ in range(3):
            requests.post(
                f"{self.base_url}/api/count",
                json={"action": "inc"},
                timeout=5
            )

        # 清零
        response = requests.post(
            f"{self.base_url}/api/count",
            json={"action": "clear"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"
        print("✅ 计数器清零成功")

        # 验证计数器值为0
        response = requests.get(f"{self.base_url}/api/count", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == 0
        print("✅ 清零后计数器值为0")

    def test_post_count_invalid_action(self):
        """
        测试无效的action参数
        """
        response = requests.post(
            f"{self.base_url}/api/count",
            json={"action": "invalid"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "action参数错误" in data["data"]
        print("✅ 无效action参数正确返回错误")

    def test_post_count_missing_action(self):
        """
        测试缺少action参数
        """
        response = requests.post(
            f"{self.base_url}/api/count",
            json={},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "缺少action参数" in data["data"]
        print("✅ 缺少action参数正确返回错误")

    def test_post_count_invalid_json(self):
        """
        测试无效的JSON格式
        """
        response = requests.post(
            f"{self.base_url}/api/count",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        # 服务器应该返回400错误或类似的错误响应
        assert response.status_code != 200
        print("✅ 无效JSON格式正确返回错误")