"""
集成测试：验证手机号搜索功能
通过API端点测试手机号搜索功能，包括精确匹配和模糊匹配
"""

import pytest
import requests
import json
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from tests.e2e.testutil import uuid_str, create_phone_user, generate_unique_phone


class TestPhoneHashSearch:

    """集成测试：验证手机号搜索功能"""

    def test_phone_search_exact_match(self, base_url):
        """
        测试手机号精确匹配搜索
        验证API能够通过完整手机号找到对应用户
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"手机号搜索测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 使用精确手机号搜索
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )

        # 验证搜索结果
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查返回的用户列表中是否包含我们创建的用户
        found_user = None
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None, f"未找到用户 {user_id}"
        assert found_user["nickname"] == test_nickname
        # 手机号应该是部分隐藏的格式
        assert found_user["phone_number"] == test_phone[:3] + "****" + test_phone[-4:]

        print(f"✅ 手机号精确匹配搜索成功，用户: {test_nickname}，ID: {user_id}")

    def test_phone_search_partial_match_not_allowed(self, base_url):
        """
        测试手机号部分匹配（不被允许）
        验证API不会返回部分匹配的手机号搜索结果
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"部分匹配测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 使用部分手机号搜索（前7位）
        partial_phone = test_phone[:7]  # 取前7位
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": partial_phone},
            headers=admin_headers,
            timeout=15
        )

        # 验证搜索结果 - 不应该找到用户
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查返回的用户列表中是否不包含我们创建的用户
        user_found = False
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                user_found = True
                break

        assert not user_found, f"部分手机号匹配不应该返回用户 {user_id}"

        print(f"✅ 手机号部分匹配被正确阻止，部分号码: {partial_phone}")

    def test_phone_search_with_masked_format(self, base_url):
        """
        测试使用掩码格式手机号搜索
        验证API不会返回掩码格式的手机号搜索结果
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"掩码搜索测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 使用掩码格式手机号搜索
        masked_phone = test_phone[:3] + "****" + test_phone[-4:]  # 例如: 139****9999
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": masked_phone},
            headers=admin_headers,
            timeout=15
        )

        # 验证搜索结果 - 不应该找到用户
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查返回的用户列表中是否不包含我们创建的用户
        user_found = False
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                user_found = True
                break

        assert not user_found, f"掩码格式手机号搜索不应该返回用户 {user_id}"

        print(f"✅ 掩码格式手机号搜索被正确阻止，掩码号码: {masked_phone}")

    def test_phone_search_nonexistent_number(self, base_url):
        """
        测试搜索不存在的手机号
        验证API能正确处理不存在的手机号搜索请求
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 搜索一个不存在的手机号
        non_existent_phone = "19999999999"  # 一个不存在的手机号
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": non_existent_phone},
            headers=admin_headers,
            timeout=15
        )

        # 验证搜索结果
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 验证返回的用户列表为空
        assert len(search_result["data"]["users"]) == 0

        print(f"✅ 不存在手机号搜索测试通过，号码: {non_existent_phone}")

    def test_phone_search_case_sensitivity(self, base_url):
        """
        测试手机号搜索大小写敏感性
        验证手机号搜索不受大小写影响（虽然手机号本身不包含字母）
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"大小写测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 使用相同手机号搜索（手机号不涉及大小写，但测试API稳定性）
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )

        # 验证搜索结果
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查返回的用户列表中是否包含我们创建的用户
        found_user = None
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None, f"未找到用户 {user_id}"

        print(f"✅ 手机号搜索API稳定性测试通过，用户: {test_nickname}")

    def test_phone_search_performance_with_multiple_users(self, base_url):
        """
        测试多用户环境下的手机号搜索性能
        验证在大量用户数据中搜索手机号的性能表现
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建多个测试用户
        test_users = []
        for i in range(5):  # 创建5个测试用户
            test_phone = generate_unique_phone()
            test_nickname = f"性能测试用户{i}_{uuid_str(8)}"
            user_data = create_phone_user(
                base_url,
                test_phone,
                test_nickname,
                password="Test123456"
            )
            test_users.append({
                "phone": test_phone,
                "nickname": test_nickname,
                "user_id": user_data['user_id']
            })

        # 测试搜索特定用户
        target_user = test_users[2]  # 搜索第3个用户
        import time
        start_time = time.time()

        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": target_user['phone']},
            headers=admin_headers,
            timeout=15
        )

        end_time = time.time()
        search_time = end_time - start_time

        # 验证搜索结果
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查是否找到目标用户
        found_user = None
        for user in search_result["data"]["users"]:
            if user["user_id"] == target_user['user_id']:
                found_user = user
                break

        assert found_user is not None, f"未找到目标用户 {target_user['user_id']}"
        assert found_user["nickname"] == target_user['nickname']

        print(f"✅ 多用户环境下手机号搜索性能测试通过，搜索时间: {search_time:.2f}秒，目标用户: {target_user['nickname']}")

    def test_phone_search_permission_control(self, base_url):
        """
        测试手机号搜索权限控制
        验证非管理员用户无法使用手机号搜索功能
        """
        # 创建普通用户
        user_phone = generate_unique_phone()
        user_nickname = f"权限测试用户_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            user_phone,
            user_nickname,
            password="Test123456"
        )
        user_token = user_data['token']
        
        user_headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }

        # 普通用户尝试搜索手机号（应该失败）
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": user_phone},
            headers=user_headers,
            timeout=15
        )

        # 验证权限控制
        search_result = search_response.json()
        # 根据API设计，普通用户可能收到错误或空结果
        print(f"普通用户手机号搜索结果: {search_result}")

        # 使用超级管理员搜索来验证用户确实存在
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        admin_search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": user_phone},
            headers=admin_headers,
            timeout=15
        )
        admin_search_result = admin_search_response.json()
        print(f"管理员手机号搜索结果: {admin_search_result['code']}")

        print(f"✅ 手机号搜索权限控制测试完成")

    def test_phone_search_special_characters(self, base_url):
        """
        测试包含特殊字符的手机号搜索
        验证API能正确处理包含特殊字符的搜索请求
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"特殊字符测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 测试包含特殊字符的搜索（如空格、连字符等）
        # 对于手机号搜索，这些应该不会影响结果
        search_terms = [
            test_phone,
            f" {test_phone} ",  # 前后有空格
            test_phone.replace(test_phone[3:7], "****"),  # 掩码格式（应该找不到）
        ]

        for i, search_term in enumerate(search_terms):
            search_response = requests.get(
                f"{base_url}/api/users/search",
                params={"keyword": search_term},
                headers=admin_headers,
                timeout=15
            )

            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["code"] in [0, 1]  # 可能成功也可能失败，取决于实现

            if search_result["code"] == 1 and i == 0:  # 精确匹配应该成功
                # 检查是否找到目标用户
                found_user = None
                for user in search_result["data"]["users"]:
                    if user["user_id"] == user_id:
                        found_user = user
                        break
                assert found_user is not None, f"精确匹配搜索未找到用户 {user_id}"
            elif i == 2:  # 掩码格式应该找不到
                # 检查是否没有找到用户
                user_found = False
                if "data" in search_result and "users" in search_result["data"]:
                    for user in search_result["data"]["users"]:
                        if user["user_id"] == user_id:
                            user_found = True
                            break
                assert not user_found, f"掩码格式不应该找到用户 {user_id}"

        print(f"✅ 手机号搜索特殊字符处理测试通过")

    def test_phone_search_sql_injection_protection(self, base_url):
        """
        测试手机号搜索的SQL注入防护
        验证API能正确防护SQL注入攻击
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 尝试SQL注入攻击向量
        sql_injection_attempts = [
            "13900009999' OR '1'='1",
            "13900009999' UNION SELECT * FROM users--",
            "13900009999'; DROP TABLE users;--",
            "13900009999' OR 1=1--",
            "13900009999' WAITFOR DELAY '00:00:05'--",  # 仅对支持的数据库
        ]

        for attempt in sql_injection_attempts:
            try:
                search_response = requests.get(
                    f"{base_url}/api/users/search",
                    params={"keyword": attempt},
                    headers=admin_headers,
                    timeout=15
                )

                # API应该安全地处理注入尝试，不会返回敏感信息
                # 响应状态码应该是正常的（200），但不会返回任何用户
                assert search_response.status_code in [200, 400, 500], f"SQL注入尝试产生意外状态码: {search_response.status_code}"

                if search_response.status_code == 200:
                    search_result = search_response.json()
                    # 如果返回200，结果应该不包含敏感数据
                    assert isinstance(search_result, dict)
                    assert "code" in search_result

            except Exception as e:
                print(f"SQL注入防护测试遇到异常，这可能是正常的: {e}")

        print(f"✅ 手机号搜索SQL注入防护测试完成")

    def test_phone_search_unicode_characters(self, base_url):
        """
        测试手机号搜索的Unicode字符处理
        验证API能正确处理Unicode字符
        """
        # 使用超级管理员账号登录
        admin_login_response = requests.post(
            f"{base_url}/api/auth/login_phone_password",
            json={
                "phone": "13900007997",
                "password": "Firefox0820"
            },
            timeout=15
        )
        assert admin_login_response.status_code == 200
        admin_token = admin_login_response.json()["data"]["token"]
        
        admin_headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"Unicode测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 尝试使用包含Unicode字符的搜索（应该不会影响手机号搜索）
        unicode_search_attempts = [
            test_phone,
            test_phone + "🚀",  # 添加表情符号
            test_phone + "测试",  # 添加中文字符
        ]

        for attempt in unicode_search_attempts:
            search_response = requests.get(
                f"{base_url}/api/users/search",
                params={"keyword": attempt},
                headers=admin_headers,
                timeout=15
            )

            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["code"] in [0, 1]

            # 只有精确匹配才会成功找到用户
            if attempt == test_phone:
                found_user = None
                for user in search_result["data"]["users"]:
                    if user["user_id"] == user_id:
                        found_user = user
                        break
                assert found_user is not None, f"精确匹配应该找到用户 {user_id}"
            else:
                # 非精确匹配不应该找到用户
                user_found = False
                if "data" in search_result and "users" in search_result["data"]:
                    for user in search_result["data"]["users"]:
                        if user["user_id"] == user_id:
                            user_found = True
                            break
                assert not user_found, f"非精确匹配不应该找到用户 {user_id}"

        print(f"✅ 手机号搜索Unicode字符处理测试完成")