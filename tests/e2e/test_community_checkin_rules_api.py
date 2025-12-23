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

from hashutil import random_str, uuid_str, generate_unique_phone
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
# 导入测试工具函数
from tests.e2e.testutil import get_headers_by_creating_phone_user, create_phone_user, TEST_DEFAULT_SMS_CODE, TEST_DEFAULT_PWD, TEST_DEFAULT_WXCAHT_CODE


class TestCommunityCheckinRulesAPI:

    def setup_method(self):
        """每个测试方法前的设置：启动 Flask 应用"""
        import os
        import sys
        import time
        import subprocess
        import requests
        
        # 设置环境变量
        os.environ['ENV_TYPE'] = 'function'
        
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

    def test_get_rules_requires_authentication(self):
        """测试获取规则列表需要认证"""
        base_url = self.base_url

        # 未认证的请求应该失败
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id=1")
        assert response.status_code == 200  # API返回200状态码，但业务code为0
        data = response.json()
        assert data.get('code') == 0, "未认证请求应该失败"
        assert 'token' in data.get('msg', '').lower() or '认证' in data.get('msg', ''), "错误消息应该提到认证"

    def test_get_rules_requires_community_permission(self):
        """测试获取规则列表需要社区管理权限"""
        base_url = self.base_url

        # 创建普通用户（非社区管理员）
        phone = generate_unique_phone()
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

    def test_create_and_get_rules_workflow(self):
        """测试完整的规则创建和获取流程"""
        # 创建社区和社区管理员

        base_url = self.base_url
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


    def test_update_rule(self):
        """测试修改规则"""
        base_url = self.base_url
        # 先创建一个规则
        auth_headers, commu,a_rule=self._create_header_and_commu_and_a_rule(base_url)

        # 修改规则 - 只发送需要更新的字段
        update_data = {
            "rule_name": f"更新后的规则_{random_str(6)}",
            "icon_url": "https://example.com/updated-icon.png",
            "frequency_type": 1,
            "time_slot_type": 2
        }
        rule_id =a_rule["community_rule_id"]
        response = requests.put(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               json=update_data,
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
        assert rule_detail['rule_name'] == update_data['rule_name'], "规则名称应该已更新"
        assert rule_detail['icon_url'] == update_data['icon_url'], "图标URL应该已更新"
        assert rule_detail['frequency_type'] == update_data['frequency_type'], "频率类型应该已更新"
        assert rule_detail['time_slot_type'] == update_data['time_slot_type'], "时间段类型应该已更新"

    def test_enable_and_disable_rule(self):
        """测试启用和停用规则"""
        base_url = self.base_url
        # 先创建一个规则
        header,commu,a_new_rule= self._create_header_and_commu_and_a_rule(self.base_url)
        rule_id = a_new_rule["community_rule_id"]
        # 1. 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=header)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, f"启用规则失败: {enable_data.get('msg')}"
        assert enable_data['data']['status'] == 1, "规则应该已启用 (status=1)"

        # 验证规则状态
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=header)
        assert response.status_code == 200
        detail_data = response.json()
        assert detail_data['data']['status'] == 1, "规则详情应该显示已启用 (status=1)"

        # 2. 停用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/disable",
                                headers=header)
        assert response.status_code == 200
        disable_data = response.json()
        assert disable_data.get('code') == 1, f"停用规则失败: {disable_data.get('msg')}"
        assert disable_data['data']['status'] == 0, "规则应该已停用 (status=0)"

        # 验证规则状态
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=header)
        assert response.status_code == 200
        detail_data = response.json()
        assert detail_data['data']['status'] == 0, "规则详情应该显示已停用 (status=0)"

    def test_cannot_update_enabled_rule(self):
        """测试不能修改已启用的规则"""
        base_url = self.base_url

        # 创建并启用一个规则
        header,comm,a_rule = self._create_header_and_commu_and_a_rule(self.base_url)
        rule_id = a_rule["community_rule_id"]
        # 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=header)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, "启用规则应该成功"

        # 尝试修改已启用的规则
        update_data = {
            "rule_name": f"尝试修改已启用规则_{random_str(6)}"
        }

        response = requests.put(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               json=update_data,
                               headers=header)
        assert response.status_code == 200
        update_response = response.json()
        assert update_response.get('code') == 0, "修改已启用的规则应该失败"
        assert '启用' in update_response.get('msg', '') or 'enabled' in update_response.get('msg', '').lower(), "错误消息应该提到规则已启用"

    def test_delete_rule(self):
        base_url = self.base_url

        # 创建一个规则（未启用状态）
        header,comm,a_rule = self._create_header_and_commu_and_a_rule(self.base_url)
        rule_id = a_rule["community_rule_id"]

        # 删除规则
        response = requests.delete(f"{base_url}/api/community-checkin/rules/{rule_id}",
                                  headers=header)
        assert response.status_code == 200
        delete_data = response.json()
        assert delete_data.get('code') == 1, f"删除规则失败: {delete_data.get('msg')}"
        assert delete_data.get('msg') == "删除社区规则成功"

        # 验证规则已删除（获取详情应该失败）
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=header)
        assert response.status_code == 200
        detail_data = response.json()
        # 已删除的规则状态应该为 2，表示已删除
        assert detail_data.get('code') == 0, "已删除的规则不应该能获取到详情"
        assert detail_data.get('msg') == "此规则已删除"


    def test_cannot_delete_enabled_rule(self):
        """测试不能删除已启用的规则"""
        base_url = self.base_url

        # 创建并启用一个规则
        header,comm,a_rule = self._create_header_and_commu_and_a_rule(self.base_url)
        rule_id = a_rule["community_rule_id"]
        # 启用规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule_id}/enable",
                                headers=header)
        assert response.status_code == 200
        enable_data = response.json()
        assert enable_data.get('code') == 1, "启用规则应该成功"

        # 尝试删除已启用的规则
        response = requests.delete(f"{base_url}/api/community-checkin/rules/{rule_id}",
                                  headers=header)
        assert response.status_code == 200
        delete_data = response.json()
        assert delete_data.get('code') == 0, "删除已启用的规则应该失败"
        assert '启用' in delete_data.get('msg', '') or 'enabled' in delete_data.get('msg', '').lower(), "错误消息应该提到规则已启用"

    def test_get_rules_with_include_disabled(self):
        """测试获取规则列表时包含已禁用的规则"""
        base_url = self.base_url
        header, comm, a_rule = self._create_header_and_commu_and_a_rule(base_url)
        comm_id = comm['community_id']
        rule1_id = a_rule["community_rule_id"]
        
        # 创建规则前先获取当前社区的规则数量
        response_before = requests.get(f"{base_url}/api/community-checkin/rules?community_id={comm_id}&include_disabled=true",
                               headers=header)
        assert response_before.status_code == 200
        list_data_before = response_before.json()
        assert list_data_before.get('code') == 1, f"获取规则列表失败: {list_data_before.get('msg')}"
        rules_before = list_data_before['data']['rules']
        initial_rule_count = len(rules_before)
        print(f"创建规则前的规则数量: {initial_rule_count}")
        
        # 创建第二个规则
        rule_data2 = {
            "community_id": comm_id,
            "rule_name": f"测试规则2_{random_str(6)}",
            "icon_url": "https://example.com/icon2.png",
            "frequency_type": 1,  # 每周
            "time_slot_type": 2,  # 下午
            "custom_time": "14:00:00",
            "week_days": 2  # 周二
        }

        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data2,
                                headers=header)
        assert response.status_code == 200
        create_data2 = response.json()
        rule2_id = create_data2['data']['community_rule_id']
        rule2_comm_id = create_data2['data']['community_id']
        assert rule2_comm_id == int(comm_id), "创建规则2应该成功"
        assert create_data2['data']['status'] == 0, "创建的规则2应该未启用"
        
        # 使用API验证规则数量，而不是直接调用服务层
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id={comm_id}&include_disabled=true",
                               headers=header)
        assert response.status_code == 200
        list_data = response.json()
        assert list_data.get('code') == 1, f"获取规则列表失败: {list_data.get('msg')}"
        rules = list_data['data']['rules']
        # 验证规则数量比之前增加了2个（我们创建了2个规则）
        assert len(rules) == initial_rule_count + 2, f"应该有{initial_rule_count + 2}个规则，实际有{len(rules)}个"
        
        # 启用第一个规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule1_id}/enable", headers=header)
        res_data = response.json()
        assert res_data.get('code') == 1, "启用规则1应该成功"
        assert res_data.get('msg') == "规则已启用"
        assert res_data.get('data')['status'] == 1
        assert res_data.get('data')['community_id'] == int(comm_id)
        
        # 获取启用的规则列表
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id={comm_id}&include_disabled=False",
                               headers=header)
        assert response.status_code == 200
        list_data = response.json()
        assert list_data.get('code') == 1, f"获取规则列表失败: {list_data.get('msg')}"
        rules = list_data['data']['rules']
        # 获取启用的规则
        enabled_rules = [r for r in rules if r['status'] == 1]
        # 验证启用的规则数量比之前增加了1个
        expected_enabled_count = len([r for r in rules_before if r['status'] == 1]) + 1
        assert len(enabled_rules) == expected_enabled_count, f"应该有{expected_enabled_count}个启用的规则，实际有{len(enabled_rules)}个"

        # 启用然后禁用第二个规则
        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule2_id}/enable", headers=header)
        res_data = response.json()
        assert res_data.get('code') == 1, "启用规则2应该成功"

        response = requests.post(f"{base_url}/api/community-checkin/rules/{rule2_id}/disable", headers=header)
        res_data = response.json()
        assert res_data.get('code') == 1, "禁用规则2应该成功"


        # 1. 获取不包含已禁用规则的列表
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id={comm['community_id']}&include_disabled=false",
                               headers=header)
        assert response.status_code == 200
        list_data = response.json()
        rules = list_data['data']['rules']

        # 应该只包含启用的规则 (status=1)
        # 验证启用规则的数量
        expected_enabled_count = len([r for r in rules_before if r['status'] == 1]) + 1  # rule1被启用
        assert len(rules) == expected_enabled_count, f"应该有{expected_enabled_count}个启用的规则，实际有{len(rules)}个"

        # 2. 获取包含已禁用规则的列表
        response = requests.get(f"{base_url}/api/community-checkin/rules?community_id={comm['community_id']}&include_disabled=true",
                               headers=header)
        assert response.status_code == 200
        list_data_all = response.json()
        rules_all = list_data_all['data']['rules']

        # 应该包含所有规则（包括停用的）
        assert len(rules_all) == initial_rule_count + 2, f"应该包含{initial_rule_count + 2}个规则，实际有{len(rules_all)}个"

        # 找到已禁用的规则 (status=0)
        disabled_rules = [r for r in rules_all if r['status'] == 0]
        expected_disabled_count = len([r for r in rules_before if r['status'] == 0]) + 1  # rule2被禁用
        assert len(disabled_rules) == expected_disabled_count, f"应该有{expected_disabled_count}个已禁用的规则，实际有{len(disabled_rules)}个"

        # 找到启用的规则 (status=1)
        enabled_rules = [r for r in rules_all if r['status'] == 1]
        assert len(enabled_rules) == expected_enabled_count, f"应该有{expected_enabled_count}个启用的规则，实际有{len(enabled_rules)}个"

    def _create_header_and_commu_and_a_rule(self, base_url,rule_data=None):
        """创建规则的参数验证"""
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
        assert rule_data['rule_name'] is not None, "规则名称不能为空"
        response = requests.post(f"{base_url}/api/community-checkin/rules",
                                json=rule_data,
                                headers=auth_headers)
        assert response.status_code == 200
        result = response.json()
        assert result.get('code') == 1
        a_rule= result['data']
        return auth_headers,commu, a_rule
    def test_create_rule_successfully(self):
        base_url = self.base_url
        auth_headers, commu=self._create_community_and_admin_headers(self.base_url)

        """测试创建规则的参数验证"""
        base_url = self.base_url
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
        assert data['data']['community_rule_id'] is not None  # 只检查ID存在，不检查具体值
    def test_rule_detail_permission(self):
        """测试规则详情的权限控制"""
        base_url = self.base_url
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
        header, commu_created, a_rule = self._create_header_and_commu_and_a_rule(self.base_url, rule_data)
        rule_id = a_rule['community_rule_id']

        # 创建另一个普通用户
        phone = generate_unique_phone()
        nickname = f"其他用户_{random_str(6)}"
        other_headers,_ = get_headers_by_creating_phone_user(base_url, phone, nickname)

        # 其他用户尝试获取规则详情（应该失败，因为不属于该社区）
        response = requests.get(f"{base_url}/api/community-checkin/rules/{rule_id}",
                               headers=other_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0, "其他用户不应该能访问不属于自己社区的规则"
        assert '权限' in data.get('msg', '') or 'permission' in data.get('msg', '').lower(), "错误消息应该提到权限"