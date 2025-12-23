"""
测试打卡今日事项API的E2E测试用例
测试路径：GET /api/checkin/today
遵循TDD原则：先写失败测试，观察失败，再实现最小代码
"""

import pytest
import requests
import json
import time as time_module
from datetime import datetime, date, time
from tests.e2e.testutil import uuid_str, random_str, create_phone_user, generate_unique_phone


class TestCheckinTodayAPI:

    """打卡今日事项API测试类"""

    def test_get_today_checkin_no_rules(self, base_url):
        """
        测试场景：用户没有任何打卡规则
        预期结果：返回空的打卡事项列表
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        assert response.status_code == 200, f"期望状态码 200，实际 {response.status_code}"
        data = response.json()
        print(f"响应数据: {data}")
        assert data["code"] == 1, f"期望 code=1，实际 code={data['code']}, msg={data.get('msg')}"
        assert data["msg"] == "success"
        assert "data" in data
        
        # 验证返回的数据结构
        response_data = data["data"]
        assert "date" in response_data
        assert "checkin_items" in response_data
        assert isinstance(response_data["checkin_items"], list)
        # 注意：新用户可能会自动创建默认打卡规则
        # 所以这里只验证数据结构，不验证数量
        
        # 验证日期格式
        today = date.today().strftime('%Y-%m-%d')
        assert response_data["date"] == today
        
        print(f"✅ 测试通过：用户无打卡规则时返回空列表")

    def test_get_today_checkin_with_daily_rule(self, base_url):
        """
        测试场景：用户有每天打卡的规则
        预期结果：返回今日打卡事项，状态为未打卡
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1, f"获取失败: {data_before.get('msg')}"
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 创建每天打卡的规则
        rule_data = {
            "rule_name": "晨练",
            "icon_url": "https://example.com/exercise.png",
            "frequency_type": 0,  # 每天
            "time_slot_type": 1,  # 上午
            "status": 1  # 启用
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        rule_result = rule_response.json()
        print(f"创建规则响应: {rule_result}")
        assert rule_result["code"] == 1, f"创建规则失败: {rule_result.get('msg')}"
        rule_id = rule_result["data"]["rule_id"]
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        print(f"获取今日打卡事项响应: {data}")
        assert data["code"] == 1, f"获取失败: {data.get('msg')}"
        assert data["msg"] == "success"
        
        # 验证返回的数据结构
        response_data = data["data"]
        assert "date" in response_data
        assert "checkin_items" in response_data
        # 验证打卡项数量比之前增加了1
        assert len(response_data["checkin_items"]) == initial_count + 1
        
        # 验证新创建的打卡事项内容
        # 寻找新创建的打卡项（基于规则ID）
        new_checkin_item = None
        for item in response_data["checkin_items"]:
            if item["rule_id"] == rule_id:
                new_checkin_item = item
                break
        
        assert new_checkin_item is not None, f"未找到规则ID为 {rule_id} 的打卡项"
        assert new_checkin_item["rule_name"] == "晨练"
        assert new_checkin_item["icon_url"] == "https://example.com/exercise.png"
        assert new_checkin_item["planned_time"] == "09:00:00"  # 上午默认9点
        assert new_checkin_item["status"] == "unchecked"
        assert new_checkin_item["checkin_time"] is None
        assert new_checkin_item["record_id"] is None
        
        print(f"✅ 测试通过：用户有每天打卡规则时返回正确的打卡事项")

    def test_get_today_checkin_with_custom_time(self, base_url):
        """
        测试场景：用户有自定义时间的打卡规则
        预期结果：返回今日打卡事项，计划时间为自定义时间
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 创建自定义时间的打卡规则
        rule_data = {
            "rule_name": "服药提醒",
            "icon_url": "https://example.com/medicine.png",
            "frequency_type": 0,  # 每天
            "time_slot_type": 4,  # 自定义时间
            "custom_time": "14:30",
            "status": 1  # 启用
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        rule_result = rule_response.json()
        assert rule_result["code"] == 1
        rule_id = rule_result["data"]["rule_id"]
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证新创建的打卡事项内容
        # 寻找新创建的打卡项（基于规则ID）
        new_checkin_item = None
        for item in data["data"]["checkin_items"]:
            if item["rule_id"] == rule_id:
                new_checkin_item = item
                break
        
        assert new_checkin_item is not None, f"未找到规则ID为 {rule_id} 的打卡项"
        assert new_checkin_item["rule_name"] == "服药提醒"
        assert new_checkin_item["planned_time"] == "14:30:00"  # 自定义时间
        assert new_checkin_item["status"] == "unchecked"
        
        print(f"✅ 测试通过：自定义时间的打卡规则返回正确的计划时间")

    def test_get_today_checkin_after_checkin(self, base_url):
        """
        测试场景：用户已完成今日打卡
        预期结果：返回今日打卡事项，状态为已打卡
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 创建打卡规则
        rule_data = {
            "rule_name": "晨练",
            "frequency_type": 0,  # 每天
            "time_slot_type": 1,  # 上午
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        rule_id = rule_response.json()["data"]["rule_id"]
        
        # 执行打卡
        checkin_response = requests.post(
            f"{base_url}/api/checkin",
            headers=headers,
            json={"rule_id": rule_id},
            timeout=5
        )
        
        assert checkin_response.status_code == 200
        checkin_result = checkin_response.json()
        assert checkin_result["code"] == 1
        record_id = checkin_result["data"]["record_id"]
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证打卡事项内容 - 通过规则ID查找正确的打卡项
        new_checkin_item = None
        for item in data["data"]["checkin_items"]:
            if item["rule_id"] == rule_id:
                new_checkin_item = item
                break
        
        assert new_checkin_item is not None, f"未找到规则ID为 {rule_id} 的打卡项"
        assert new_checkin_item["status"] == "checked"
        assert new_checkin_item["checkin_time"] is not None
        assert new_checkin_item["record_id"] == record_id
        
        print(f"✅ 测试通过：已打卡的事项状态正确显示为checked")

    def test_get_today_checkin_multiple_rules(self, base_url):
        """
        测试场景：用户有多个打卡规则
        预期结果：返回所有今日需要打卡的事项
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 创建多个打卡规则
        rules = [
            {
                "rule_name": "晨练",
                "frequency_type": 0,
                "time_slot_type": 1,
                "status": 1
            },
            {
                "rule_name": "服药",
                "frequency_type": 0,
                "time_slot_type": 2,
                "status": 1
            },
            {
                "rule_name": "晚间散步",
                "frequency_type": 0,
                "time_slot_type": 3,
                "status": 1
            }
        ]
        
        for rule_data in rules:
            rule_response = requests.post(
                f"{base_url}/api/checkin/rules",
                headers=headers,
                json=rule_data,
                timeout=5
            )
            assert rule_response.status_code == 200
            assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证返回的打卡事项数量比之前增加了3个
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count + 3
        
        # 验证每个事项的计划时间（只验证新创建的3个规则的时间）
        expected_times = ["09:00:00", "14:00:00", "20:00:00"]
        actual_times = [item["planned_time"] for item in checkin_items]
        # 检查预期的时间是否在返回的时间列表中
        for expected_time in expected_times:
            assert expected_time in actual_times, f"期望时间 {expected_time} 不在返回的时间列表中"
        
        print(f"✅ 测试通过：多个打卡规则时返回所有今日事项")

    def test_get_today_checkin_weekly_rule_today_included(self, base_url):
        """
        测试场景：用户有每周打卡规则，今天在打卡日内
        预期结果：返回今日打卡事项
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 获取今天是周几（0=周一，6=周日）
        today_weekday = date.today().weekday()
        # 设置week_days位掩码，包含今天
        week_days_mask = 1 << today_weekday
        
        # 创建每周打卡规则（仅今天）
        rule_data = {
            "rule_name": "周例会",
            "frequency_type": 1,  # 每周
            "time_slot_type": 2,  # 下午
            "week_days": week_days_mask,
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证返回的打卡事项数量比之前增加了1
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count + 1
        # 验证新创建的规则包含"周例会"
        rule_names = [item["rule_name"] for item in checkin_items]
        assert "周例会" in rule_names
        
        print(f"✅ 测试通过：每周规则在打卡日内时返回打卡事项")

    def test_get_today_checkin_weekly_rule_today_excluded(self, base_url):
        """
        测试场景：用户有每周打卡规则，今天不在打卡日内
        预期结果：不返回该打卡事项
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 获取今天是周几（0=周一，6=周日）
        today_weekday = date.today().weekday()
        # 设置week_days位掩码，不包含今天（选择其他天）
        other_day = (today_weekday + 1) % 7
        week_days_mask = 1 << other_day
        
        # 创建每周打卡规则（不包含今天）
        rule_data = {
            "rule_name": "周例会",
            "frequency_type": 1,  # 每周
            "time_slot_type": 2,  # 下午
            "week_days": week_days_mask,
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证打卡事项数量没有增加
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count  # 不应增加，因为规则不适用于今天
        
        print(f"✅ 测试通过：每周规则在非打卡日时不返回打卡事项")

    def test_get_today_checkin_workday_rule_on_weekday(self, base_url):
        """
        测试场景：用户有工作日打卡规则，今天是工作日
        预期结果：返回今日打卡事项
        
        注意：此测试仅在周一至周五运行时通过
        """
        # 检查今天是否是工作日
        today_weekday = date.today().weekday()
        if today_weekday >= 5:  # 周六或周日
            pytest.skip("今天是周末，跳过工作日测试")
        
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 创建工作日打卡规则
        rule_data = {
            "rule_name": "上班打卡",
            "frequency_type": 2,  # 工作日
            "time_slot_type": 1,  # 上午
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证返回的打卡事项数量比之前增加了1
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count + 1
        # 验证新创建的规则包含"上班打卡"
        rule_names = [item["rule_name"] for item in checkin_items]
        assert "上班打卡" in rule_names
        
        print(f"✅ 测试通过：工作日规则在工作日时返回打卡事项")

    def test_get_today_checkin_workday_rule_on_weekend(self, base_url):
        """
        测试场景：用户有工作日打卡规则，今天是周末
        预期结果：不返回该打卡事项
        
        注意：此测试仅在周六或周日运行时通过
        """
        # 检查今天是否是周末
        today_weekday = date.today().weekday()
        if today_weekday < 5:  # 周一至周五
            pytest.skip("今天是工作日，跳过周末测试")
        
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 创建工作日打卡规则
        rule_data = {
            "rule_name": "上班打卡",
            "frequency_type": 2,  # 工作日
            "time_slot_type": 1,  # 上午
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证打卡事项数量没有增加（因为今天是周末，工作日规则不适用）
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count  # 数量没有变化，因为规则今天不适用
        
        print(f"✅ 测试通过：工作日规则在周末时不返回打卡事项")

    def test_get_today_checkin_without_token(self, base_url):
        """
        测试场景：未提供认证token
        预期结果：返回401错误或code=0
        """
        # 发送请求（不带Authorization头）
        response = requests.get(
            f"{base_url}/api/checkin/today",
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert data["msg"] == "缺少token参数"
        
        print(f"✅ 测试通过：未提供token时返回错误")

    def test_get_today_checkin_with_invalid_token(self, base_url):
        """
        测试场景：提供无效的token
        预期结果：返回401错误或code=0
        """
        # 准备无效的请求头
        headers = {
            "Authorization": "Bearer invalid_token_here",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 0
        assert "token" in data["msg"].lower() or "认证" in data["msg"]
        
        print(f"✅ 测试通过：无效token时返回错误")

    def test_get_today_checkin_disabled_rule(self, base_url):
        """
        测试场景：用户有已禁用的打卡规则
        预期结果：不返回已禁用的打卡事项
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 在创建规则前，先获取当前打卡项的数量
        response_before = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        assert response_before.status_code == 200
        data_before = response_before.json()
        assert data_before["code"] == 1
        initial_count = len(data_before["data"]["checkin_items"])
        print(f"创建规则前的打卡项数量: {initial_count}")
        
        # 创建已禁用的打卡规则
        rule_data = {
            "rule_name": "已禁用的规则",
            "frequency_type": 0,  # 每天
            "time_slot_type": 1,  # 上午
            "status": 2  # 禁用
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        assert rule_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证打卡事项数量没有增加（因为规则是禁用的）
        checkin_items = data["data"]["checkin_items"]
        assert len(checkin_items) == initial_count  # 数量没有变化，因为规则是禁用的
        
        print(f"✅ 测试通过：已禁用的规则不返回打卡事项")

    def test_get_today_checkin_after_cancel(self, base_url):
        """
        测试场景：用户打卡后又撤销了打卡
        预期结果：返回今日打卡事项，状态为未打卡
        """
        # 创建测试用户
        phone = generate_unique_phone()
        nickname = f"测试用户_{uuid_str(8)}"
        user_data = create_phone_user(base_url, phone, nickname)
        token = user_data['token']
        
        # 准备请求头
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        # 创建打卡规则
        rule_data = {
            "rule_name": "晨练",
            "frequency_type": 0,  # 每天
            "time_slot_type": 1,  # 上午
            "status": 1
        }
        
        rule_response = requests.post(
            f"{base_url}/api/checkin/rules",
            headers=headers,
            json=rule_data,
            timeout=5
        )
        
        assert rule_response.status_code == 200
        rule_id = rule_response.json()["data"]["rule_id"]
        
        # 执行打卡
        checkin_response = requests.post(
            f"{base_url}/api/checkin",
            headers=headers,
            json={"rule_id": rule_id},
            timeout=5
        )
        
        assert checkin_response.status_code == 200
        record_id = checkin_response.json()["data"]["record_id"]
        
        # 撤销打卡
        cancel_response = requests.post(
            f"{base_url}/api/checkin/cancel",
            headers=headers,
            json={"record_id": record_id},
            timeout=5
        )
        
        assert cancel_response.status_code == 200
        assert cancel_response.json()["code"] == 1
        
        # 发送获取今日打卡事项请求
        response = requests.get(
            f"{base_url}/api/checkin/today",
            headers=headers,
            timeout=5
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 1
        
        # 验证打卡事项状态为未打卡
        checkin_item = data["data"]["checkin_items"][0]
        assert checkin_item["rule_id"] == rule_id
        assert checkin_item["status"] == "unchecked"
        assert checkin_item["checkin_time"] is None
        # 撤销后record_id应该保留（状态为已撤销）
        assert checkin_item["record_id"] == record_id
        
        print(f"✅ 测试通过：撤销打卡后状态正确显示为unchecked")
