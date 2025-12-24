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

from database.flask_models import User, Community
from tests.conftest import IntegrationTestBase


class TestUserIntegration(IntegrationTestBase):
    """用户管理集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建标准测试用户（与test_auth_login_phone.py兼容）
            cls.test_user = cls.create_standard_test_user(role=1)
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='测试社区',
                creator=cls.test_user
            )
            
            # 建立用户-社区关系
            cls.test_user.community_id = cls.test_community.community_id
            cls.db.session.commit()
    
    def test_get_user_profile(self):
        """测试获取用户资料"""
        # 使用认证请求工具
        response = self.make_authenticated_request(
            'GET', 
            '/api/user/profile',
            phone_number='13900007997',
            password='Firefox0820'
        )
        
        print(f'响应状态码: {response.status_code}')
        print(f'响应内容: {response.data.decode()}')
        
        # 使用标准成功断言
        data = self.assert_api_success(response, expected_data_keys=['nickname'])
        assert data['data']['nickname'] == '测试用户'  # 来自test_auth_login_phone.py的用户
    
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
            'User', self.test_user.user_id
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
            'community_id': self.test_community.community_id
        }
        response = client.post('/api/user/switch-community',
                             data=json.dumps(switch_data),
                             content_type='application/json')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 1


class TestCommunityIntegration(IntegrationTestBase):
    """社区管理集成测试类"""
    
    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建社区管理员测试用户
            cls.test_user = cls.create_standard_test_user(role=4)  # 超级管理员权限
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='社区测试社区',
                creator=cls.test_user
            )
    
    def test_create_community(self):
        """测试创建社区"""
        # 创建社区管理员用户
        admin_user = self.create_standard_test_user(role=4)
        
        # 使用认证请求工具
        community_data = {
            'name': '新测试社区',
            'description': '这是一个新的测试社区'
        }
        
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number='13900007000',  # 超级管理员手机号
            password='Firefox0820'
        )
        
        # 验证响应
        data = json.loads(response.data)
        assert 'code' in data
        print(f'社区创建API响应: {data}')
    
    def test_get_community_list(self):
        """测试获取社区列表"""
        # 使用认证请求工具
        response = self.make_authenticated_request(
            'GET',
            '/api/communities',
            phone_number='13900007000',  # 超级管理员手机号
            password='Firefox0820'
        )
        
        # 验证响应
        data = self.assert_api_success(response)
        assert len(data['data']) >= 1  # 至少包含测试社区


if __name__ == '__main__':
    pytest.main([__file__])