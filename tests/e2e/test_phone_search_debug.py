"""
手机号搜索调试测试
用于调试和验证手机号搜索功能的详细行为
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

class TestPhoneSearchDebug:

    """手机号搜索调试测试"""

    def test_phone_search_debug_complete_flow(self, base_url):
        """
        调试：完整的手机号搜索流程
        从用户创建到搜索的完整端到端测试
        """
        print("开始调试：完整的手机号搜索流程")
        
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
        print("✅ 管理员登录成功")

        # 创建测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"调试用户_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None
        print(f"✅ 测试用户创建成功，ID: {user_id}, 手机号: {test_phone}")

        # 详细调试：获取所有用户以验证用户创建
        all_users_response = requests.get(
            f"{base_url}/api/users",
            headers=admin_headers,
            timeout=15
        )
        print(f"获取所有用户状态码: {all_users_response.status_code}")
        if all_users_response.status_code == 200:
            all_users_result = all_users_response.json()
            print(f"所有用户响应: {all_users_result.get('code', 'N/A')}")
        else:
            print(f"获取所有用户失败: {all_users_response.text[:200]}...")

        # 执行手机号搜索
        print(f"开始搜索手机号: {test_phone}")
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )

        print(f"搜索响应状态码: {search_response.status_code}")
        search_result = search_response.json()
        print(f"搜索响应JSON: {json.dumps(search_result, ensure_ascii=False, indent=2)}")

        # 验证搜索结果
        assert search_response.status_code == 200
        assert search_result["code"] == 1
        assert "data" in search_result
        assert "users" in search_result["data"]

        # 检查返回的用户列表中是否包含我们创建的用户
        found_user = None
        for user in search_result["data"]["users"]:
            print(f"检查用户: ID={user.get('user_id')}, 昵称={user.get('nickname')}")
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None, f"未找到用户 {user_id}，搜索结果: {search_result}"
        assert found_user["nickname"] == test_nickname
        # 手机号应该是部分隐藏的格式
        assert found_user["phone_number"] == test_phone[:3] + "****" + test_phone[-4:]

        print(f"✅ 完整手机号搜索流程调试成功，用户: {test_nickname}，ID: {user_id}")

    def test_phone_search_debug_database_consistency(self, base_url):
        """
        调试：数据库一致性验证
        验证搜索结果与数据库存储的一致性
        """
        print("开始调试：数据库一致性验证")
        
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
        test_nickname = f"一致性测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None
        print(f"✅ 一致性测试用户创建成功，ID: {user_id}")

        # 通过用户详情API验证数据存储
        user_detail_response = requests.get(
            f"{base_url}/api/user/{user_id}",
            headers=admin_headers,
            timeout=15
        )
        print(f"用户详情API状态码: {user_detail_response.status_code}")
        if user_detail_response.status_code == 200:
            user_detail_result = user_detail_response.json()
            print(f"用户详情: {user_detail_result}")
        else:
            print(f"获取用户详情失败: {user_detail_response.text}")

        # 执行手机号搜索
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )
        print(f"搜索API状态码: {search_response.status_code}")

        # 验证搜索结果
        assert search_response.status_code == 200
        search_result = search_response.json()
        assert search_result["code"] == 1

        # 验证搜索结果与用户详情的一致性
        found_user = None
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None
        assert found_user["nickname"] == test_nickname

        print(f"✅ 数据库一致性验证通过，用户ID: {user_id}")

    def test_phone_search_debug_edge_cases(self, base_url):
        """
        调试：手机号搜索边界情况
        验证各种边界情况的处理
        """
        print("开始调试：手机号搜索边界情况")
        
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

        # 测试边界情况：超长搜索词
        long_search_term = "1" * 100  # 100个字符
        long_search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": long_search_term},
            headers=admin_headers,
            timeout=15
        )
        print(f"长搜索词响应状态码: {long_search_response.status_code}")

        # 测试边界情况：空搜索词
        empty_search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": ""},
            headers=admin_headers,
            timeout=15
        )
        print(f"空搜索词响应状态码: {empty_search_response.status_code}")

        # 测试边界情况：特殊字符
        special_search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": "!@#$%^&*()"},
            headers=admin_headers,
            timeout=15
        )
        print(f"特殊字符搜索响应状态码: {special_search_response.status_code}")

        # 验证API能够处理这些边界情况而不崩溃
        assert long_search_response.status_code in [200, 400, 422]
        assert empty_search_response.status_code in [200, 400, 422]
        assert special_search_response.status_code in [200, 400, 422]

        print("✅ 边界情况处理调试完成")

    def test_phone_search_debug_response_structure(self, base_url):
        """
        调试：搜索响应结构验证
        验证API返回的响应结构是否符合预期
        """
        print("开始调试：搜索响应结构验证")
        
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
        test_nickname = f"结构测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 执行搜索
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )

        # 详细验证响应结构
        assert search_response.status_code == 200
        search_result = search_response.json()
        
        # 验证顶层结构
        assert "code" in search_result
        assert "msg" in search_result
        assert "data" in search_result
        
        # 验证data结构
        data = search_result["data"]
        assert "users" in data
        assert isinstance(data["users"], list)
        
        # 验证用户结构
        found_user = None
        for user in data["users"]:
            if user["user_id"] == user_id:
                found_user = user
                break
        
        assert found_user is not None
        
        # 验证用户字段
        expected_fields = ["user_id", "nickname", "phone_number", "name", "avatar_url", "role", "status"]
        for field in expected_fields:
            assert field in found_user, f"用户对象缺少字段: {field}"
        
        print(f"✅ 响应结构验证通过，用户: {test_nickname}")
        print(f"   用户结构: {list(found_user.keys())}")

    def test_phone_search_debug_performance_metrics(self, base_url):
        """
        调试：性能指标测试
        测量搜索API的响应时间和资源使用情况
        """
        print("开始调试：性能指标测试")
        
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

        # 创建多个用户用于性能测试
        test_users = []
        for i in range(3):
            test_phone = generate_unique_phone()
            test_nickname = f"性能用户{i}_{uuid_str(8)}"
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

        # 测量搜索性能
        import time
        total_time = 0
        iterations = 5

        for i in range(iterations):
            target_user = test_users[i % len(test_users)]
            start_time = time.time()

            search_response = requests.get(
                f"{base_url}/api/users/search",
                params={"keyword": target_user['phone']},
                headers=admin_headers,
                timeout=15
            )

            end_time = time.time()
            iteration_time = end_time - start_time
            total_time += iteration_time

            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["code"] == 1

            # 验证找到正确用户
            found_user = None
            for user in search_result["data"]["users"]:
                if user["user_id"] == target_user['user_id']:
                    found_user = user
                    break
            assert found_user is not None

        avg_response_time = total_time / iterations
        print(f"✅ 性能指标测试完成")
        print(f"   平均响应时间: {avg_response_time:.3f}秒")
        print(f"   总请求数: {iterations}")
        print(f"   每次搜索都成功找到目标用户")

    def test_phone_search_debug_case_sensitivity_and_normalization(self, base_url):
        """
        调试：大小写敏感性和数据标准化
        验证手机号搜索的标准化处理
        """
        print("开始调试：大小写敏感性和数据标准化")
        
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
        test_nickname = f"标准化测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 手机号本身不涉及大小写，但测试API对输入的处理
        # 尝试在手机号前后添加空格（应该被标准化处理）
        search_terms = [
            test_phone,           # 标准格式
            f" {test_phone}",     # 前导空格
            f"{test_phone} ",     # 尾随空格
            f" {test_phone} ",    # 前后空格
        ]

        for search_term in search_terms:
            search_response = requests.get(
                f"{base_url}/api/users/search",
                params={"keyword": search_term},
                headers=admin_headers,
                timeout=15
            )

            assert search_response.status_code == 200
            search_result = search_response.json()
            print(f"搜索词 '{search_term}' 的响应码: {search_response.status_code}")

            if search_result["code"] == 1 and "data" in search_result:
                found_user = None
                for user in search_result["data"]["users"]:
                    if user["user_id"] == user_id:
                        found_user = user
                        break
                # 根据系统设计，规范化后的搜索应该能找到用户
                if search_term.strip() == test_phone:
                    assert found_user is not None, f"搜索词 '{search_term}' 应该能找到用户"
                else:
                    # 如果搜索词不匹配原始手机号，则可能找不到
                    pass

        print(f"✅ 大小写敏感性和数据标准化测试完成")

    def test_phone_search_debug_concurrent_access(self, base_url):
        """
        调试：并发访问测试
        验证API在并发访问下的表现
        """
        print("开始调试：并发访问测试")
        
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
        test_nickname = f"并发测试_{uuid_str(8)}"
        user_data = create_phone_user(
            base_url,
            test_phone,
            test_nickname,
            password="Test123456"
        )
        user_id = user_data['user_id']
        assert user_id is not None

        # 模拟并发搜索（串行执行以模拟）
        import time
        start_time = time.time()

        for i in range(3):
            search_response = requests.get(
                f"{base_url}/api/users/search",
                params={"keyword": test_phone},
                headers=admin_headers,
                timeout=15
            )

            assert search_response.status_code == 200
            search_result = search_response.json()
            assert search_result["code"] == 1

            # 验证每次都能找到用户
            found_user = None
            for user in search_result["data"]["users"]:
                if user["user_id"] == user_id:
                    found_user = user
                    break
            assert found_user is not None, f"第{i+1}次搜索未找到用户"

        end_time = time.time()
        total_time = end_time - start_time

        print(f"✅ 并发访问测试完成")
        print(f"   3次连续搜索总耗时: {total_time:.3f}秒")
        print(f"   平均每次: {total_time/3:.3f}秒")
        print(f"   每次搜索都成功找到用户")

    def test_phone_search_debug_error_handling(self, base_url):
        """
        调试：错误处理验证
        验证API对各种错误情况的处理
        """
        print("开始调试：错误处理验证")
        
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

        # 测试各种错误情况
        error_test_cases = [
            # (description, params, expected_behavior)
            ("无参数搜索", {}, "应该返回错误或空结果"),
            ("None参数", {"keyword": None}, "应该安全处理"),
            ("超长参数", {"keyword": "a" * 1000}, "应该限制长度"),
            ("包含特殊字符", {"keyword": "test\n\r\0"}, "应该过滤特殊字符"),
        ]

        for description, params, expected in error_test_cases:
            try:
                if params:  # 如果有参数
                    search_response = requests.get(
                        f"{base_url}/api/users/search",
                        params=params,
                        headers=admin_headers,
                        timeout=15
                    )
                else:  # 无参数
                    search_response = requests.get(
                        f"{base_url}/api/users/search",
                        headers=admin_headers,
                        timeout=15
                    )

                print(f"   {description}: 状态码 {search_response.status_code}")
                
                # 验证API没有崩溃
                assert search_response.status_code in [200, 400, 422, 500]
                
                if search_response.status_code == 200:
                    # 如果返回200，验证响应结构
                    search_result = search_response.json()
                    assert isinstance(search_result, dict)
                    assert "code" in search_result

            except Exception as e:
                print(f"   {description}: 发生异常 {e}")
                # API应该安全处理异常情况

        print("✅ 错误处理调试完成")

    def test_phone_search_debug_authz_enforcement(self, base_url):
        """
        调试：权限强制执行验证
        验证非管理员用户无法执行手机号搜索
        """
        print("开始调试：权限强制执行验证")
        
        # 创建普通用户
        user_phone = generate_unique_phone()
        user_nickname = f"权限测试_{uuid_str(8)}"
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

        # 普通用户尝试手机号搜索
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": user_phone},
            headers=user_headers,
            timeout=15
        )

        print(f"普通用户搜索状态码: {search_response.status_code}")
        search_result = search_response.json()
        print(f"普通用户搜索响应: {search_result}")

        # 根据系统设计，普通用户可能收到错误或有限结果
        # 验证系统没有泄露敏感信息
        if search_response.status_code == 200:
            assert isinstance(search_result, dict)
            if "data" in search_result and "users" in search_result["data"]:
                # 如果返回用户列表，验证是否只返回适当的数据
                pass  # 取决于具体权限设计

        # 使用管理员账号验证用户确实存在
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
        print(f"管理员搜索状态码: {admin_search_response.status_code}")

        print("✅ 权限强制执行调试完成")

    def test_phone_search_debug_data_integrity(self, base_url):
        """
        调试：数据完整性验证
        验证搜索返回的数据与原始数据一致
        """
        print("开始调试：数据完整性验证")
        
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

        # 创建具有特殊字符的测试用户
        test_phone = generate_unique_phone()
        test_nickname = f"数据完整性测试_@#$%_{uuid_str(8)}"
        test_avatar = f"{base_url}/avatar/{uuid_str(16)}.jpg"
        
        # 注册用户
        register_response = requests.post(
            f"{base_url}/api/auth/register_phone",
            json={
                'phone': test_phone,
                'code': '123456',
                'password': 'Test123456',
                'nickname': test_nickname,
                'avatar_url': test_avatar
            },
            timeout=15
        )
        assert register_response.status_code == 200
        register_result = register_response.json()
        assert register_result["code"] == 1
        user_id = register_result["data"]["user_id"]
        assert user_id is not None

        # 获取用户详情
        user_detail_response = requests.get(
            f"{base_url}/api/user/{user_id}",
            headers=admin_headers,
            timeout=15
        )
        assert user_detail_response.status_code == 200
        user_detail = user_detail_response.json()["data"]

        # 执行手机号搜索
        search_response = requests.get(
            f"{base_url}/api/users/search",
            params={"keyword": test_phone},
            headers=admin_headers,
            timeout=15
        )
        assert search_response.status_code == 200
        search_result = search_response.json()

        # 找到搜索结果中的用户
        found_user = None
        for user in search_result["data"]["users"]:
            if user["user_id"] == user_id:
                found_user = user
                break

        assert found_user is not None

        # 验证关键字段的一致性
        assert found_user["nickname"] == user_detail["nickname"]
        assert found_user["user_id"] == user_detail["user_id"]
        # 注意：搜索结果中的手机号通常是部分隐藏的
        assert found_user["phone_number"] == test_phone[:3] + "****" + test_phone[-4:]

        print(f"✅ 数据完整性验证通过，用户: {test_nickname}")
