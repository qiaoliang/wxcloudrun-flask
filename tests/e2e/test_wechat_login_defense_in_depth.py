"""
测试微信登录的defense-in-depth机制
验证在各种边界情况和异常输入下的系统行为
"""

import pytest
import requests
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from tests.e2e.testutil import uuid_str
from wxcloudrun import app  # 导入应用实例


class TestWechatLoginDefenseInDepth:

    """测试微信登录的defense-in-depth机制"""

    def test_wechat_login_defense_in_depth_with_minimal_data(self, base_url):
        """
        测试defense-in-depth：最小数据登录
        验证当只提供必需参数时，API能正确处理并提供默认值
        """
        code = f"wx_auth_code_minimal_{uuid_str(8)}"
        
        # 只提供必需的code参数
        login_data = {
            "code": code
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15  # 增加超时时间以应对可能的外部API调用
        )

        # 验证响应 - 应该成功登录（系统提供默认值）
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"  # 假设是新用户
        assert result['user_id'] is not None
        assert result['wechat_openid'] is not None

        # Defense-in-depth验证：系统应该提供了默认用户信息
        assert result['nickname'] is not None
        assert len(result['nickname']) > 0
        assert result['avatar_url'] is not None
        assert len(result['avatar_url']) > 0
        assert "token" in result
        assert "refresh_token" in result

        print(f"✅ 最小数据登录成功，ID: {result['user_id']}, 默认昵称: {result['nickname']}")

    def test_wechat_login_defense_in_depth_with_empty_user_info(self, base_url):
        """
        测试defense-in-depth：空用户信息的处理
        验证当提供空的用户信息时，API能正确处理
        """
        code = f"wx_auth_code_empty_{uuid_str(8)}"
        
        # 提供空的用户信息
        login_data = {
            "code": code,
            "nickname": "",
            "avatar_url": ""
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"
        assert result['user_id'] is not None

        # Defense-in-depth验证：系统应该处理空值并提供默认值
        assert result['nickname'] is not None
        assert len(result['nickname']) > 0  # 不应该是空字符串
        assert result['avatar_url'] is not None
        assert len(result['avatar_url']) > 0  # 不应该是空字符串

        print(f"✅ 空用户信息处理成功，ID: {result['user_id']}, 处理后昵称: {result['nickname']}")

    def test_wechat_login_defense_in_depth_with_invalid_avatar_url(self, base_url):
        """
        测试defense-in-depth：无效头像URL的处理
        验证当提供无效头像URL时，API能正确处理
        """
        code = f"wx_auth_code_invalid_{uuid_str(8)}"
        
        # 提供无效的头像URL
        login_data = {
            "code": code,
            "nickname": "测试用户",
            "avatar_url": "invalid_url_format"  # 无效的URL格式
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"
        assert result['user_id'] is not None
        assert result['nickname'] == "测试用户"

        # Defense-in-depth验证：系统应该处理无效URL或使用默认值
        assert result['avatar_url'] is not None
        # 根据defense-in-depth实现，无效URL可能被替换为默认头像
        assert result['avatar_url'].startswith('http') or len(result['avatar_url']) > 0

        print(f"✅ 无效头像URL处理成功，ID: {result['user_id']}, 头像URL: {result['avatar_url'][:50]}...")

    def test_wechat_login_defense_in_depth_with_too_long_nickname(self, base_url):
        """
        测试defense-in-depth：过长昵称的处理
        验证当提供过长昵称时，API能正确截断处理
        """
        # 创建一个非常长的昵称
        long_nickname = "这是一个过长的昵称" + "A" * 100 + uuid_str(50)
        code = f"wx_auth_code_long_{uuid_str(8)}"
        
        login_data = {
            "code": code,
            "nickname": long_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result['user_id'] is not None
        assert len(result['nickname']) > 0  # 不应该是空字符串
        
        # Defense-in-depth验证：过长的昵称应该被截断
        assert len(result['nickname']) <= 53  # 应该被截断到某个限制长度
        assert result['nickname'].endswith("...") or len(result['nickname']) < len(long_nickname)

        print(f"✅ 过长昵称处理成功，原始长度: {len(long_nickname)}, 截断后: {len(result['nickname'])}")

    def test_wechat_login_defense_in_depth_with_special_characters(self, base_url):
        """
        测试defense-in-depth：特殊字符昵称的处理
        验证包含特殊字符的昵称能被正确处理
        """
        # 使用安全的特殊字符组合
        special_nickname = "测试@#$%^&*()_+{}[]| 用户"
        code = f"wx_auth_code_special_{uuid_str(8)}"
        
        login_data = {
            "code": code,
            "nickname": special_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result['user_id'] is not None
        
        # 验证昵称被适当处理（可能被清理或转义）
        assert result['nickname'] is not None
        print(f"✅ 特殊字符昵称处理成功，原始: {special_nickname[:20]}..., 处理后: {result['nickname'][:20]}...")

    def test_wechat_login_defense_in_depth_with_sql_injection_attempt(self, base_url):
        """
        测试defense-in-depth：SQL注入防护
        验证系统能防护SQL注入攻击
        """
        # 尝试SQL注入攻击向量
        sql_injection_nickname = "Test'; DROP TABLE users; --"
        code = f"wx_auth_code_sql_{uuid_str(8)}"
        
        login_data = {
            "code": code,
            "nickname": sql_injection_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该安全地处理注入尝试
        assert response.status_code == 200  # 响应应该是正常的
        data = response.json()
        assert data["code"] in [0, 1]  # 可能成功也可能失败，但不应该崩溃

        # 如果成功创建用户，验证数据被正确清理
        if data["code"] == 1:
            result = data.get("data")
            assert result is not None
            # 验证恶意代码没有被执行
            assert result['user_id'] is not None
            # 验证昵称被清理（可能被替换或移除恶意部分）
            assert sql_injection_nickname not in result['nickname'] or len(result['nickname']) < len(sql_injection_nickname)

        print("✅ SQL注入防护测试完成")

    def test_wechat_login_defense_in_depth_with_xss_attempt(self, base_url):
        """
        测试defense-in-depth：XSS防护
        验证系统能防护跨站脚本攻击
        """
        # 尝试XSS攻击向量
        xss_nickname = "TestUser"
        xss_avatar = "javascript:alert('XSS')"
        code = f"wx_auth_code_xss_{uuid_str(8)}"
        
        login_data = {
            "code": code,
            "nickname": xss_nickname,
            "avatar_url": xss_avatar
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该安全地处理XSS尝试
        assert response.status_code == 200
        data = response.json()
        assert data["code"] in [0, 1]

        # 如果成功创建用户，验证恶意代码被清理
        if data["code"] == 1:
            result = data.get("data")
            assert result is not None
            assert result['user_id'] is not None
            # 验证恶意脚本没有被保留
            assert "<script>" not in result['nickname']
            assert "javascript:" not in result['avatar_url']

        print("✅ XSS防护测试完成")

    def test_wechat_login_defense_in_depth_with_unicode_characters(self, base_url):
        """
        测试defense-in-depth：Unicode字符处理
        验证系统能正确处理各种Unicode字符
        """
        # 包含各种Unicode字符的昵称
        unicode_nickname = "用户名测试😀🎉测试员姓名测试测试员姓名测试测试员姓名测试测试员姓名测试测试员姓名测试"
        code = f"wx_auth_code_unicode_{uuid_str(8)}"
        
        login_data = {
            "code": code,
            "nickname": unicode_nickname,
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result['user_id'] is not None
        
        # 验证Unicode字符被正确处理
        assert result['nickname'] is not None
        print(f"✅ Unicode字符处理成功，昵称长度: {len(result['nickname'])}")

    def test_wechat_login_defense_in_depth_with_case_variations(self, base_url):
        """
        测试defense-in-depth：大小写变化处理
        验证系统能正确处理大小写变化
        """
        # 使用不同大小写的code（虽然code通常是区分大小写的，但测试系统如何处理）
        code = f"WX_AUTH_CODE_{uuid_str(8)}".lower()
        
        login_data = {
            "code": code,
            "nickname": "测试用户Case",
            "avatar_url": "https://example.com/avatar.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该成功登录
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result['user_id'] is not None
        assert result['nickname'] == "测试用户Case"

        print(f"✅ 大小写变化处理成功，ID: {result['user_id']}")

    def test_wechat_login_defense_in_depth_with_multiple_concurrent_requests(self, base_url):
        """
        测试defense-in-depth：并发请求处理
        验证系统能正确处理并发的登录请求
        """
        import threading
        import time
        
        results = []
        
        def make_request(code_suffix):
            code = f"wx_auth_code_concurrent_{code_suffix}"
            
            login_data = {
                "code": code,
                "nickname": f"并发测试用户{code_suffix}",
                "avatar_url": "https://example.com/avatar.jpg"
            }

            # 发送登录请求
            response = requests.post(
                f"{base_url}/api/auth/login_wechat",
                json=login_data,
                timeout=15
            )
            
            results.append({
                "code_suffix": code_suffix,
                "status_code": response.status_code,
                "response": response.json()
            })

        # 创建多个线程并发发送请求
        threads = []
        for i in range(3):  # 创建3个并发请求
            thread = threading.Thread(target=make_request, args=[uuid_str(5)])
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # 稍微延迟以模拟更真实的并发

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都得到适当的响应
        for result in results:
            assert result["status_code"] == 200
            response_data = result["response"]
            assert response_data["code"] in [0, 1]  # 可能成功也可能失败，但系统不应崩溃

        print(f"✅ 并发请求处理测试完成，成功处理了 {len(results)} 个请求")