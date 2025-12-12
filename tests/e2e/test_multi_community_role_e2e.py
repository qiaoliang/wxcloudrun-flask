"""
多社区角色分配功能的端到端（E2E）测试

测试验证用户可以在多个社区担任不同角色的功能，包括：
- 用户可以同时在A社区担任专员，在B社区担任主管
- 权限控制根据用户在特定社区的角色正确生效
- 用户界面正确显示用户在不同社区的角色
- 数据一致性得到维护
"""
import pytest
import requests
from datetime import datetime


class TestMultiCommunityRoleAssignmentE2E:
    """端到端测试：用户在多个社区担任不同角色的功能"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        return login_data['data']['token'], login_data['data']['user_id']

    def _create_test_user(self, base_url, phone, nickname, password='Test123456'):
        """创建测试用户"""
        register_response = requests.post(f'{base_url}/api/auth/register_phone', json={
            'phone': phone,
            'code': '123456',  # 使用固定的验证码
            'password': password,
            'nickname': nickname
        })
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert register_data.get('code') == 1
        return register_data['data']['user_id']

    def _create_test_community(self, base_url, admin_headers, name, location='测试地址'):
        """创建测试社区"""
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': name,
                'location': location,
                'description': '测试社区描述'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        return data['data']['community_id']

    def test_multi_community_role_assignment_basic_flow(self, test_server):
        """
        E2E测试：基本的多社区角色分配流程
        业务规则：用户可以在多个社区担任不同角色
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 1. 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000001', '多角色测试用户')

        # 2. 创建两个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '社区A-测试')
        community_b_id = self._create_test_community(base_url, admin_headers, '社区B-测试')

        # 3. 将用户添加到第一个社区作为专员
        response1 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_ids': [test_user_id],
                'role': 'staff'  # 专员
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get('code') == 1, f"添加到社区A失败: {data1}"
        assert data1['data']['added_count'] >= 1, "应该成功添加至少1个用户到社区A"

        # 4. 将同一用户添加到第二个社区作为主管
        response2 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'manager'  # 主管
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get('code') == 1, f"添加到社区B失败: {data2}"
        assert data2['data']['added_count'] >= 1, "应该成功添加至少1个用户到社区B"

        # 5. 验证用户在两个社区都有正确的角色
        # 检查社区A - 用户应该作为专员存在
        staff_response_a = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_a_id}
        )
        assert staff_response_a.status_code == 200
        staff_data_a = staff_response_a.json()
        assert staff_data_a.get('code') == 1
        staff_list_a = staff_data_a['data'].get('staff_members', [])
        user_in_community_a = next((s for s in staff_list_a if s['user_id'] == test_user_id), None)
        assert user_in_community_a is not None, f"用户应该在社区A中，但未找到: {staff_list_a}"
        assert user_in_community_a['role'] == 'staff', f"用户在社区A的角色应该是staff，实际是: {user_in_community_a['role']}"

        # 检查社区B - 用户应该作为主管存在
        staff_response_b = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        assert staff_response_b.status_code == 200
        staff_data_b = staff_response_b.json()
        assert staff_data_b.get('code') == 1
        staff_list_b = staff_data_b['data'].get('staff_members', [])
        user_in_community_b = next((s for s in staff_list_b if s['user_id'] == test_user_id), None)
        assert user_in_community_b is not None, f"用户应该在社区B中，但未找到: {staff_list_b}"
        assert user_in_community_b['role'] == 'manager', f"用户在社区B的角色应该是manager，实际是: {user_in_community_b['role']}"

        print("✓ E2E基本流程测试通过：用户成功在多个社区担任不同角色")

    def test_user_permission_based_on_community_role(self, test_server):
        """
        E2E测试：验证用户权限根据其在特定社区的角色正确生效
        业务规则：用户在每个社区的权限应基于其在该社区的角色
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000002', '权限测试用户')

        # 创建两个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '权限测试社区A')
        community_b_id = self._create_test_community(base_url, admin_headers, '权限测试社区B')

        # 将用户添加到社区A作为专员，社区B作为主管
        # 添加到社区A作为专员
        response_a = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response_a.status_code == 200 and response_a.json().get('code') == 1

        # 添加到社区B作为主管
        response_b = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'manager'
            }
        )
        assert response_b.status_code == 200 and response_b.json().get('code') == 1

        # 获取测试用户的token（模拟用户登录）
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13800000002',
            'password': 'Test123456'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        test_user_token = login_data['data']['token']
        test_user_headers = {'Authorization': f'Bearer {test_user_token}'}

        # 验证用户可以访问自己管理的社区列表
        managed_communities_response = requests.get(
            f'{base_url}/api/user/managed-communities',
            headers=test_user_headers
        )
        assert managed_communities_response.status_code == 200
        managed_data = managed_communities_response.json()
        assert managed_data.get('code') == 1

        managed_communities = managed_data['data']['communities']
        assert len(managed_communities) == 2, f"用户应该管理2个社区，实际管理{len(managed_communities)}个"

        # 验证用户在每个社区的角色
        community_a_info = next((c for c in managed_communities if c['community_id'] == community_a_id), None)
        community_b_info = next((c for c in managed_communities if c['community_id'] == community_b_id), None)

        assert community_a_info is not None, "应该找到社区A的信息"
        assert community_b_info is not None, "应该找到社区B的信息"

        assert community_a_info['role_in_community'] == 'staff', f"在社区A的角色应该是staff，实际是: {community_a_info['role_in_community']}"
        assert community_b_info['role_in_community'] == 'manager', f"在社区B的角色应该是manager，实际是: {community_b_info['role_in_community']}"

        print("✓ E2E权限测试通过：用户权限根据社区角色正确生效")

    def test_same_user_cannot_be_added_twice_to_same_community(self, test_server):
        """
        E2E测试：验证同一用户不能在同一个社区中被重复添加
        业务规则：防止用户在同一个社区中担任多个角色或重复任职
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000003', '重复添加测试用户')

        # 创建一个社区
        community_id = self._create_test_community(base_url, admin_headers, '防重复社区')

        # 第一次添加用户到社区
        response1 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get('code') == 1
        assert data1['data']['added_count'] == 1

        # 尝试第二次添加同一用户到同一社区（不同角色）
        response2 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'manager'  # 尝试作为主管添加
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get('code') == 1
        
        # 应该有失败记录，因为用户已在该社区任职
        assert 'failed' in data2['data'], "应该有失败记录，因为用户已在社区任职"
        assert len(data2['data']['failed']) >= 1, "应该至少有一个失败项"
        assert any('已在当前社区任职' in str(f.get('reason', '')) for f in data2['data']['failed']), \
            "失败原因应该是用户已在当前社区任职"

        print("✓ E2E防重复测试通过：防止用户在同一个社区重复任职")

    def test_user_can_be_removed_from_individual_communities(self, test_server):
        """
        E2E测试：验证用户可以从单个社区移除，但保留在其他社区的任职
        业务规则：移除操作应该是社区级别的，不影响用户在其他社区的角色
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000004', '移除测试用户')

        # 创建三个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '移除测试社区A')
        community_b_id = self._create_test_community(base_url, admin_headers, '移除测试社区B')
        community_c_id = self._create_test_community(base_url, admin_headers, '移除测试社区C')

        # 将用户添加到所有三个社区
        for i, (cid, role) in enumerate([(community_a_id, 'staff'), (community_b_id, 'manager'), (community_c_id, 'staff')], 1):
            response = requests.post(f'{base_url}/api/community/add-staff',
                headers=admin_headers,
                json={
                    'community_id': cid,
                    'user_ids': [test_user_id],
                    'role': role
                }
            )
            assert response.status_code == 200 and response.json().get('code') == 1, f"添加到社区{i}失败"

        # 验证用户在所有三个社区都存在
        for cid, expected_role in [(community_a_id, 'staff'), (community_b_id, 'manager'), (community_c_id, 'staff')]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': cid}
            )
            assert staff_response.status_code == 200
            staff_list = staff_response.json()['data'].get('staff_members', [])
            user_in_community = next((s for s in staff_list if s['user_id'] == test_user_id), None)
            assert user_in_community is not None, f"用户应该在社区{cid}中"
            assert user_in_community['role'] == expected_role, f"用户在社区{cid}的角色应该是{expected_role}"

        # 从社区A移除用户
        remove_response = requests.post(f'{base_url}/api/community/remove-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_id': test_user_id
            }
        )
        assert remove_response.status_code == 200 and remove_response.json().get('code') == 1

        # 验证用户已从社区A移除，但在社区B和C仍存在
        # 检查社区A（应该不再有该用户）
        staff_response_a = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_a_id}
        )
        staff_list_a = staff_response_a.json()['data'].get('staff_members', [])
        user_in_community_a = next((s for s in staff_list_a if s['user_id'] == test_user_id), None)
        assert user_in_community_a is None, "用户应该已从社区A移除"

        # 检查社区B（应该仍有该用户，角色为manager）
        staff_response_b = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        staff_list_b = staff_response_b.json()['data'].get('staff_members', [])
        user_in_community_b = next((s for s in staff_list_b if s['user_id'] == test_user_id), None)
        assert user_in_community_b is not None, "用户应该仍在社区B中"
        assert user_in_community_b['role'] == 'manager', "用户在社区B的角色应该仍是manager"

        # 检查社区C（应该仍有该用户，角色为staff）
        staff_response_c = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_c_id}
        )
        staff_list_c = staff_response_c.json()['data'].get('staff_members', [])
        user_in_community_c = next((s for s in staff_list_c if s['user_id'] == test_user_id), None)
        assert user_in_community_c is not None, "用户应该仍在社区C中"
        assert user_in_community_c['role'] == 'staff', "用户在社区C的角色应该仍是staff"

        print("✓ E2E移除测试通过：用户可从单个社区移除而不影响其他社区")

    def test_get_managed_communities_api_returns_correct_roles(self, test_server):
        """
        E2E测试：验证获取用户管理的社区API返回正确的角色信息
        业务规则：API应准确返回用户在每个社区的角色
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建多个测试用户
        user_a_id = self._create_test_user(base_url, '13800000005', '管理社区测试用户A')
        user_b_id = self._create_test_user(base_url, '13800000006', '管理社区测试用户B')

        # 创建多个社区
        community_x_id = self._create_test_community(base_url, admin_headers, '管理测试社区X')
        community_y_id = self._create_test_community(base_url, admin_headers, '管理测试社区Y')
        community_z_id = self._create_test_community(base_url, admin_headers, '管理测试社区Z')

        # 设置复杂的角色分配场景
        # 用户A: X社区为staff, Y社区为manager
        # 用户B: Y社区为staff, Z社区为manager
        assignments = [
            (user_a_id, community_x_id, 'staff'),
            (user_a_id, community_y_id, 'manager'),
            (user_b_id, community_y_id, 'staff'),
            (user_b_id, community_z_id, 'manager')
        ]

        for user_id, community_id, role in assignments:
            response = requests.post(f'{base_url}/api/community/add-staff',
                headers=admin_headers,
                json={
                    'community_id': community_id,
                    'user_ids': [user_id],
                    'role': role
                }
            )
            assert response.status_code == 200 and response.json().get('code') == 1, \
                f"为用户{user_id}分配到社区{community_id}角色{role}失败"

        # 检查用户A管理的社区
        user_a_login = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13800000005',
            'password': 'Test123456'
        })
        user_a_token = user_a_login.json()['data']['token']
        user_a_headers = {'Authorization': f'Bearer {user_a_token}'}

        managed_resp_a = requests.get(f'{base_url}/api/user/managed-communities',
            headers=user_a_headers
        )
        assert managed_resp_a.status_code == 200
        managed_data_a = managed_resp_a.json()['data']

        assert len(managed_data_a['communities']) == 2, "用户A应该管理2个社区"

        # 验证用户A在每个社区的角色
        communities_a = {c['community_id']: c['role_in_community'] for c in managed_data_a['communities']}
        assert community_x_id in communities_a, "用户A应该在社区X中"
        assert community_y_id in communities_a, "用户A应该在社区Y中"
        assert communities_a[community_x_id] == 'staff', f"用户A在社区X的角色应该是staff，实际是{communities_a[community_x_id]}"
        assert communities_a[community_y_id] == 'manager', f"用户A在社区Y的角色应该是manager，实际是{communities_a[community_y_id]}"

        # 检查用户B管理的社区
        user_b_login = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13800000006',
            'password': 'Test123456'
        })
        user_b_token = user_b_login.json()['data']['token']
        user_b_headers = {'Authorization': f'Bearer {user_b_token}'}

        managed_resp_b = requests.get(f'{base_url}/api/user/managed-communities',
            headers=user_b_headers
        )
        assert managed_resp_b.status_code == 200
        managed_data_b = managed_resp_b.json()['data']

        assert len(managed_data_b['communities']) == 2, "用户B应该管理2个社区"

        # 验证用户B在每个社区的角色
        communities_b = {c['community_id']: c['role_in_community'] for c in managed_data_b['communities']}
        assert community_y_id in communities_b, "用户B应该在社区Y中"
        assert community_z_id in communities_b, "用户B应该在社区Z中"
        assert communities_b[community_y_id] == 'staff', f"用户B在社区Y的角色应该是staff，实际是{communities_b[community_y_id]}"
        assert communities_b[community_z_id] == 'manager', f"用户B在社区Z的角色应该是manager，实际是{communities_b[community_z_id]}"

        print("✓ E2E管理社区API测试通过：正确返回用户在各社区的角色")