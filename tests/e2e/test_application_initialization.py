"""
应用初始化E2E测试
验证应用启动后默认社区和超级管理员被正确创建
"""

import pytest
import os
import sys
import json
import requests
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestApplicationInitialization:
    """应用初始化端到端测试"""

    def test_default_community_and_super_admin_created_after_startup(self, test_server):
        """
        测试应用启动后默认社区和超级管理员被正确创建

        这是TDD测试：先写测试，观察失败，然后实现代码
        """
        base_url = test_server


        # 1. 验证默认社区存在
        # 首先尝试通过超级管理员登录获取token
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        }, timeout=5)

        # 验证登录接口响应
        assert login_response.status_code == 200
        login_data = login_response.json()

        # 2. 验证超级管理员账户存在并可以登录
        if login_data.get('code') != 1:
            # 如果登录失败，说明超级管理员不存在，这是预期的失败
            pytest.fail(f"超级管理员账户不存在或无法登录 - 应用初始化未完成。响应: {login_data}")

        # 3. 验证返回的token和用户信息
        assert 'token' in login_data['data']
        assert 'user_id' in login_data['data']
        # Note: role is not returned in login response, need to get user info separately

        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}

        # 4. 验证默认社区存在
        communities_response = requests.get(f'{base_url}/api/communities', headers=headers, timeout=5)
        assert communities_response.status_code == 200
        communities_data = communities_response.json()
        assert communities_data.get('code') == 1

        communities = communities_data['data']
        default_community = None

        for community in communities:
            if community['name'] == '安卡大家庭':
                default_community = community
                break

        # 6. 验证默认社区的属性
        if default_community is None:
            pytest.fail("默认社区 '安卡大家庭' 不存在 - 应用初始化未完成")

        assert default_community['description'] == "系统默认社区，新注册用户自动加入"
        assert default_community['status'] == 1  # 启用状态
        assert default_community['is_default'] is True

        # 7. 验证超级管理员是默认社区的管理员
        staff_response = requests.get(f'{base_url}/api/community/staff/list?community_id={default_community["community_id"]}',
                                     headers=headers, timeout=5)
        assert staff_response.status_code == 200
        staff_data = staff_response.json()
        assert staff_data.get('code') == 1

        staff_members = staff_data['data']['staff_members']
        super_admin_found = False

        # 将 login_data 的 user_id 转换为字符串进行比较
        login_user_id = str(login_data['data']['user_id'])

        for member in staff_members:
            if member['user_id'] == login_user_id and member['role'] == 'manager':
                super_admin_found = True
                break

        assert super_admin_found, "超级管理员不是默认社区的主管"

        # 验证社区的创建者信息
        assert default_community['creator']['user_id'] == login_data['data']['user_id']
        assert default_community['creator']['nickname'] == "系统超级管理员"

        # 验证社区统计信息
        assert default_community['admin_count'] == 1  # 超级管理员
        assert default_community['user_count'] == 0   # 暂无普通用户

        # 8. 验证黑屋社区存在
        blackhouse_community = None
        for community in communities:
            if community['name'] == '黑屋':
                blackhouse_community = community
                break

        # 9. 验证黑屋社区的属性
        if blackhouse_community is None:
            pytest.fail("黑屋社区 '黑屋' 不存在 - 应用初始化未完成")

        assert blackhouse_community['description'] == "特殊管理社区，用户在此社区时功能受限"
        assert blackhouse_community['status'] == 1  # 启用状态
        assert blackhouse_community['is_blackhouse'] is True

        # 10. 验证超级管理员是黑屋社区的管理员
        blackhouse_staff_response = requests.get(f'{base_url}/api/community/staff/list?community_id={blackhouse_community["community_id"]}',
                                                headers=headers, timeout=5)
        assert blackhouse_staff_response.status_code == 200
        blackhouse_staff_data = blackhouse_staff_response.json()
        assert blackhouse_staff_data.get('code') == 1

        blackhouse_staff_members = blackhouse_staff_data['data']['staff_members']
        blackhouse_super_admin_found = False

        for member in blackhouse_staff_members:
            if member['user_id'] == login_user_id and member['role'] == 'manager':
                blackhouse_super_admin_found = True
                break

        assert blackhouse_super_admin_found, "超级管理员不是黑屋社区的主管"

        # 验证黑屋社区的创建者信息
        assert blackhouse_community['creator']['user_id'] == login_data['data']['user_id']
        assert blackhouse_community['creator']['nickname'] == "系统超级管理员"

        # 验证黑屋社区统计信息
        assert blackhouse_community['admin_count'] == 1  # 超级管理员
        assert blackhouse_community['user_count'] == 0   # 初始时没有任何用户

        print("✅ 应用初始化测试通过：默认社区、黑屋社区和超级管理员已正确创建")