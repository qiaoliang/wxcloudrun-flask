"""
测试计数器API的E2E测试用例
"""

import pytest
import requests
import json


class TestCountAPI:
    """计数器API测试类"""

    def test_get_count_initial_value(self, test_server):
        """
        测试获取计数器初始值
        验证新启动的环境计数器值为0
        """
        response = requests.get(f"{test_server}/api/count", timeout=5)

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert "data" in data
        assert data["data"] == 0
        print("✅ 初始计数器值为0")

    

    

    def test_post_count_clear(self, test_server):
        """
        测试清零计数器
        """
        # 先递增几次
        for _ in range(3):
            requests.post(
                f"{test_server}/api/count",
                json={"action": "inc"},
                timeout=5
            )

        # 清零
        response = requests.post(
            f"{test_server}/api/count",
            json={"action": "clear"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        assert data["msg"] == "success"
        print("✅ 计数器清零成功")

        # 验证计数器值为0
        response = requests.get(f"{test_server}/api/count", timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == 0
        print("✅ 清零后计数器值为0")

    def test_post_count_invalid_action(self, test_server):
        """
        测试无效的action参数
        """
        response = requests.post(
            f"{test_server}/api/count",
            json={"action": "invalid"},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "action参数错误" in data["data"]
        print("✅ 无效action参数正确返回错误")

    def test_post_count_missing_action(self, test_server):
        """
        测试缺少action参数
        """
        response = requests.post(
            f"{test_server}/api/count",
            json={},
            timeout=5
        )

        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "缺少action参数" in data["data"]
        print("✅ 缺少action参数正确返回错误")

    def test_post_count_invalid_json(self, test_server):
        """
        测试无效的JSON格式
        """
        response = requests.post(
            f"{test_server}/api/count",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=5
        )

        # 服务器应该返回400错误或类似的错误响应
        assert response.status_code != 200
        print("✅ 无效JSON格式正确返回错误")

    
    @pytest.mark.skip()
    def test_multiple_concurrent_operations(self, test_server, concurrent_context):
        """
        测试多个并发操作同时进行
        验证清理机制不会干扰并发测试
        """
        import threading
        import queue
        import time

        # 先清零计数器
        requests.post(f"{test_server}/api/count", json={"action": "clear"}, timeout=5)

        results = queue.Queue()

        # 创建多个并发操作：递增和查询
        def increment_and_check(op_id):
            try:
                # 添加随机延迟，模拟真实场景
                time.sleep(0.05 * (op_id % 3))

                # 递增
                inc_response = requests.post(
                    f"{test_server}/api/count",
                    json={"action": "inc"},
                    timeout=10  # 增加超时时间
                )

                # 短暂延迟后再查询
                time.sleep(0.02)

                # 立即查询
                get_response = requests.get(f"{test_server}/api/count", timeout=10)

                results.put({
                    "op_id": op_id,
                    "inc_status": inc_response.status_code,
                    "get_status": get_response.status_code,
                    "value": get_response.json().get("data", 0)
                })
            except Exception as e:
                results.put({
                    "op_id": op_id,
                    "error": str(e)
                })

        # 创建10个并发操作
        threads = []
        for i in range(10):
            thread = threading.Thread(target=increment_and_check, args=(i,))
            threads.append(thread)
            thread.start()

        # 等待所有线程完成
        for thread in threads:
            thread.join()

        # 检查结果
        success_count = 0
        error_count = 0
        total_value = 0

        while not results.empty():
            result = results.get()
            if "error" in result:
                error_count += 1
                print(f"操作{result['op_id']}错误: {result['error']}")
            elif result["inc_status"] == 200 and result["get_status"] == 200:
                success_count += 1
                total_value += result["value"]

        assert error_count == 0, f"有{error_count}个操作失败"
        assert success_count == 10, f"只有{success_count}/10个操作成功"
        assert total_value >= 10, f"计数器总和应该至少为10，实际为: {total_value}"
        print(f"✅ 多个并发操作成功，总计值: {total_value}")