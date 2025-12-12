"""
多社区角色分配功能的测试用例
用于验证用户可以同时在多个社区担任不同角色的功能
"""
import pytest
import requests
from datetime import datetime


class TestMultiCommunityRoleAssignment:
    """测试用户在多个社区担任不同角色的功能"""
    
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
            'code': '123456',
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
    
    def test_user_cannot_be_added_to_multiple_communities_currently(self, test_server):
        """
        RED: 测试当前系统是否阻止用户在多个社区任职
        这个测试应该会失败，因为当前实现不允许用户在多个社区任职
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000001', '测试用户A')
        
        # 创建两个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '社区A')
        community_b_id = self._create_test_community(base_url, admin_headers, '社区B')
        
        # 将用户添加到第一个社区
        response1 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get('code') == 1, f"添加到社区A失败: {data1}"
        
        # 尝试将同一用户添加到第二个社区 - 这里当前会失败，但在实现后应该成功
        response2 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'manager'  # 在第二个社区担任主管
            }
        )
        
        # RED: 测试当前行为 - 应该失败（因为唯一约束）
        assert response2.status_code == 200
        data2 = response2.json()
        # 当前实现会返回错误（因为唯一性约束），所以应该有failed记录
        assert data2.get('code') == 1, f"添加到社区B应该失败，但返回了: {data2}"
        # 这里我们验证当前系统确实阻止了多重角色分配
        assert 'failed' in data2.get('data', {}), "当前系统应阻止用户在多个社区任职"
        print("✓ 当前系统确实阻止了用户在多个社区任职（符合预期）")
    
    def test_user_can_be_assigned_different_roles_in_different_communities_after_implementation(self, test_server):
        """
        RED: 测试实现后用户能否在不同社区担任不同角色
        这个测试在当前实现下会失败，但在修改数据库约束后应该成功
        """
        base_url = test_server
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000002', '测试用户B')
        
        # 创建两个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '社区C')
        community_b_id = self._create_test_community(base_url, admin_headers, '社区D')
        
        # 将用户添加到第一个社区作为专员
        response1 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get('code') == 1, f"添加到社区C失败: {data1}"
        
        # 尝试将同一用户添加到第二个社区作为主管 - 在实现后这应该成功
        response2 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'manager'  # 在第二个社区担任主管
            }
        )
        
        # GREEN: 验证修改后此测试应该成功
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get('code') == 1, f"添加到社区D失败: {data2}"
        
        # 验证用户成功添加到第二个社区
        if 'failed' in data2.get('data', {}):
            failed_list = data2['data'].get('failed', [])
            # 如果仍有失败，检查是否是因为其他原因而不是唯一性约束
            print(f"注意: 添加到第二个社区有失败项: {failed_list}")
        
        # 验证用户在两个社区都有角色
        # 获取第一个社区的工作人员列表
        staff_response1 = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_a_id}
        )
        assert staff_response1.status_code == 200
        staff_data1 = staff_response1.json()
        staff_list1 = staff_data1['data'].get('staff_members', [])
        user_in_community_a = next((s for s in staff_list1 if s['user_id'] == test_user_id), None)
        assert user_in_community_a is not None, f"用户应该在社区A中，但未找到: {staff_list1}"
        assert user_in_community_a['role'] == 'staff', f"用户在社区A的角色应该是staff，实际是: {user_in_community_a['role']}"
        
        # 获取第二个社区的工作人员列表
        staff_response2 = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        assert staff_response2.status_code == 200
        staff_data2 = staff_response2.json()
        staff_list2 = staff_data2['data'].get('staff_members', [])
        user_in_community_b = next((s for s in staff_list2 if s['user_id'] == test_user_id), None)
        assert user_in_community_b is not None, f"用户应该在社区B中，但未找到: {staff_list2}"
        assert user_in_community_b['role'] == 'manager', f"用户在社区B的角色应该是manager，实际是: {user_in_community_b['role']}"
        
        print("✓ 用户成功在多个社区担任不同角色")
        
    def test_check_user_roles_in_multiple_communities(self, test_server):
        """
        RED: 测试检查用户在多个社区的角色信息
        在当前实现中，用户只能在一个社区任职，所以这个测试会验证当前状态
        """
        base_url = test_server
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        
        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000003', '测试用户C')
        
        # 创建一个社区
        community_id = self._create_test_community(base_url, admin_headers, '社区E')
        
        # 将用户添加为专员
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        
        # 获取用户在社区的信息 - 验证当前角色
        user_info_response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id
            }
        )
        assert user_info_response.status_code == 200
        user_info = user_info_response.json()
        assert user_info.get('code') == 1
        staff_list = user_info['data'].get('staff_members', [])
        found_user = next((s for s in staff_list if s['user_id'] == test_user_id), None)
        assert found_user is not None, "用户应该在社区工作人员列表中"
        assert found_user['role'] == 'staff', "用户角色应该是专员"
        
        print("✓ 当前系统中用户角色信息正确")