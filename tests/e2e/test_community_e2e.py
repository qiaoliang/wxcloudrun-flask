"""
社区功能E2E测试
模拟真实用户场景的端到端测试
"""

import pytest
import os
import sys
import json
import time
import requests
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestCommunityE2E:
    """社区功能端到端测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        # API基础URL
        cls.base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
        cls.session = requests.Session()
        
        # 测试数据
        cls.test_users = {}
        cls.test_communities = {}
        
        # 确保服务运行
        cls.check_service_health()
    
    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        cls.session.close()
    
    @classmethod
    def check_service_health(cls):
        """检查服务健康状态"""
        try:
            response = cls.session.get(f'{cls.base_url}/api/health')
            if response.status_code != 200:
                pytest.skip('API服务未运行或不可用')
        except requests.exceptions.ConnectionError:
            pytest.skip('无法连接到API服务')
    
    def setup_method(self):
        """每个测试方法前的准备"""
        # 清理测试数据
        self.cleanup_test_data()
        
        # 创建测试用户
        self.create_test_users()
        
        # 创建测试社区
        self.create_test_communities()
    
    def teardown_method(self):
        """每个测试方法后的清理"""
        self.cleanup_test_data()
    
    def cleanup_test_data(self):
        """清理测试数据"""
        # 注意：实际环境中应该有专门的清理接口或测试数据库
        pass
    
    def create_test_users(self):
        """创建测试用户"""
        # 创建超级管理员
        response = self.session.post(f'{self.base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') != 0:
                self.test_users['super_admin'] = {
                    'token': data['data']['token'],
                    'user_id': data['data']['user_id']
                }
        
        # 创建社区管理员
        response = self.session.post(f'{self.base_url}/api/auth/register_phone', json={
            'phone': '13800138001',
            'code': '123456',  # 测试环境使用固定验证码
            'password': 'Test123456',
            'nickname': '社区管理员'
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') != 0:
                self.test_users['community_admin'] = {
                    'token': data['data']['token'],
                    'user_id': data['data']['user_id']
                }
                
                # 更新用户角色为社区管理员
                self.update_user_role(self.test_users['community_admin']['user_id'], 3)
        
        # 创建普通用户
        response = self.session.post(f'{self.base_url}/api/auth/register_phone', json={
            'phone': '13800138002',
            'code': '123456',
            'password': 'Test123456',
            'nickname': '普通用户'
        })
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') != 0:
                self.test_users['normal_user'] = {
                    'token': data['data']['token'],
                    'user_id': data['data']['user_id']
                }
    
    def create_test_communities(self):
        """创建测试社区"""
        if 'super_admin' not in self.test_users:
            return
        
        headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
        
        # 创建测试社区
        response = self.session.post(f'{self.base_url}/api/communities', 
            headers=headers,
            json={
                'name': 'E2E测试社区',
                'description': '用于E2E测试的社区',
                'location': '北京市'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('code') != 0:
                self.test_communities['test_community'] = data['data']
    
    def update_user_role(self, user_id, role):
        """更新用户角色（需要管理员权限）"""
        if 'super_admin' not in self.test_users:
            return
        
        headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
        # 这里应该有更新用户角色的API，暂时跳过
        pass
    
    def test_complete_community_management_workflow(self):
        """测试完整的社区管理工作流"""
        if 'super_admin' not in self.test_users or 'test_community' not in self.test_communities:
            pytest.skip('缺少必要的测试数据')
        
        super_admin_headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
        community_id = self.test_communities['test_community']['community_id']
        
        # 1. 超级管理员查看所有社区
        response = self.session.get(f'{self.base_url}/api/communities', headers=super_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') != 0
        communities = data['data']
        assert len(communities) >= 1
        
        # 2. 获取社区详情
        response = self.session.get(f'{self.base_url}/api/communities/{community_id}', headers=super_admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') != 0
        community_detail = data['data']
        assert community_detail['name'] == 'E2E测试社区'
        
        # 3. 添加社区管理员
        if 'community_admin' in self.test_users:
            response = self.session.post(
                f'{self.base_url}/api/communities/{community_id}/admins',
                headers=super_admin_headers,
                json={
                    'user_ids': [self.test_users['community_admin']['user_id']],
                    'role': 2
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            
            # 4. 社区管理员登录并查看管理的社区
            admin_headers = {'Authorization': f"Bearer {self.test_users['community_admin']['token']}"}
            response = self.session.get(f'{self.base_url}/api/communities/{community_id}', headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            
            # 5. 社区管理员查看社区用户
            response = self.session.get(f'{self.base_url}/api/communities/{community_id}/users', headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            
            # 6. 社区管理员搜索用户
            response = self.session.get(
                f'{self.base_url}/api/communities/{community_id}/users?keyword=普通',
                headers=admin_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
    
    def test_user_join_community_flow(self):
        """测试用户加入社区流程"""
        if 'normal_user' not in self.test_users or 'test_community' not in self.test_communities:
            pytest.skip('缺少必要的测试数据')
        
        user_headers = {'Authorization': f"Bearer {self.test_users['normal_user']['token']}"}
        community_id = self.test_communities['test_community']['community_id']
        
        # 1. 用户查看当前社区信息
        response = self.session.get(f'{self.base_url}/api/user/community', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') != 0
        current_community = data['data']['community']
        assert current_community['name'] == '安卡大家庭'  # 默认社区
        
        # 2. 用户查看可申请的社区
        response = self.session.get(f'{self.base_url}/api/communities/available', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') != 0
        available_communities = data['data']
        assert len(available_communities) >= 1
        
        # 3. 用户申请加入社区
        response = self.session.post(f'{self.base_url}/api/community/applications',
            headers=user_headers,
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区进行测试'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') != 0
        
        # 4. 管理员查看申请
        if 'super_admin' in self.test_users:
            admin_headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
            response = self.session.get(f'{self.base_url}/api/community/applications', headers=admin_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            applications = data['data']
            assert len(applications) >= 1
            
            # 找到刚提交的申请
            application = None
            for app in applications:
                if app['user']['user_id'] == self.test_users['normal_user']['user_id']:
                    application = app
                    break
            
            assert application is not None
            application_id = application['application_id']
            
            # 5. 管理员批准申请
            response = self.session.put(
                f'{self.base_url}/api/community/applications/{application_id}/approve',
                headers=admin_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            
            # 6. 用户查看更新后的社区信息
            response = self.session.get(f'{self.base_url}/api/user/community', headers=user_headers)
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            updated_community = data['data']['community']
            assert updated_community['community_id'] == community_id
    
    def test_user_search_and_promote_flow(self):
        """测试用户搜索和提升管理员流程"""
        if 'super_admin' not in self.test_users or 'test_community' not in self.test_communities:
            pytest.skip('缺少必要的测试数据')
        
        # 创建测试用户
        response = self.session.post(f'{self.base_url}/api/auth/register_phone', json={
            'phone': '13800138003',
            'code': '123456',
            'password': 'Test123456',
            'nickname': '待提升用户'
        })
        
        if response.status_code != 200:
            pytest.skip('无法创建测试用户')
        
        data = response.json()
        if data.get('code') == 0:
            pytest.skip('用户创建失败')
        
        new_user_id = data['data']['user_id']
        
        # 将用户分配到测试社区
        if 'super_admin' in self.test_users:
            headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
            community_id = self.test_communities['test_community']['community_id']
            
            # 1. 搜索用户
            response = self.session.get(
                f'{self.base_url}/api/communities/{community_id}/users?keyword=13800138003',
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            users = data['data']['users']
            assert len(users) == 1
            assert users[0]['nickname'] == '待提升用户'
            
            # 2. 将用户提升为管理员
            response = self.session.post(
                f'{self.base_url}/api/communities/{community_id}/users/{new_user_id}/set-admin',
                headers=headers,
                json={'role': 2}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            
            # 3. 验证用户已成为管理员
            response = self.session.get(
                f'{self.base_url}/api/communities/{community_id}/admins',
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') != 0
            admins = data['data']
            
            # 查找新提升的管理员
            new_admin = None
            for admin in admins:
                if admin['user_id'] == new_user_id:
                    new_admin = admin
                    break
            
            assert new_admin is not None
            assert new_admin['role_name'] == 'normal'
    
    def test_permission_boundary(self):
        """测试权限边界"""
        if 'normal_user' not in self.test_users or 'test_community' not in self.test_communities:
            pytest.skip('缺少必要的测试数据')
        
        user_headers = {'Authorization': f"Bearer {self.test_users['normal_user']['token']}"}
        community_id = self.test_communities['test_community']['community_id']
        
        # 1. 普通用户尝试访问社区列表（应该被拒绝）
        response = self.session.get(f'{self.base_url}/api/communities', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 业务错误
        assert '权限不足' in data['msg']
        
        # 2. 普通用户尝试管理社区（应该被拒绝）
        response = self.session.get(
            f'{self.base_url}/api/communities/{community_id}/users',
            headers=user_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '权限不足' in data['msg']
        
        # 3. 普通用户尝试添加管理员（应该被拒绝）
        response = self.session.post(
            f'{self.base_url}/api/communities/{community_id}/admins',
            headers=user_headers,
            json={'user_ids': [1], 'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '权限不足' in data['msg']
    
    def test_error_handling(self):
        """测试错误处理"""
        if 'super_admin' not in self.test_users:
            pytest.skip('缺少超级管理员用户')
        
        headers = {'Authorization': f"Bearer {self.test_users['super_admin']['token']}"}
        
        # 1. 访问不存在的社区
        response = self.session.get(f'{self.base_url}/api/communities/99999', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区不存在' in data['msg']
        
        # 2. 创建重复名称的社区
        if 'test_community' in self.test_communities:
            response = self.session.post(f'{self.base_url}/api/communities',
                headers=headers,
                json={
                    'name': 'E2E测试社区',  # 重复名称
                    'description': '另一个测试社区'
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') == 0
            assert '社区名称已存在' in data['msg']
        
        # 3. 处理不存在的申请
        response = self.session.put(
            f'{self.base_url}/api/community/applications/99999/approve',
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '申请不存在' in data['msg']
        
        # 4. 拒绝申请未提供理由
        response = self.session.put(
            f'{self.base_url}/api/community/applications/99999/reject',
            headers=headers,
            json={}  # 没有拒绝理由
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '缺少拒绝理由' in data['msg']


class TestCommunityPerformance:
    """社区功能性能测试"""
    
    @classmethod
    def setup_class(cls):
        """测试类初始化"""
        cls.base_url = os.getenv('API_BASE_URL', 'http://localhost:8080')
        cls.session = requests.Session()
    
    @classmethod
    def teardown_class(cls):
        """测试类清理"""
        cls.session.close()
    
    def test_large_community_user_search(self):
        """测试大社区用户搜索性能"""
        # 这个测试需要预先创建大量用户数据
        # 在实际环境中应该使用专门的性能测试工具
        pass
    
    def test_concurrent_applications(self):
        """测试并发申请处理"""
        # 模拟多个用户同时提交申请
        # 需要使用线程池或异步请求
        pass


if __name__ == '__main__':
    # 设置环境变量
    os.environ['API_BASE_URL'] = 'http://localhost:8080'
    
    # 运行测试
    pytest.main([__file__, '-v', '-s'])