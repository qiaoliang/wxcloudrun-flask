"""
社区功能E2E测试 - TDD版本
使用test_server fixture，遵循TDD原则
"""

import pytest
import requests
from datetime import datetime


class TestCommunityE2E:
    """社区功能端到端测试"""
    
    def test_get_communities_list_with_super_admin(self, test_server):
        """
        测试超级管理员获取社区列表
        RED: 首先写这个测试，预期它失败
        """
        base_url = test_server
        
        # 1. 超级管理员登录
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        
        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. 获取社区列表
        response = requests.get(f'{base_url}/api/communities', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        
        communities = data['data']
        assert len(communities) >= 1
        
        # 3. 验证默认社区存在
        default_community = None
        for community in communities:
            if community['name'] == '安卡大家庭':
                default_community = community
                break
        
        assert default_community is not None
        assert default_community['is_default'] is True
        assert default_community['description'] == "系统默认社区，新注册用户自动加入"
        assert default_community['status'] == 1
        assert default_community['status_name'] == 'enabled'
    
    def test_create_community_as_super_admin(self, test_server):
        """
        测试超级管理员创建社区
        RED: 这个测试应该先失败，因为创建社区的API可能还没有实现
        """
        base_url = test_server
        
        # 1. 超级管理员登录
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        
        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. 创建新社区
        response = requests.post(f'{base_url}/api/communities', 
            headers=headers,
            json={
                'name': 'TDD测试社区',
                'description': '用于TDD测试的社区',
                'location': '北京市'
            }
        )
        
        # 这个测试预期失败，因为API可能还没有实现
        # 或者API的响应格式与文档不符
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        
        community = data['data']
        assert community['name'] == 'TDD测试社区'
        assert community['description'] == '用于TDD测试的社区'
        assert community['location'] == '北京市'
        assert community['is_default'] is False
    
    def test_normal_user_permission_denied(self, test_server):
        """
        测试普通用户权限被拒绝
        RED: 普通用户不应该能访问社区管理API
        """
        base_url = test_server
        
        # 1. 创建普通用户
        register_response = requests.post(f'{base_url}/api/auth/register_phone', json={
            'phone': '13800138000',
            'code': '123456',
            'password': 'Test123456',
            'nickname': '普通用户'
        })
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert register_data.get('code') == 1
        
        token = register_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. 普通用户尝试获取社区列表（应该被拒绝）
        response = requests.get(f'{base_url}/api/communities', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 业务错误
        assert '权限不足' in data['msg'] or '需要超级管理员权限' in data['msg']
        
        # 3. 普通用户尝试创建社区（应该被拒绝）
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '非法社区',
                'description': '普通用户不应该能创建社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '权限不足' in data['msg'] or '需要超级管理员权限' in data['msg']
    
    def test_create_community_validation_errors(self, test_server):
        """
        测试创建社区的参数验证
        REFACTOR: 添加更多边界条件测试
        """
        base_url = test_server
        
        # 1. 超级管理员登录
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        
        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        
        # 2. 测试空名称
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'description': '没有名称的社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区名称不能为空' in data['msg']
        
        # 3. 测试重复名称
        # 首先创建一个社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '重复测试社区',
                'description': '第一个社区'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1
        
        # 尝试创建同名社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '重复测试社区',
                'description': '第二个社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区名称已存在' in data['msg']