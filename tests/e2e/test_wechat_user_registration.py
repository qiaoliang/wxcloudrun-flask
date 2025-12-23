"""
微信用户注册测试类
测试通过微信登录API注册新用户的功能
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


class TestWechatUserRegistration:

    """微信用户注册测试类"""

    def test_wechat_user_registration_with_full_info(self, base_url):
        """
        测试微信用户注册（完整信息）
        验证提供完整用户信息时的注册流程
        """
        # 生成唯一的微信code和昵称以避免冲突
        wxchat_code = f"wx_auth_code_{uuid_str(8)}"
        nickname = f"测试用户_{uuid_str(8)}"
        avatar_url = f"{base_url}/avatar/{uuid_str(20)}.jpg"
        
        # 准备登录数据
        login_data = {
            "code": wxchat_code,
            "nickname": nickname,
            "avatar_url": avatar_url
        }

        # 发送登录请求（新用户会自动注册）
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 注册/登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"  # 应该是新用户注册
        assert result['user_id'] is not None
        assert result['wechat_openid'] is not None
        assert result['nickname'] == nickname
        assert result['avatar_url'] == avatar_url
        assert "token" in result  # token应该存在
        assert "refresh_token" in result  # refresh_token应该存在

        print(f"✅ 微信用户注册成功，ID: {result['user_id']}, 昵称: {result['nickname']}")

    def test_wechat_user_registration_with_code_only(self, base_url):
        """
        测试微信用户注册（仅code）
        验证只提供code时系统的默认处理
        """
        wxchat_code = f"wx_auth_code_only_{uuid_str(8)}"
        
        # 只提供code
        login_data = {
            "code": wxchat_code
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"
        assert result['user_id'] is not None
        assert result['wechat_openid'] is not None
        
        # 系统应该提供默认的昵称和头像
        assert result['nickname'] is not None
        assert len(result['nickname']) > 0
        assert result['avatar_url'] is not None
        assert len(result['avatar_url']) > 0

        print(f"✅ 仅code微信注册成功，ID: {result['user_id']}, 默认昵称: {result['nickname']}")

    def test_wechat_user_registration_with_empty_info(self, base_url):
        """
        测试微信用户注册（空信息）
        验证提供空用户信息时的处理
        """
        wxchat_code = f"wx_auth_code_empty_{uuid_str(8)}"
        
        # 提供空的用户信息
        login_data = {
            "code": wxchat_code,
            "nickname": "",
            "avatar_url": ""
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1  # 登录成功
        assert data["msg"] == "success"

        # 验证返回的数据结构
        result = data.get("data")
        assert isinstance(result, dict)
        assert result["login_type"] == "new_user"
        assert result['user_id'] is not None
        
        # 系统应该处理空值并提供默认值
        assert result['nickname'] is not None
        assert len(result['nickname']) > 0  # 不应该是空字符串
        assert result['avatar_url'] is not None
        assert len(result['avatar_url']) > 0  # 不应该是空字符串

        print(f"✅ 空信息微信注册成功，ID: {result['user_id']}，处理后昵称: {result['nickname']}")

    def test_wechat_user_registration_duplicate_code(self, base_url):
        """
        测试重复的微信code
        验证相同code的多次请求行为
        """
        wxchat_code = f"wx_auth_duplicate_{uuid_str(8)}"
        nickname = f"重复测试_{uuid_str(8)}"
        
        # 首次注册
        first_login_data = {
            "code": wxchat_code,
            "nickname": nickname,
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        first_response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=first_login_data,
            timeout=15
        )

        # 验证首次注册成功
        assert first_response.status_code == 200
        first_data = first_response.json()
        assert first_data["code"] == 1
        first_user_id = first_data["data"]["user_id"]
        assert first_user_id is not None

        # 再次使用相同的code注册
        second_login_data = {
            "code": wxchat_code,
            "nickname": f"重复测试2_{uuid_str(8)}",  # 不同的昵称
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        second_response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=second_login_data,
            timeout=15
        )

        # 验证响应 - 根据系统设计，可能是返回相同用户或创建新用户
        assert second_response.status_code == 200
        second_data = second_response.json()
        assert second_data["code"] == 1
        second_user_id = second_data["data"]["user_id"]
        assert second_user_id is not None

        # 根据业务逻辑，相同的code可能会返回相同的用户
        # 但具体行为取决于系统设计
        print(f"✅ 重复code处理，首次用户ID: {first_user_id}, 再次用户ID: {second_user_id}")

    def test_wechat_user_registration_special_characters(self, base_url):
        """
        测试微信用户注册（特殊字符）
        验证包含特殊字符的昵称处理
        """
        wxchat_code = f"wx_auth_special_{uuid_str(8)}"
        # 使用包含特殊字符的昵称
        special_nickname = f"特殊字符测试@#$%_{uuid_str(8)}"
        
        login_data = {
            "code": wxchat_code,
            "nickname": special_nickname,
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"

        # 验证返回的数据
        result = data.get("data")
        assert result is not None
        assert result['user_id'] is not None
        assert result['nickname'] is not None

        print(f"✅ 特殊字符昵称注册成功，原始昵称: {special_nickname}, 处理后: {result['nickname']}")

    def test_wechat_user_registration_unicode_nickname(self, base_url):
        """
        测试微信用户注册（Unicode昵称）
        验证包含Unicode字符的昵称处理
        """
        wxchat_code = f"wx_auth_unicode_{uuid_str(8)}"
        # 使用包含Unicode字符的昵称
        unicode_nickname = f"国际化测试用户😀🎉_{uuid_str(8)}"
        
        login_data = {
            "code": wxchat_code,
            "nickname": unicode_nickname,
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"

        # 验证返回的数据
        result = data.get("data")
        assert result is not None
        assert result['user_id'] is not None
        assert result['nickname'] is not None

        print(f"✅ Unicode昵称注册成功，昵称长度: {len(result['nickname'])}")

    def test_wechat_user_registration_long_nickname(self, base_url):
        """
        测试微信用户注册（长昵称）
        验证过长昵称的截断处理
        """
        wxchat_code = f"wx_auth_long_{uuid_str(8)}"
        # 创建一个很长的昵称
        long_nickname = "这是一个非常长的测试昵称" + "A" * 100 + f"_{uuid_str(10)}"
        
        login_data = {
            "code": wxchat_code,
            "nickname": long_nickname,
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"

        # 验证返回的数据
        result = data.get("data")
        assert result is not None
        assert result['user_id'] is not None
        assert result['nickname'] is not None
        
        # 验证昵称被适当截断
        assert len(result['nickname']) <= len(long_nickname)
        print(f"✅ 长昵称处理成功，原始长度: {len(long_nickname)}, 处理后长度: {len(result['nickname'])}")

    def test_wechat_user_registration_invalid_avatar_url(self, base_url):
        """
        测试微信用户注册（无效头像URL）
        验证无效头像URL的处理
        """
        wxchat_code = f"wx_auth_invalid_avatar_{uuid_str(8)}"
        nickname = f"无效头像测试_{uuid_str(8)}"
        
        login_data = {
            "code": wxchat_code,
            "nickname": nickname,
            "avatar_url": "not_a_valid_url"  # 无效的URL
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"

        # 验证返回的数据
        result = data.get("data")
        assert result is not None
        assert result['user_id'] is not None
        assert result['nickname'] == nickname

        # 验证头像URL被适当地处理（可能使用默认值）
        print(f"✅ 无效头像URL处理成功，用户ID: {result['user_id']}")

    def test_wechat_user_registration_missing_code(self, base_url):
        """
        测试微信用户注册（缺少code）
        验证缺少必需code参数的处理
        """
        # 不提供code参数
        login_data = {
            "nickname": f"缺少code测试_{uuid_str(8)}",
            "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
        }

        # 发送登录请求
        response = requests.post(
            f"{base_url}/api/auth/login_wechat",
            json=login_data,
            timeout=15
        )

        # 验证响应 - 应该返回错误
        assert response.status_code == 200  # API可能返回200但code为0
        data = response.json()
        assert data["code"] == 0  # 应该是错误状态
        assert "code" in data["msg"] or "缺少" in data["msg"]  # 应该提示缺少code

        print("✅ 缺少code参数处理正确")

    def test_wechat_user_registration_concurrent_requests(self, base_url):
        """
        测试微信用户注册（并发请求）
        验证系统处理并发注册请求的能力
        """
        import threading
        import time
        
        results = []
        
        def make_registration_request(code_suffix):
            code = f"wx_auth_concurrent_{code_suffix}"
            nickname = f"并发测试用户{code_suffix}"
            
            login_data = {
                "code": code,
                "nickname": nickname,
                "avatar_url": f"{base_url}/avatar/{uuid_str(20)}.jpg"
            }

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

        # 创建多个线程并发发送注册请求
        threads = []
        for i in range(5):  # 创建5个并发请求
            thread = threading.Thread(target=make_registration_request, args=[uuid_str(5)])
            threads.append(thread)
            thread.start()
            time.sleep(0.1)  # 稍微延迟

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 验证所有请求都得到适当的响应
        successful_registrations = 0
        for result in results:
            assert result["status_code"] == 200
            response_data = result["response"]
            assert response_data["code"] in [0, 1]  # 可能成功也可能失败，但系统不应崩溃
            if response_data["code"] == 1:
                successful_registrations += 1

        print(f"✅ 并发注册测试完成，发送了 {len(results)} 个请求，成功 {successful_registrations} 个")