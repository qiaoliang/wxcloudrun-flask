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
        
        # 1. 验证应用健康状态
        response = requests.get(f'{base_url}/api/count', timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1  # 成功响应 (code=1表示成功)
        
        # 2. 验证默认社区存在
        # 首先尝试通过超级管理员登录获取token
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        }, timeout=5)
        
        # 验证登录接口响应
        assert login_response.status_code == 200
        login_data = login_response.json()
        
        # 3. 验证超级管理员账户存在并可以登录
        if login_data.get('code') != 1:
            # 如果登录失败，说明超级管理员不存在，这是预期的失败
            pytest.fail(f"超级管理员账户不存在或无法登录 - 应用初始化未完成。响应: {login_data}")
        
        # 4. 验证返回的token和用户信息
        assert 'token' in login_data['data']
        assert 'user_id' in login_data['data']
        # Note: role is not returned in login response, need to get user info separately
        
        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 5. 验证默认社区存在
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
        
        staff = staff_data['data']
        super_admin_found = False
        
        for member in staff:
            if member['user_id'] == login_data['data']['user_id'] and member['role'] == 'manager':
                super_admin_found = True
                break
        
        assert super_admin_found, "超级管理员不是默认社区的主管"
        
        # 验证社区的创建者信息
        assert default_community['creator']['user_id'] == login_data['data']['user_id']
        assert default_community['creator']['nickname'] == "系统超级管理员"
        
        # 验证社区统计信息
        assert default_community['admin_count'] == 1  # 超级管理员
        assert default_community['user_count'] == 0   # 暂无普通用户
        
        print("✅ 应用初始化测试通过：默认社区和超级管理员已正确创建")