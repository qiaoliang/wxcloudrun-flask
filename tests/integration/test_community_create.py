"""
社区创建集成测试
测试社区创建API端点，验证avatar_url参数修复
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
from test_constants import TEST_CONSTANTS


class TestCommunityCreateIntegration(IntegrationTestBase):
    """社区创建集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 获取或创建超级管理员（用于社区创建权限）
            super_admin = cls.create_or_get_super_admin('community_create_test')
            # 超级管理员信息现在是字典，直接获取
            cls.super_admin_id = super_admin['user_id']
            cls.super_admin_phone = super_admin['phone_number']
            
            # 创建标准测试用户
            test_user = cls.create_standard_test_user(role=1, test_context='community_create_test')
            cls.test_user_id = test_user.user_id
            cls.test_user_phone = test_user.phone_number

    def test_create_community_without_avatar_url(self):
        """测试创建社区不包含avatar_url参数（修复验证）"""
        # 准备社区创建数据（不包含avatar_url）
        community_data = {
            'name': '测试社区创建',
            'description': '用于验证avatar_url参数修复的测试社区'
        }
        
        # 发送创建社区请求（使用超级管理员权限）
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'data' in data
        
        community = data['data']
        assert community['community_id'] is not None
        assert community['name'] == '测试社区创建'
        assert community['description'] == '用于验证avatar_url参数修复的测试社区'
        assert community['creator_id'] == self.super_admin_id
        assert community['message'] == '创建成功'
        
        # 验证数据库中的社区记录（与响应数据一致性验证）
        with self.app.app_context():
            saved_community = self.db.session.get(Community, community['community_id'])
            assert saved_community is not None
            assert saved_community.name == community['name']
            assert saved_community.description == community['description']
            assert saved_community.creator_id == community['creator_id']

    def test_create_community_with_all_valid_params(self):
        """测试创建社区包含所有有效参数"""
        # 准备完整的社区创建数据（不包含avatar_url）
        community_data = {
            'name': '完整参数社区',
            'description': '包含所有有效参数的测试社区',
            'location': '测试位置',
            'location_lat': 39.9042,
            'location_lon': 116.4074,
            'manager_id': self.test_user_id  # 指定主管
        }
        
        # 发送创建社区请求（使用超级管理员权限）
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        community = data['data']
        assert community['community_id'] is not None
        assert community['name'] == '完整参数社区'
        assert community['description'] == '包含所有有效参数的测试社区'
        assert community['creator_id'] == self.super_admin_id
        assert community['message'] == '创建成功'
        
        # 验证数据库记录（API目前不支持location、manager_id等额外参数）
        with self.app.app_context():
            saved_community = self.db.session.get(Community, community['community_id'])
            assert saved_community is not None
            assert saved_community.location is None  # API不支持location参数
            assert saved_community.location_lat is None  # API不支持location_lat参数
            assert saved_community.location_lon is None  # API不支持location_lon参数
            assert saved_community.manager_id is None  # API不支持manager_id参数

    def test_create_community_with_avatar_url_param_should_be_ignored(self):
        """测试创建社区包含avatar_url参数时应该被忽略"""
        # 准备包含avatar_url的社区创建数据
        community_data = {
            'name': '包含avatar参数的社区',
            'description': '测试avatar_url参数被正确忽略',
            'avatar_url': TEST_CONSTANTS.generate_avatar_url('test_user')  # 这个参数应该被忽略
        }
        
        # 发送创建社区请求（使用超级管理员权限）
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )
        
        # 验证响应成功（avatar_url被忽略，不影响创建）
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        community = data['data']
        assert community['community_id'] is not None
        assert community['name'] == '包含avatar参数的社区'
        assert community['description'] == '测试avatar_url参数被正确忽略'
        assert community['creator_id'] == self.super_admin_id
        assert community['message'] == '创建成功'
        
        # 验证数据库记录（Community模型没有avatar_url字段）
        with self.app.app_context():
            saved_community = self.db.session.get(Community, community['community_id'])
            assert saved_community is not None
            assert saved_community.name == community['name']
            # 确认Community模型确实没有avatar_url属性
            assert not hasattr(saved_community, 'avatar_url')

    def test_create_community_minimal_params(self):
        """测试创建社区使用最小参数（仅name）"""
        # 准备最小参数数据
        community_data = {
            'name': '最小参数社区'
            # description是可选的，avatar_url被移除
        }
        
        # 发送创建社区请求（使用超级管理员权限）
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )
        
        # 验证响应
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        
        community = data['data']
        assert community['community_id'] is not None
        assert community['name'] == '最小参数社区'
        assert community['creator_id'] == self.super_admin_id
        assert community['message'] == '创建成功'

    def test_create_community_validation_errors(self):
        """测试社区创建验证错误"""
        # 测试空名称
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data={'name': '', 'description': '测试描述'},
            phone_number=self.super_admin_phone
        )
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert '社区名称不能为空' in data['msg']

    def test_community_service_signature_compatibility(self):
        """测试CommunityService.create_community方法签名兼容性"""
        from wxcloudrun.community_service import CommunityService
        import inspect
        
        # 验证方法签名
        sig = inspect.signature(CommunityService.create_community)
        params = list(sig.parameters.keys())
        
        # 确认avatar_url不在参数列表中
        assert 'avatar_url' not in params
        
        # 确认必需参数存在
        required_params = ['name', 'description', 'creator_id']
        for param in required_params:
            assert param in params
        
        # 测试直接调用服务方法
        with self.app.app_context():
            community = CommunityService.create_community(
                name='直接服务调用测试',
                description='通过直接调用CommunityService创建',
                creator_id=self.test_user_id
            )
            
            assert community is not None
            assert community.name == '直接服务调用测试'
            assert community.creator_id == self.test_user_id
            
            # 清理测试数据
            self.db.session.delete(community)
            self.db.session.commit()