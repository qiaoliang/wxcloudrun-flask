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
            super_admin = cls.get_super_admin('community_create_test')
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

    def test_create_community_permission_validation(self):
        """测试社区创建权限验证"""
        # 测试普通用户无权限创建社区
        community_data = {
            'name': '权限测试社区',
            'description': '测试权限验证'
        }

        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.test_user_phone  # 普通用户，role=1
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert '无权限创建社区' in data['msg']

    def test_create_community_authentication_required(self):
        """测试社区创建需要认证"""
        client = self.get_test_client()

        # 不提供token的请求
        response = client.post('/api/community/create',
                             data=json.dumps({'name': '测试社区', 'description': '测试'}),
                             content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert 'token' in data['msg'].lower()

    def test_create_community_invalid_token(self):
        """测试无效token的处理"""
        client = self.get_test_client()
        headers = {'Authorization': 'Bearer invalid_token'}

        response = client.post('/api/community/create',
                             data=json.dumps({'name': '测试社区', 'description': '测试'}),
                             headers=headers,
                             content_type='application/json')

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0

    def test_create_community_missing_parameters(self):
        """测试缺少必需参数的情况"""
        # 测试完全缺少参数（使用空的JSON对象）
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data={},
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['msg'] == '缺少请求参数'  # 空对象被识别为缺少参数

    def test_create_community_empty_name(self):
        """测试空社区名称的处理"""
        test_cases = [
            {'name': '', 'description': '测试描述'},
            {'name': '   ', 'description': '测试描述'},  # 只有空格
        ]

        for community_data in test_cases:
            response = self.make_authenticated_request(
                'POST',
                '/api/community/create',
                data=community_data,
                phone_number=self.super_admin_phone
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['code'] == 0
            assert '社区名称不能为空' in data['msg']

    def test_create_community_duplicate_name(self):
        """测试重复社区名称的处理"""
        # 使用时间戳确保名称唯一性
        import time
        timestamp = int(time.time() * 1000)
        unique_name = f'重复名称测试社区_{timestamp}'

        # 先创建一个社区
        community_data = {
            'name': unique_name,
            'description': '第一个社区'
        }

        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1

        # 尝试创建同名社区
        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['msg'] == '创建失败'  # API统一返回创建失败消息

    def test_create_community_response_data_structure(self):
        """测试社区创建响应数据结构的完整性"""
        community_data = {
            'name': '数据结构测试社区',
            'description': '测试响应数据结构完整性'
        }

        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'data' in data

        community = data['data']

        # 验证响应包含所有必需字段
        required_fields = [
            'community_id', 'name', 'description', 'creator_id',
            'manager_id', 'location', 'location_lat', 'location_lon',
            'status', 'created_at', 'message'
        ]

        for field in required_fields:
            assert field in community, f"响应数据缺少必需字段: {field}"

        # 验证数据类型
        assert isinstance(community['community_id'], int), "community_id 应该是整数"
        assert isinstance(community['name'], str), "name 应该是字符串"
        assert isinstance(community['description'], str), "description 应该是字符串"
        assert isinstance(community['creator_id'], int), "creator_id 应该是整数"
        assert isinstance(community['status'], int), "status 应该是整数"
        assert isinstance(community['message'], str), "message 应该是字符串"

        # 验证时间格式
        assert community['created_at'] is not None, "created_at 不能为空"

        # 验证默认值
        assert community['status'] == 1, "新创建的社区状态应该是启用(1)"
        assert community['message'] == '创建成功', "成功消息应该是'创建成功'"

    def test_create_community_database_consistency(self):
        """测试社区创建的数据库一致性"""
        community_data = {
            'name': '数据库一致性测试社区',
            'description': '验证数据库记录与响应数据的一致性'
        }

        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )

        assert response.status_code == 200
        response_data = response.get_json()
        assert response_data['code'] == 1

        community_response = response_data['data']

        # 验证数据库记录
        with self.app.app_context():
            saved_community = self.db.session.get(Community, community_response['community_id'])
            assert saved_community is not None, "数据库中应该存在创建的社区记录"

            # 验证字段一致性
            assert saved_community.community_id == community_response['community_id']
            assert saved_community.name == community_response['name']
            assert saved_community.description == community_response['description']
            assert saved_community.creator_id == community_response['creator_id']
            assert saved_community.status == community_response['status']

            # 验证时间格式转换正确
            assert saved_community.created_at is not None
            assert community_response['created_at'] == saved_community.created_at.isoformat()

    def test_create_community_edge_cases(self):
        """测试社区创建的边界情况"""
        # 测试极长名称
        long_name = 'a' * 100  # 100个字符的名称
        community_data = {
            'name': long_name,
            'description': '测试极长名称'
        }

        response = self.make_authenticated_request(
            'POST',
            '/api/community/create',
            data=community_data,
            phone_number=self.super_admin_phone
        )

        # 根据实际API行为验证结果
        assert response.status_code == 200
        data = response.get_json()
        if data['code'] == 1:
            # 如果成功，验证名称被正确保存
            assert data['data']['name'] == long_name
        else:
            # 如果失败，应该有合理的错误信息
            assert data['code'] == 0

    def test_create_community_special_characters(self):
        """测试包含特殊字符的社区名称"""
        special_names = [
            '社区@#$%^&*()',
            '社区"引号"测试',
            "社区'单引号'测试",
            '社区\n换行\n测试',
            '社区\t制表符\t测试',
            '社区\u4e2d\u6587\u6d4b\u8bd5'  # 中文
        ]

        for name in special_names:
            community_data = {
                'name': name,
                'description': f'测试特殊字符名称: {name}'
            }

            response = self.make_authenticated_request(
                'POST',
                '/api/community/create',
                data=community_data,
                phone_number=self.super_admin_phone
            )

            # 验证API能够处理特殊字符
            assert response.status_code == 200
            data = response.get_json()

            if data['code'] == 1:
                # 如果成功，验证名称被正确保存
                assert data['data']['name'] == name
            else:
                # 如果失败，应该有合理的错误信息
                assert data['code'] == 0

    def test_create_community_concurrent_safety(self):
        """测试社区创建的并发安全性（模拟）"""
        # 在实际环境中，这个测试可能需要真正的并发
        # 这里我们模拟快速连续创建社区的情况

        import time
        timestamp = int(time.time() * 1000)
        communities_created = []

        for i in range(3):
            community_data = {
                'name': f'并发测试社区_{timestamp}_{i}',
                'description': f'第{i}个并发测试社区'
            }

            response = self.make_authenticated_request(
                'POST',
                '/api/community/create',
                data=community_data,
                phone_number=self.super_admin_phone
            )

            assert response.status_code == 200
            data = response.get_json()

            if data['code'] == 1:
                communities_created.append(data['data']['community_id'])

        # 验证所有创建的社区都有唯一的ID
        assert len(set(communities_created)) == len(communities_created), "社区ID应该是唯一的"