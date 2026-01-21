"""
测试 /api/user/managed-communities API
验证返回的社区数据包含 manager_name 字段
"""
import json
import pytest
from tests.integration.conftest import IntegrationTestBase


class TestManagedCommunitiesAPI(IntegrationTestBase):
    """测试 managed-communities API"""

    def test_managed_communities_contains_manager_name(self):
        """测试 managed-communities API 返回的数据包含 manager_name 字段"""
        with self.app.app_context():
            # Arrange
            admin = self.get_super_admin('test_manager_name')

            # 获取 token 和 client
            admin_token = self.get_jwt_token(admin['phone_number'])
            client = self.get_test_client()

            # Act - 直接获取超级管理员管理的社区（包括两个默认社区）
            response = client.get(
                '/api/user/managed-communities?limit=100',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            # Assert
            data = self.assert_api_success(response)
            communities = data['data']['communities']
            assert len(communities) > 0, "超级管理员应该能管理至少一个社区"

            # 验证至少有一个社区包含 manager_name 字段
            found_manager_name = False
            for community in communities:
                if 'manager_name' in community:
                    found_manager_name = True
                    # 如果社区有主管，验证 manager_name 不为 None
                    if community.get('manager_id'):
                        assert community['manager_name'] is not None, \
                            f"社区 {community['name']} 有 manager_id={community['manager_id']}，但 manager_name 为 None"
                    break

            assert found_manager_name, "返回的社区数据中应该包含 manager_name 字段"

    def test_managed_communities_data_structure(self):
        """测试 managed-communities API 返回的数据结构正确"""
        with self.app.app_context():
            # Arrange
            admin = self.get_super_admin('test_data_structure')

            # 获取 token 和 client
            admin_token = self.get_jwt_token(admin['phone_number'])
            client = self.get_test_client()

            # Act
            response = client.get(
                '/api/user/managed-communities?limit=100',
                headers={'Authorization': f'Bearer {admin_token}'}
            )

            # Assert
            data = self.assert_api_success(response)
            communities = data['data']['communities']
            assert len(communities) > 0

            # 验证每个社区的数据结构包含必需字段
            for community in communities:
                # 基本字段
                assert 'community_id' in community
                assert 'name' in community
                assert 'description' in community
                assert 'location' in community
                assert 'status' in community
                assert 'created_at' in community

                # 主管相关字段（关键修复点）
                assert 'manager_id' in community
                assert 'manager_name' in community, "manager_name 字段必须存在"
                assert 'manager' in community

                # 验证 manager_name 的值类型
                if community.get('manager_id'):
                    # 如果有 manager_id，manager_name 应该是字符串
                    assert community['manager_name'] is None or isinstance(community['manager_name'], str), \
                        f"manager_name 应该是字符串或 None，实际是 {type(community['manager_name'])}"
