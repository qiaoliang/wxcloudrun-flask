"""
社区打卡规则API的E2E测试用例
测试 /api/community-checkin/rules 相关接口

遵循TDD原则：先写失败测试，观察失败，再实现最小代码
遵循测试反模式原则：测试真实行为，而非mock行为
"""

import pytest
import requests
import json
import time
import os
import sys
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from hashutil import random_str, uuid_str

# 导入测试工具函数
from .testutil import get_headers_by_creating_phone_user, create_phone_user, TEST_DEFAULT_SMS_CODE, TEST_DEFAULT_PWD, TEST_DEFAULT_WXCAHT_CODE


class TestCommunityCheckinRulesAPI:
    """社区打卡规则API测试类"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1, f"登录失败: {login_data.get('msg')}"
        return login_data['data']['token'], login_data['data']['user_id']
    def _create_community_and_admin_headers(self,base_url):
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }

        # 2. 准备社区数据
        timestamp = int(time.time())
        community_data = {
            'name': f'测试社区_{uuid_str(16)}',
            'location': f'测试地址_{uuid_str(16)}',
            'description': f'这是一个测试社区的描述_{uuid_str(16)}',
            'manager_id': super_admin_id,
            'location_lat': 39.9042,
            'location_lon': 116.4074
        }

        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1, "创建社区失败"
        return admin_headers,data['data']

    def test_get_rules_requires_authentication(self, test_server):
        """测试获取规则列表需要认证"""
        base_url = test_server

        # 未认证的请求应该失败
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id=1")
        assert response.status_code == 200  # API返回200状态码，但业务code为0
        data = response.json()
        assert data.get('code') == 0, "未认证请求应该失败"
        assert 'token' in data.get('msg', '').lower() or '认证' in data.get('msg', ''), "错误消息应该提到认证"

    def test_get_rules_requires_community_permission(self, test_server):
        """测试获取规则列表需要社区管理权限"""
        base_url = test_server

        # 创建普通用户（非社区管理员）
        phone = f"138{random_str(8)}"
        nickname = f"普通用户_{random_str(6)}"
        user_data = create_phone_user(base_url, phone, nickname)
        user_token = user_data['token']

        headers = {
            "Authorization": f"Bearer {user_token}",
            "Content-Type": "application/json"
        }

        # 尝试获取不存在的社区的规则
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id=999", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0, "无权限访问应该失败"
        assert '权限' in data.get('msg', '') or 'permission' in data.get('msg', '').lower(), "错误消息应该提到权限"

    def test_create_and_get_rules_workflow(self, test_server):
        """测试完整的规则创建和获取流程"""
        # 创建社区和社区管理员

        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)

        # 1. 尝试创建规则（应该失败，因为用户可能没有社区管理权限）
        rule_data = {
            "community_id": 999,  # 不存在的社区
            "rule_name": f"测试规则_{random_str(6)}",
            "icon_url": "https://example.com/icon.png",
            "frequency_type": 0,  # 每日
            "time_slot_type": 4,  # 自定义时间
            "custom_time": "09:00:00",
            "custom_start_date": "2025-01-01",
            "custom_end_date": "2025-12-31",
            "week_days": 127  # 每天
        }

        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data,
                                headers=auth_headers)
        assert response.status_code == 200
        create_data = response.json()

        assert create_data.get('code') == 0, f"创建规则应该失败，但返回了: {create_data.get('msg')}"
        assert '社区' in create_data.get('msg', '') or '权限' in create_data.get('msg', '') or 'community' in create_data.get('msg', '').lower(), f"错误消息应该提到社区或权限: {create_data.get('msg')}"


    def test_update_rule(self, test_server):
        """测试修改规则"""
        base_url = test_server
        # 先创建一个规则
        auth_headers, commu,a_rule=self._create_header_and_commu_and_a_rule(base_url)

        # 修改规则
        a_rule["rule_name"] = f"更新后的规则_{random_str(6)}"

        response = requests.put(f"{base_url}/api/community-checkin/rules/{a_rule["community_rule_id"]}",
                               json=a_rule,
                               headers=auth_headers)
        assert response.status_code == 200
        update_response = response.json()
        assert update_response.get('code') == 1, f"修改规则失败: {update_response.get('msg')}"

        # 验证规则已更新
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=auth_headers)
        assert response.status_code == 200
        detail_data = response.json()

        rule_detail = detail_data['data']
        assert rule_detail['rule_name'] == a_rule['rule_name'], "规则名称应该已更新"
        assert rule_detail['icon_url'] == a_rule['icon_url'], "图标URL应该已更新"
        assert rule_detail['frequency_type'] == a_rule['frequency_type'], "频率类型应该已更新"
        assert rule_detail['time_slot_type'] == a_rule['time_slot_type'], "时间段类型应该已更新"

    def test_enable_and_disable_rule(self, test_server):
        """测试启用和停用规则"""
        base_url = test_server
        # 先创建一个规则
        header,commu,a_new_rule= self._create_header_and_commu_and_a_rule(test_server)
        rule_id = a_new_rule["community_rule_id"]
        # 1. 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=header)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, f"启用规则失败: {enable_data.get('msg')}"
        assert enable_data['data']['is_enabled'] == True, "规则应该已启用"

        # 验证规则状态
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=header)
        assert response.status_code == 200
        detail_data = response.json()
        assert detail_data['data']['is_enabled'] == True, "规则详情应该显示已启用"

        # 2. 停用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/disable",
                                headers=header)
        assert response.status_code == 200
        disable_data = response.json()
        assert disable_data.get('code') == 1, f"停用规则失败: {disable_data.get('msg')}"
        assert disable_data['data']['is_enabled'] == False, "规则应该已停用"

        # 验证规则状态
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=header)
        assert response.status_code == 200
        detail_data = response.json()
        assert detail_data['data']['is_enabled'] == False, "规则详情应该显示已停用"

    def test_cannot_update_enabled_rule(self, test_server):
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)
        """测试不能修改已启用的规则"""
        base_url = test_server

        # 创建并启用一个规则
        rule_id = self.test_create_and_get_rules_workflow(test_server)

        # 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=auth_headers)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, "启用规则应该成功"

        # 尝试修改已启用的规则
        update_data = {
            "rule_name": f"尝试修改已启用规则_{random_str(6)}"
        }

        response = requests.put(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               json=update_data,
                               headers=auth_headers)
        assert response.status_code == 200
        update_response = response.json()
        assert update_response.get('code') == 0, "修改已启用的规则应该失败"
        assert '启用' in update_response.get('msg', '') or 'enabled' in update_response.get('msg', '').lower(), "错误消息应该提到规则已启用"

    def test_delete_rule(self, test_server):
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)
        """测试删除规则（仅限未启用状态）"""
        base_url = test_server

        # 创建一个规则（未启用状态）
        rule_id = self.test_create_and_get_rules_workflow(test_server)

        # 删除规则
        response = requests.delete(f"{base_url}/api/community-checkin/rules/{rule_id}",
                                  headers=auth_headers)
        assert response.status_code == 200
        delete_data = response.json()
        assert delete_data.get('code') == 1, f"删除规则失败: {delete_data.get('msg')}"

        # 验证规则已删除（获取详情应该失败）
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=auth_headers)
        assert response.status_code == 200
        detail_data = response.json()
        assert detail_data.get('code') == 0, "已删除的规则不应该能获取到详情"
        assert '不存在' in detail_data.get('msg', '') or 'not found' in detail_data.get('msg', '').lower(), "错误消息应该提到规则不存在"

    def test_cannot_delete_enabled_rule(self, test_server):
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)
        """测试不能删除已启用的规则"""
        base_url = test_server

        # 创建并启用一个规则
        rule_id = self.test_create_and_get_rules_workflow(test_server)

        # 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=auth_headers)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, "启用规则应该成功"

        # 尝试删除已启用的规则
        response = requests.delete(f"{base_url}/api/community-checkin/rules/{rule_id}",
                                  headers=auth_headers)
        assert response.status_code == 200
        delete_data = response.json()
        assert delete_data.get('code') == 0, "删除已启用的规则应该失败"
        assert '启用' in delete_data.get('msg', '') or 'enabled' in delete_data.get('msg', '').lower(), "错误消息应该提到规则已启用"

    def test_get_rules_with_include_disabled(self, test_server):
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)
        """测试获取规则列表时包含已禁用的规则"""
        base_url = test_server

        # 创建两个规则
        self._create_header_and_commu_and_a_rule(test_server, auth_headers)
        rule1_id = self.test_create_and_get_rules_workflow(test_server)

        # 创建第二个规则并禁用它
        rule_data2 = {
            "community_id": 1,
            "rule_name": f"测试规则2_{random_str(6)}",
            "icon_url": "https://example.com/icon2.png",
            "frequency_type": 1,  # 每周
            "time_slot_type": 2,  # 下午
            "custom_time": "14:00:00",
            "week_days": 2  # 周二
        }

        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data2,
                                headers=auth_headers)
        assert response.status_code == 200
        create_data2 = response.json()
        rule2_id = create_data2['data']['community_rule_id']

        # 启用然后禁用第二个规则
        requests.post(f"{base_url}/api/community-checkin/rules/{rule2_id}/enable", headers=auth_headers)
        requests.post(f"{base_url}/api/community-checkin/rules/{rule2_id}/disable", headers=auth_headers)

        # 1. 获取不包含已禁用规则的列表
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id=1&include_disabled=false",
                               headers=auth_headers)
        assert response.status_code == 200
        list_data = response.json()
        rules = list_data['data']

        # 应该只包含未禁用的规则
        enabled_rules = [r for r in rules if r['is_enabled'] == True]
        assert len(enabled_rules) == 0, "没有启用的规则"

        # 2. 获取包含已禁用规则的列表
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id=1&include_disabled=true",
                               headers=auth_headers)
        assert response.status_code == 200
        list_data_all = response.json()
        rules_all = list_data_all['data']

        # 应该包含所有规则
        assert len(rules_all) >= 2, "应该包含所有规则"

        # 找到已禁用的规则
        disabled_rules = [r for r in rules_all if r['is_enabled'] == False]
        assert len(disabled_rules) >= 1, "应该包含已禁用的规则"

    def _create_header_and_commu_and_a_rule(self, base_url,rule_data=None):
        """测试创建规则的参数验证"""
        auth_headers, commu=self._create_community_and_admin_headers(base_url)
        test_data={
            "rule_name": f"rule_{uuid_str(16)}",
            "icon_url": "...",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "09:00:00",
            "custom_start_date": "2025-01-01",
            "custom_end_date": "2025-12-31",
            "week_days": 127
        }
        if rule_data is None:
            rule_data=test_data
        rule_data["community_id"]=commu['community_id']

        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data,
                                headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert result.get('code') == 1
        a_rule= result['data']
        return auth_headers,commu, a_rule
    def test_create_rule_successfully(self, test_server):
        base_url = test_server
        auth_headers, commu=self._create_community_and_admin_headers(test_server)

        """测试创建规则的参数验证"""
        base_url = test_server
        test_data={
            "community_id": commu['community_id'],
            "rule_name": "每日健康打卡",
            "icon_url": "...",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "09:00:00",
            "custom_start_date": "2025-01-01",
            "custom_end_date": "2025-12-31",
            "week_days": 127
        }
        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=test_data,
                                headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert "创建社区规则成功" in data.get('msg', '')
        assert data['data']['community_rule_id'] is 1
    def test_rule_detail_permission(self, test_server):
        """测试规则详情的权限控制"""
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)

        # 创建一个规则
        rule_data={
            "community_id": commu['community_id'],
            "rule_name": f"rule_{uuid_str(10)}",
            "icon_url": "...",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "09:00:00",
            "custom_start_date": "2025-01-01",
            "custom_end_date": "2025-12-31",
        }
        # 使用现有的方法创建规则
        header, commu_created, a_rule = self._create_header_and_commu_and_a_rule(test_server, rule_data)
        rule_id = a_rule['community_rule_id']

        # 创建另一个普通用户
        phone = f"139{random_str(8)}"
        nickname = f"其他用户_{random_str(6)}"
        other_headers,_ = get_headers_by_creating_phone_user(base_url, phone, nickname)

        # 其他用户尝试获取规则详情（应该失败，因为不属于该社区）
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=other_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0, "其他用户不应该能访问不属于自己社区的规则"
        assert '权限' in data.get('msg', '') or 'permission' in data.get('msg', '').lower(), "错误消息应该提到权限"

    def test_complete_rule_lifecycle(self, test_server):
        base_url = test_server
        auth_headers, commu = self._create_community_and_admin_headers(base_url)
        """测试完整的规则生命周期"""
        base_url = test_server

        print("\n=== 开始测试完整的规则生命周期 ===")

        # 1. 创建规则
        rule_data = {
            "community_id": 1,
            "rule_name": f"生命周期测试规则_{random_str(6)}",
            "icon_url": "https://example.com/lifecycle.png",
            "frequency_type": 0,
            "time_slot_type": 4,
            "custom_time": "08:00:00",
            "week_days": 127
        }

        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data,
                                headers=auth_headers)
        assert response.status_code == 200
        create_data = response.json()
        assert create_data.get('code') == 1, "创建规则失败"
        rule_id = create_data['data']['community_rule_id']
        print(f"✓ 规则创建成功，ID: {rule_id}")

        # 2. 修改规则
        update_data = {
            "rule_name": f"更新后的规则_{random_str(6)}",
            "icon_url": "https://example.com/updated.png"
        }

        response = requests.put(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               json=update_data,
                               headers=auth_headers)
        assert response.status_code == 200
        update_data = response.json()
        assert update_data.get('code') == 1, "修改规则失败"
        print("✓ 规则修改成功")

        # 3. 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=auth_headers)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, "启用规则失败"
        print("✓ 规则启用成功")

        # 4. 停用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/disable",
                                headers=auth_headers)
        assert response.status_code == 200
        disable_data = response.json()
        assert disable_data.get('code') == 1, "停用规则失败"
        print("✓ 规则停用成功")

        # 5. 删除规则（现在规则已停用，可以删除）
        response = requests.delete(f"{base_url}/api/community-checkin/rules/{rule_id}",
                                  headers=auth_headers)
        assert response.status_code == 200
        delete_data = response.json()
        assert delete_data.get('code') == 1, "删除规则失败"
        print("✓ 规则删除成功")

        print("=== 完整的规则生命周期测试完成 ===")