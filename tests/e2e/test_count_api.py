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