"""
社区列表API集成测试
专注于验证真实API行为和数据一致性
遵循测试最佳实践，避免测试反模式
"""

import pytest
import json
import sys
import os

# 添加上级目录到路径以导入测试工具
tests_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, tests_path)
from test_constants import TEST_CONSTANTS

from database.flask_models import User, Community
from .conftest import IntegrationTestBase


class TestCommunityListAPI(IntegrationTestBase):
    """社区列表API集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()
    
    def setup_method(self, method):
        """每个测试方法前的设置"""
        super().setup_method(method)

    @classmethod
    def _create_test_data(cls):
        """创建测试所需的社区数据"""
        with cls.app.app_context():
            # 创建测试用户
            cls.test_user = cls.create_standard_test_user(role=1)
            cls.test_phone_number = cls.test_user.phone_number  # 存储手机号码
            cls.test_user_id = cls.test_user.user_id  # 存储用户ID
            cls.test_user_nickname = cls.test_user.nickname  # 存储用户昵称
            
            # 创建多个测试社区以验证列表功能
            cls.test_communities = []
            
            # 创建普通社区（应该出现在列表中）
            community1 = cls.create_test_community(
                name='公开测试社区1',
                creator=cls.test_user,
                description='第一个公开测试社区',
                status=1  # 启用状态
            )
            cls.test_communities.append(community1)
            
            community2 = cls.create_test_community(
                name='公开测试社区2', 
                creator=cls.test_user,
                description='第二个公开测试社区',
                status=1  # 启用状态
            )
            cls.test_communities.append(community2)
            
            # 创建禁用社区（不应该出现在列表中）
            disabled_community = cls.create_test_community(
                name='禁用测试社区',
                creator=cls.test_user,
                description='这个社区被禁用了',
                status=2  # 禁用状态
            )
            
            # 创建默认社区（不应该出现在列表中）
            default_community = cls.create_test_community(
                name='安卡大家庭',
                creator=cls.test_user,
                description='默认社区',
                status=1,
                is_default=True
            )
            
            # 保存预期数据用于验证
            cls.expected_communities = [community1, community2]

    def test_community_list_success(self):
        """测试获取社区列表成功场景"""
        # 使用基类提供的认证请求方法
        response = self.make_authenticated_request(
            'GET', 
            '/api/community/list?page=1&page_size=20',
            phone_number=self.test_phone_number
        )
        
        # 验证响应结构
        data = self.assert_api_success(response, ['communities'])
        
        # 验证社区列表数据
        communities = data['data']['communities']
        print(f"✅ 返回社区数量: {len(communities)}")
        
        # 应该至少有我们创建的2个公开社区（可能还有其他已存在的社区）
        assert len(communities) >= 2, f"期望至少2个社区，实际返回{len(communities)}个"
        
        # 验证返回的社区包含我们创建的测试社区
        returned_community_names = [c['name'] for c in communities]
        expected_names = ['公开测试社区1', '公开测试社区2']
        
        for expected_name in expected_names:
            assert expected_name in returned_community_names, f"期望找到社区 '{expected_name}'，但未找到"
            print(f"✅ 找到预期社区: {expected_name}")

    def test_community_list_data_structure(self):
        """测试社区列表数据结构的完整性"""
        response = self.make_authenticated_request(
            'GET',
            '/api/community/list?page=1&page_size=20',
            phone_number=self.test_phone_number
        )
        
        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']
        
        if communities:
            # 验证第一个社区的完整数据结构
            community = communities[0]
            required_fields = [
                'community_id', 'name', 'description', 'creator_id',
                'status', 'created_at', 'updated_at', 'manager_count', 'worker_count'
            ]
            
            for field in required_fields:
                assert field in community, f"社区数据缺少必需字段: {field}"
                print(f"✅ 字段 '{field}' 存在")
            
            # 验证数据类型
            assert isinstance(community['community_id'], int), "community_id 应该是整数"
            assert isinstance(community['name'], str), "name 应该是字符串"
            assert isinstance(community['description'], str), "description 应该是字符串"
            assert isinstance(community['status'], int), "status 应该是整数"
            assert isinstance(community['manager_count'], int), "manager_count 应该是整数"
            assert isinstance(community['worker_count'], int), "worker_count 应该是整数"
            
            # 验证时间格式
            assert community['created_at'] is not None, "created_at 不能为空"
            assert community['updated_at'] is not None, "updated_at 不能为空"
            
            print("✅ 所有数据类型验证通过")

    def test_community_list_filtering_logic(self):
        """测试社区列表过滤逻辑的正确性"""
        response = self.make_authenticated_request(
            'GET',
            '/api/community/list?page=1&page_size=20',
            phone_number=self.test_phone_number
        )
        
        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']
        returned_community_names = [c['name'] for c in communities]
        
        # 验证禁用社区不在列表中
        assert '禁用测试社区' not in returned_community_names, "禁用社区不应该出现在列表中"
        print("✅ 禁用社区正确过滤")
        
        # 验证默认社区不在列表中
        assert '安卡大家庭' not in returned_community_names, "默认社区不应该出现在列表中"
        print("✅ 默认社区正确过滤")
        
        # 验证只返回启用状态的社区
        for community in communities:
            assert community['status'] == 1, f"社区 '{community['name']}' 状态应该是启用(1)，实际是 {community['status']}"
        print("✅ 所有返回社区都是启用状态")

    def test_community_list_authentication_required(self):
        """测试社区列表需要认证"""
        client = self.get_test_client()
        
        # 不提供token的请求
        response = client.get('/api/community/list?page=1&page_size=20')
        
        # 应该返回认证错误
        error_data = self.assert_api_error(response, expected_code=0)
        assert 'token' in error_data['msg'].lower(), "错误消息应该提到token"
        print("✅ 认证验证正常工作")

    def test_community_list_invalid_token(self):
        """测试无效token的处理"""
        client = self.get_test_client()
        headers = {'Authorization': 'Bearer invalid_token'}
        
        response = client.get('/api/community/list?page=1&page_size=20', headers=headers)
        
        # 应该返回认证错误
        self.assert_api_error(response, expected_code=0)
        print("✅ 无效token正确处理")

    def test_community_list_pagination_parameters(self):
        """测试分页参数的处理"""
        # 测试不同的分页参数
        test_cases = [
            {'page': 1, 'page_size': 5},
            {'page': 1, 'page_size': 10},
            {'page': 2, 'page_size': 5}
        ]
        
        for params in test_cases:
            response = self.make_authenticated_request(
                'GET',
                f"/api/community/list?page={params['page']}&page_size={params['page_size']}",
                phone_number=self.test_phone_number
            )
            
            data = self.assert_api_success(response, ['communities'])
            communities = data['data']['communities']
            
            # 验证分页大小限制
            assert len(communities) <= params['page_size'], f"返回数量不应超过page_size: {params['page_size']}"
            print(f"✅ 分页参数 page={params['page']}, page_size={params['page_size']} 正常工作")

    def test_community_list_response_consistency(self):
        """测试响应数据的一致性"""
        # 多次调用API，验证响应一致性
        responses = []
        
        for i in range(3):
            response = self.make_authenticated_request(
                'GET',
                '/api/community/list?page=1&page_size=20',
                phone_number=self.test_phone_number
            )
            
            data = self.assert_api_success(response, ['communities'])
            communities = data['data']['communities']
            responses.append(communities)
        
        # 验证响应一致性
        first_response = responses[0]
        for i, response in enumerate(responses[1:], 1):
            assert len(response) == len(first_response), f"第{i+1}次响应的社区数量与第1次不一致"
            
            # 验证社区顺序和内容一致
            for j, community in enumerate(response):
                assert community['community_id'] == first_response[j]['community_id'], f"第{i+1}次响应的第{j+1}个社区ID不一致"
                assert community['name'] == first_response[j]['name'], f"第{i+1}次响应的第{j+1}个社区名称不一致"
        
        print("✅ 多次调用响应数据一致")

    def test_community_list_creator_information(self):
        """测试社区创建者信息的完整性"""
        response = self.make_authenticated_request(
            'GET',
            '/api/community/list?page=1&page_size=20',
            phone_number=self.test_phone_number
        )
        
        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']
        
        # 查找我们创建的社区
        test_community_names = ['公开测试社区1', '公开测试社区2']
        
        for community in communities:
            if community['name'] in test_community_names:
                # 验证创建者信息
                assert community['creator_id'] == self.test_user_id, "创建者ID应该匹配"
                assert 'creator' in community, "应该包含创建者详细信息"
                
                creator = community['creator']
                if creator:  # creator可能为None
                    assert 'user_id' in creator, "创建者信息应该包含user_id"
                    assert 'nickname' in creator, "创建者信息应该包含nickname"
                    assert 'avatar_url' in creator, "创建者信息应该包含avatar_url"
                    
                    assert creator['user_id'] == self.test_user_id, "创建者user_id应该匹配"
                    assert creator['nickname'] == self.test_user_nickname, "创建者nickname应该匹配"
                
                print(f"✅ 社区 '{community['name']}' 的创建者信息正确")
                break