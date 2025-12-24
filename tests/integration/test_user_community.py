"""
用户管理集成测试
测试用户相关的API端点和业务逻辑
"""

import pytest
import json
import sys
import os

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.conftest import TestBase


class TestUserIntegration(TestBase):
    """用户管理集成测试类"""
    
    def test_get_user_profile(self):
        """测试获取用户资料"""
        client = self.get_test_client()
        
        # 模拟登录状态
        with client.session_transaction() as sess:
            sess['user_openid'] = self.test_user.openid
        
        # 发送请求
        response = client.get('/api/profile')
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'data' in data
        assert data['data']['nickname'] == self.test_user.nickname
    
    def test_update_user_profile(self):
        """测试更新用户资料"""
        client = self.get_test_client()
        
        # 模拟登录状态
        with client.session_transaction() as sess:
            sess['user_openid'] = self.test_user.openid
        
        # 准备更新数据
        update_data = {
            'nickname': '更新后的昵称',
            'avatar_url': 'https://example.com/new_avatar.jpg'
        }
        
        # 发送请求
        response = client.post('/api/profile', 
                             data=json.dumps(update_data),
                             content_type='application/json')
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        
        # 验证数据库中的更新
        updated_user = self.db.session.get(
            'User', self.test_user.id
        )
        assert updated_user.nickname == '更新后的昵称'
    
    def test_user_community_management(self):
        """测试用户社区管理功能"""
        client = self.get_test_client()
        
        # 模拟登录状态
        with client.session_transaction() as sess:
            sess['user_openid'] = self.test_user.openid
        
        # 测试获取用户社区
        response = client.get('/api/user/community')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        
        # 测试切换社区
        switch_data = {
            'community_id': self.test_community.id
        }
        response = client.post('/api/user/switch-community',
                             data=json.dumps(switch_data),
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1


class TestCommunityIntegration(TestBase):
    """社区管理集成测试类"""
    
    def test_create_community(self):
        """测试创建社区"""
        client = self.get_test_client()
        
        # 模拟登录状态
        with client.session_transaction() as sess:
            sess['user_openid'] = self.test_user.openid
        
        # 准备社区数据
        community_data = {
            'name': '新测试社区',
            'description': '这是一个新的测试社区'
        }
        
        # 发送请求
        response = client.post('/api/community/create',
                             data=json.dumps(community_data),
                             content_type='application/json')
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'community_id' in data['data']
        
        # 验证数据库中的创建
        new_community = self.db.session.get(
            'Community', data['data']['community_id']
        )
        assert new_community.name == '新测试社区'
    
    def test_get_community_list(self):
        """测试获取社区列表"""
        client = self.get_test_client()
        
        # 模拟登录状态
        with client.session_transaction() as sess:
            sess['user_openid'] = self.test_user.openid
        
        # 发送请求
        response = client.get('/api/communities')
        
        # 验证响应
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1
        assert 'data' in data
        assert len(data['data']) >= 1  # 至少包含测试社区


if __name__ == '__main__':
    pytest.main([__file__])