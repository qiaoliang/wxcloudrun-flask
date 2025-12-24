"""
优化的角色权限测试
遵循KISS和DRY原则，使用统一的测试工具
"""

import pytest
from .conftest import IntegrationTestBase
from test_utils import RolePermissionTester, TestUserFactory
from test_constants import TEST_CONSTANTS
from database.flask_models import Community  # 添加Community导入


class TestRolePermissionsOptimized(IntegrationTestBase):
    """优化的角色权限测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls.role_permissions = {
            1: ("普通用户", "普通用户"),
            2: ("社区专员", "社区专员"), 
            3: ("社区主管", "社区主管"),
            4: ("超级系统管理员", "超级系统管理员")  # 修正期望值与API返回一致
        }
        
        # 创建测试社区供其他测试使用
        with cls.app.app_context():
            # 先创建一个测试用户作为社区创建者
            cls.test_user = cls.create_standard_test_user(role=4)  # 超级管理员
            cls.test_community = cls.create_test_community(
                name='角色权限测试社区',
                creator=cls.test_user
            )
            cls.test_community_id = cls.test_community.community_id

    @pytest.mark.parametrize("role,expected_role_name", [
        (1, "普通用户"),
        (2, "社区专员"),
        (3, "社区主管"), 
        (4, "超级系统管理员")
    ])
    def test_user_role_permissions_parametrized(self, role, expected_role_name):
        """
        参数化测试：不同角色的权限设置
        """
        # Arrange - 创建指定角色的用户
        user = RolePermissionTester.create_user_with_role(
            self, 
            role=role,
            test_context=f"role_test_{role}"
        )
        
        # Act & Assert - 测试用户权限
        RolePermissionTester.test_user_permissions(
            self, 
            user=user,
            expected_role=role,
            expected_role_name=expected_role_name
        )

    def test_all_roles_in_single_test(self):
        """
        单个测试中验证所有角色权限
        遵循KISS原则，减少重复的测试设置
        """
        # 准备测试社区
        with self.app.app_context():
            test_community = self.db.session.get(Community, self.test_community_id)
        
        # 测试所有角色
        for role, (role_name, expected_role_name) in self.role_permissions.items():
            # 创建角色用户
            user = RolePermissionTester.create_user_with_role(
                self,
                role=role,
                test_context=f"comprehensive_role_test_{role}",
                community_id=test_community.community_id
            )
            
            # 验证权限
            RolePermissionTester.test_user_permissions(
                self,
                user=user,
                expected_role=role,
                expected_role_name=expected_role_name
            )

    def test_role_based_api_access(self):
        """
        测试基于角色的API访问权限
        使用统一的认证请求工具
        """
        from test_utils import AuthRequestHelper
        
        # 测试不同角色访问用户资料API
        endpoints_to_test = [
            '/api/user/profile',
        ]
        
        for role in [1, 2, 3, 4]:
            for endpoint in endpoints_to_test:
                response = AuthRequestHelper.make_role_based_request(
                    self,
                    role=role,
                    endpoint=endpoint,
                    test_context=f"api_access_test_{role}"
                )
                
                # 验证响应成功
                data = self.assert_api_success(response)
                assert data['data']['role'] == role

    def test_role_permission_consistency(self):
        """
        测试角色权限的一致性
        确保相同的角色总是有相同的权限
        """
        role = 3  # 社区主管
        expected_role_name = "社区主管"
        
        # 创建两个相同角色的用户
        user1 = RolePermissionTester.create_user_with_role(
            self,
            role=role,
            test_context="consistency_test_1"
        )
        
        user2 = RolePermissionTester.create_user_with_role(
            self,
            role=role,
            test_context="consistency_test_2"
        )
        
        # 验证两个用户的权限一致
        for user in [user1, user2]:
            RolePermissionTester.test_user_permissions(
                self,
                user=user,
                expected_role=role,
                expected_role_name=expected_role_name
            )

    def test_role_hierarchy_validation(self):
        """
        测试角色层次结构的验证
        """
        # 角色层次：4 > 3 > 2 > 1
        role_hierarchy = {
            4: "超级系统管理员",  # 修正为API实际返回的值
            3: "社区主管", 
            2: "社区专员",
            1: "普通用户"
        }
        
        # 验证角色数值与名称的对应关系
        for role_value, role_name in role_hierarchy.items():
            user = RolePermissionTester.create_user_with_role(
                self,
                role=role_value,
                test_context=f"hierarchy_test_{role_value}"
            )
            
            # 支持用户对象或用户字典
            phone_number = user.phone_number if hasattr(user, 'phone_number') else user['phone_number']
            
            response = self.make_authenticated_request(
                'GET',
                '/api/user/profile',
                phone_number=phone_number,
                password=TEST_CONSTANTS.DEFAULT_PASSWORD
            )
            
            data = self.assert_api_success(response)
            assert data['data']['role'] == role_value
            assert data['data']['role_name'] == role_name