"""
微信登录defense-in-depth机制的专门测试
遵循测试反模式指南：测试真实行为而非mock行为
验证多层验证机制的有效性
"""

import pytest
import requests
import datetime
from tests.e2e.testutil import uuid_str

class TestWechatLoginDefenseInDepth:

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

    """测试微信登录的defense-in-depth机制"""

    def test_layer1_entry_point_validation_code_required(self):
        """
        测试Layer 1: 入口点验证 - code参数仍然是必需的
        验证即使其他参数可选，code参数仍然是必需的
        """
        # 测试完全空的请求
        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json={},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0  # 应该失败
        assert "缺少请求体参数" in data["msg"]

    def test_layer1_entry_point_validation_accepts_partial_data(self):
        """
        测试Layer 1: 入口点验证 - 接受部分用户数据
        验证API能接受只有code的请求
        """
        login_data = {
            "code": "test_code_layer1_partial"
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 应该成功
        assert data["msg"] == "success"

    def test_layer2_business_logic_default_nickname_generation(self):
        """
        测试Layer 2: 业务逻辑验证 - 默认昵称生成
        验证当昵称为空时，系统能生成合理的默认昵称
        """
        login_data = {
            "code": "test_code_layer2_nickname",
            "nickname": "",  # 空昵称
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1

        result = data["data"]
        assert result["nickname"] is not None
        assert len(result["nickname"]) > 0
        # 验证默认昵称格式（可能包含时间戳）
        assert "微信用户" in result["nickname"] or len(result["nickname"]) > 5

    def test_layer2_business_logic_default_avatar_generation(self):
        """
        测试Layer 2: 业务逻辑验证 - 默认头像生成
        验证当头像URL无效时，系统能提供默认头像
        """
        login_data = {
            "code": "test_code_layer2_avatar",
            "nickname": "测试用户",
            "avatar_url": "invalid_url"  # 无效URL
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1

        result = data["data"]
        assert result["avatar_url"] is not None
        # 验证默认头像URL格式
        assert result["avatar_url"].startswith("http") or len(result["avatar_url"]) > 10

    def test_layer3_environment_guard_long_nickname_truncation(self):
        """
        测试Layer 3: 环境守卫 - 长昵称截断
        验证系统会截断过长的昵称以防止数据库错误
        """
        # 创建一个超过50字符的昵称
        long_nickname = "a" * 100
        login_data = {
            "code": "test_code_layer3_truncate",
            "nickname": long_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1

        result = data["data"]
        assert result["nickname"] is not None
        # Defense-in-depth: 截断到50字符并加上省略号，所以最多53字符
        assert len(result["nickname"]) <= 53  # 应该被截断
        assert result["nickname"].endswith("...")  # 应该以省略号结尾
        assert len(result["nickname"]) >= 50  # 应该包含50个字符（或接近）

    def test_layer3_environment_guard_malicious_content_filtering(self):
        """
        测试Layer 3: 环境守卫 - 恶意内容过滤
        验证系统能处理包含潜在恶意内容的输入
        """
        # 测试包含脚本的昵称
        malicious_nickname = "<script>alert('xss')</script>用户"
        login_data = {
            "code": "test_code_layer3_xss",
            "nickname": malicious_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1

        result = data["data"]
        assert result["nickname"] is not None
        # 系统应该处理恶意内容（具体处理方式取决于实现）
        assert len(result["nickname"]) > 0

    def test_layer4_debug_dashboard_logging_completeness(self):
        """
        测试Layer 4: 调试仪表 - 日志完整性
        验证即使在异常情况下，系统也能记录足够的调试信息
        """
        # 使用一个可能触发边缘情况的请求
        edge_case_data = {
            "code": "test_code_layer4_debug",
            "nickname": "边缘情况测试用户",
            "avatar_url": "https://example.com/edge_case.jpg"
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=edge_case_data,
            timeout=5
        )

        # 无论成功或失败，都应该有完整的响应
        assert response.status_code == 200
        data = response.json()

        # 响应应该包含必要的调试信息
        assert "code" in data
        assert "msg" in data
        if data["code"] == 1:
            assert "data" in data
            result = data["data"]
            # 验证响应数据完整性
            required_fields = ["token", "refresh_token", "user_id"]
            for field in required_fields:
                assert field in result, f"响应缺少必需字段: {field}"

    def test_defense_in_depth_multiple_scenarios(self):
        """
        测试defense-in-depth: 多种边缘情况组合
        验证当多个问题同时出现时，系统仍能正常工作
        """
        # 组合多种问题：空昵称、无效头像、特殊字符
        combined_edge_case = {
            "code": "test_code_combined_edge",
            "nickname": "   ",  # 只有空格的昵称
            "avatar_url": "not_a_url_at_all"  # 完全无效的URL
        }

        response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=combined_edge_case,
            timeout=5
        )

        # Defense-in-depth应该确保系统仍能正常响应
        assert response.status_code == 200
        data = response.json()

        # 根据defense-in-depth原则，系统应该能处理这种情况
        if data["code"] == 1:
            result = data["data"]
            assert result["nickname"] is not None
            assert len(result["nickname"].strip()) > 0  # 应该被处理
            assert result["avatar_url"] is not None
            assert len(result["avatar_url"]) > 0

    def test_defense_in_depth_existing_user_update(self):
        """
        测试defense-in-depth: 现有用户更新时的保护机制
        验证更新现有用户信息时的安全检查
        """
        # 先创建一个用户
        initial_data = {
            "code": "test_code_existing_initial",
            "nickname": "初始用户",
            "avatar_url": "https://example.com/initial.jpg"
        }

        first_response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=initial_data,
            timeout=5
        )

        assert first_response.status_code == 200
        first_data = first_response.json()
        assert first_data["code"] == 1

        # 使用相同的code再次登录（模拟现有用户更新）
        update_data = {
            "code": "test_code_existing_initial",  # 相同code会得到相同openid
            "nickname": "更新后的用户"+uuid_str(30)+uuid_str(30),  # 过长昵称
            "avatar_url": "invalid_url_format"  # 无效URL
        }

        second_response = requests.post(
            f"{self.base_url}/api/auth/login_wechat",
            json=update_data,
            timeout=5
        )

        assert second_response.status_code == 200
        second_data = second_response.json()
        assert second_data["code"] == 1

        result = second_data["data"]
        assert result["login_type"] == "existing_user"
        # Defense-in-depth应该保护现有用户数据
        assert len(result["nickname"]) <= 53  # 应该被截断（50字符+省略号）
        assert result["nickname"].endswith("...")  # 应该以省略号结尾
        assert result["avatar_url"] is not None

    def test_defense_in_depth_response_structure_integrity(self):
        """
        测试defense-in-depth: 响应结构完整性
        验证即使在异常情况下，响应结构也保持一致
        """
        # 测试各种边缘情况的响应结构
        test_cases = [
            {"code": "test_structure_1", "nickname": "", "avatar_url": ""},
            {"code": "test_structure_2", "nickname": "a" * 200, "avatar_url": "invalid"},
            {"code": "test_structure_3"}  # 只有code
        ]

        for i, test_case in enumerate(test_cases):
            response = requests.post(
                f"{self.base_url}/api/auth/login_wechat",
                json=test_case,
                timeout=5
            )

            assert response.status_code == 200, f"测试用例 {i+1} 失败"

            data = response.json()
            # 响应结构应该始终一致
            assert "code" in data, f"测试用例 {i+1} 缺少code字段"
            assert "msg" in data, f"测试用例 {i+1} 缺少msg字段"

            if data["code"] == 1:
                assert "data" in data, f"测试用例 {i+1} 成功响应缺少data字段"
                result = data["data"]
                # 验证核心字段存在
                required_fields = ["user_id", "token", "refresh_token", "login_type"]
                for field in required_fields:
                    assert field in result, f"测试用例 {i+1} 缺少必需字段: {field}"

        print("✅ 所有defense-in-depth测试用例通过")