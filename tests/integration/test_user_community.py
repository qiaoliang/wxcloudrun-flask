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
from .conftest import IntegrationTestBase


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
            cls.test_user_id = cls.test_user.user_id  # 存储ID用于后续查询
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='测试社区',
                creator=cls.test_user
            )
            cls.test_community_id = cls.test_community.community_id  # 存储ID用于后续查询
            
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
        
        # 使用标准成功断言，验证新的数据结构
        data = self.assert_api_success(response, expected_data_keys=['nickname', 'role', 'role_name'])
        assert data['data']['nickname'] == '测试用户'  # 来自test_auth_login_phone.py的用户
        assert 'role' in data['data'], "响应数据中缺少role字段"
        assert 'role_name' in data['data'], "响应数据中缺少role_name字段"
        
        # 验证role是数字类型（1=普通用户, 2=社区专员, 3=社区主管, 4=超级系统管理员）
        assert isinstance(data['data']['role'], int), f"role应该是数字类型，实际是: {type(data['data']['role'])}"
        assert data['data']['role'] in [1, 2, 3, 4], f"无效的role值: {data['data']['role']}"
        
        # 验证role_name是字符串类型且为有效值
        assert isinstance(data['data']['role_name'], str), f"role_name应该是字符串类型，实际是: {type(data['data']['role_name'])}"
        role_name_map = {
            1: '普通用户',
            2: '社区专员', 
            3: '社区主管',
            4: '超级系统管理员'
        }
        assert data['data']['role_name'] == role_name_map[data['data']['role']], f"role_name与role不匹配: role={data['data']['role']}, role_name={data['data']['role_name']}"
    
    def test_update_user_profile(self):
        """测试更新用户资料"""
        client = self.get_test_client()
        
        # 模拟登录状态，确保在应用上下文中访问用户对象
        with self.app.app_context():
            # 从数据库重新查询用户对象以确保它绑定到当前会话
            test_user = self.db.session.get(User, self.test_user_id)
            with client.session_transaction() as sess:
                sess['user_openid'] = test_user.wechat_openid
        
        # 准备更新数据
        update_data = {
            'nickname': '更新后的昵称',
            'avatar_url': 'https://example.com/new_avatar.jpg'
        }
        
        # 发送请求
        response = self.make_authenticated_request(
            'POST',
            '/api/user/profile',
            data=update_data,
            phone_number='13900007997',
            password='Firefox0820'
        )
        
        # 验证响应
        data = self.assert_api_success(response)
        
        # 验证数据库中的更新 - 需要在应用上下文中执行
        with self.app.app_context():
            updated_user = self.db.session.get(User, self.test_user_id)
            assert updated_user.nickname == '更新后的昵称'
    
    def test_user_community_management(self):
        """测试用户社区管理功能"""
        client = self.get_test_client()
        
        # 测试获取用户社区
        response = self.make_authenticated_request(
            'GET',
            '/api/user/community',
            phone_number='13900007997',
            password='Firefox0820'
        )
        data = self.assert_api_success(response)
        
        # TODO: 修复切换社区API后重新启用
        # 测试切换社区 - API方法不存在，暂时注释
        # switch_data = {
        #     'community_id': self.test_community_id
        # }
        # response = self.make_authenticated_request(
        #     'POST',
        #     '/api/user/switch-community',
        #     data=switch_data,
        #     phone_number='13900007997',
        #     password='Firefox0820'
        # )
        # data = self.assert_api_success(response)


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
            cls.test_user_id = cls.test_user.user_id  # 存储ID用于后续查询
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='社区测试社区',
                creator=cls.test_user
            )
            cls.test_community_id = cls.test_community.community_id  # 存储ID用于后续查询
    
    def test_create_community(self):
        """测试创建社区"""
        # 创建社区管理员用户
        with self.app.app_context():
            admin_user = self.create_standard_test_user(role=4, phone_number='13900007998')
        
        # 使用认证请求工具
        community_data = {
            'name': '新测试社区',
            'description': '这是一个新的测试社区'
        }
        
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number='13900007998',  # 使用创建用户时的手机号
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
            phone_number='13900007997',  # 使用测试用户的手机号
            password='Firefox0820'
        )
        
        # 验证响应
        data = self.assert_api_success(response)
        assert len(data['data']) >= 1  # 至少包含测试社区
    
    def test_user_role_permissions(self):
        """测试不同角色的权限设置"""
        # 测试超级管理员权限 (role=4)
        with self.app.app_context():
            # 从数据库重新查询社区对象以确保它绑定到当前会话
            test_community = self.db.session.get(Community, self.test_community_id)
            super_admin_user = self.create_standard_test_user(role=4, phone_number='13900007999')
            # 建立用户-社区关系
            super_admin_user.community_id = test_community.community_id
            self.db.session.commit()
        
        response = self.make_authenticated_request(
            'GET', 
            '/api/user/profile',
            phone_number='13900007999',
            password='Firefox0820'
        )
        
        data = self.assert_api_success(response, expected_data_keys=['role', 'role_name'])
        assert data['data']['role'] == 4, f"超级管理员role应该是4，实际是: {data['data']['role']}"
        assert data['data']['role_name'] == '超级系统管理员', f"超级管理员role_name应该是'超级系统管理员'，实际是: {data['data']['role_name']}"
        
        # 测试社区主管权限 (role=3)
        with self.app.app_context():
            community_manager_user = self.create_standard_test_user(role=3, phone_number='13900007996')
            # 建立用户-社区关系
            test_community = self.db.session.get(Community, self.test_community_id)
            community_manager_user.community_id = test_community.community_id
            self.db.session.commit()
        
        response = self.make_authenticated_request(
            'GET', 
            '/api/user/profile',
            phone_number='13900007996',
            password='Firefox0820'
        )
        
        data = self.assert_api_success(response, expected_data_keys=['role', 'role_name'])
        assert data['data']['role'] == 3, f"社区主管role应该是3，实际是: {data['data']['role']}"
        assert data['data']['role_name'] == '社区主管', f"社区主管role_name应该是'社区主管'，实际是: {data['data']['role_name']}"
        
        # 测试社区专员权限 (role=2)
        with self.app.app_context():
            community_staff_user = self.create_standard_test_user(role=2, phone_number='13900007995')
            # 建立用户-社区关系
            test_community = self.db.session.get(Community, self.test_community_id)
            community_staff_user.community_id = test_community.community_id
            self.db.session.commit()
        
        response = self.make_authenticated_request(
            'GET', 
            '/api/user/profile',
            phone_number='13900007995',
            password='Firefox0820'
        )
        
        data = self.assert_api_success(response, expected_data_keys=['role', 'role_name'])
        assert data['data']['role'] == 2, f"社区专员role应该是2，实际是: {data['data']['role']}"
        assert data['data']['role_name'] == '社区专员', f"社区专员role_name应该是'社区专员'，实际是: {data['data']['role_name']}"
        
        # 测试普通用户权限 (role=1)
        with self.app.app_context():
            normal_user = self.create_standard_test_user(role=1, phone_number='13900008000')
            # 建立用户-社区关系
            test_community = self.db.session.get(Community, self.test_community_id)
            normal_user.community_id = test_community.community_id
            self.db.session.commit()
        
        response = self.make_authenticated_request(
            'GET', 
            '/api/user/profile',
            phone_number='13900008000',
            password='Firefox0820'
        )
        
        data = self.assert_api_success(response, expected_data_keys=['role', 'role_name'])
        assert data['data']['role'] == 1, f"普通用户role应该是1，实际是: {data['data']['role']}"
        assert data['data']['role_name'] == '普通用户', f"普通用户role_name应该是'普通用户'，实际是: {data['data']['role_name']}"


if __name__ == '__main__':
    pytest.main([__file__])