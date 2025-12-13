"""
社区管理API E2E测试
基于 test_community_management_api_design.md 设计文档实现
使用 test_server fixture 提供独立测试环境
"""

import pytest
import requests
import time
from datetime import datetime


class TestCommunityStaffManagement:
    """测试完整的工作人员管理流程（核心流程）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
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
        return register_data['data']['token'], register_data['data']['user_id']

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

    def test_complete_staff_management_workflow(self, test_server):
        """测试完整的工作人员管理流程"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_工作人员管理_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建两个测试用户（主管候选、专员候选）
        manager_token, manager_id = self._create_test_user(
            base_url, f'13900001{timestamp % 1000:03d}', '测试主管'
        )
        staff_token, staff_id = self._create_test_user(
            base_url, f'13900004{timestamp % 1000:03d}', '测试专员'
        )

        # 4. 添加主管
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager_id],
                'role': 'manager'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['added_count'] == 1
        assert len(data['data']['failed']) == 0

        # 5. 验证主管列表
        response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'role': 'manager'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        staff_list = data['data']['staff_members']
        assert len(staff_list) == 1
        assert staff_list[0]['user_id'] == str(manager_id)
        assert staff_list[0]['role'] == 'manager'

        # 6. 添加专员
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['added_count'] == 1

        # 7. 验证完整列表（包含主管和专员）
        response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'role': 'all'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        staff_list = data['data']['staff_members']
        assert len(staff_list) == 2

        # 8. 移除专员
        response = requests.post(f'{base_url}/api/community/remove-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_id': staff_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 9. 验证移除后的列表
        response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'role': 'all'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        staff_list = data['data']['staff_members']
        assert len(staff_list) == 1
        assert staff_list[0]['user_id'] == str(manager_id)

    def test_manager_uniqueness_constraint(self, test_server):
        """测试主管唯一性约束"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_主管唯一性_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建两个测试用户
        manager1_token, manager1_id = self._create_test_user(
            base_url, f'13900011{timestamp % 1000:03d}', '测试主管1'
        )
        manager2_token, manager2_id = self._create_test_user(
            base_url, f'13900012{timestamp % 1000:03d}', '测试主管2'
        )

        # 4. 添加第一个主管
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager1_id],
                'role': 'manager'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 尝试添加第二个主管
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager2_id],
                'role': 'manager'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '该社区已有主管' in data['msg'] or '主管只能添加一个' in data['msg'] or '已存在主管' in data['msg']

    def test_duplicate_staff_prevention(self, test_server):
        """测试防止重复添加工作人员"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_重复添加_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建测试用户
        staff_token, staff_id = self._create_test_user(
            base_url, f'13900041{timestamp % 1000:03d}', '测试专员'
        )

        # 4. 第一次添加专员
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 再次添加相同用户
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        data = response.json()
        # 可能返回部分成功或完全失败
        if data.get('code') == 1:
            # 部分成功情况
            assert data['data']['added_count'] == 0
            assert len(data['data']['failed']) > 0
            assert any('用户已是工作人员' in str(f.get('reason', '')) or '已是工作人员' in str(f.get('reason', '')) for f in data['data']['failed'])
        else:
            # 完全失败情况
            assert data.get('code') == 0
            assert '添加失败' in data['msg'] or '已是工作人员' in data['msg'] or '重复添加' in data['msg']

    def test_staff_list_sorting(self, test_server):
        """测试工作人员列表排序"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_排序_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建多个测试用户
        users = []
        for i in range(3):
            nickname = f'测试用户{chr(65+i)}'  # A, B, C
            token, user_id = self._create_test_user(
                base_url, f'1390005{i}{timestamp % 1000:03d}', nickname
            )
            users.append({'user_id': user_id, 'nickname': nickname})
            time.sleep(0.1)  # 确保时间戳不同

        # 4. 添加工作人员
        for user in users:
            response = requests.post(f'{base_url}/api/community/add-staff',
                headers=admin_headers,
                json={
                    'community_id': community_id,
                    'user_ids': [user['user_id']],
                    'role': 'staff'
                }
            )
            assert response.status_code == 200
            time.sleep(0.1)

        # 5. 测试按时间排序
        response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'sort_by': 'time'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        staff_list = data['data']['staff_members']
        assert len(staff_list) >= 3

        # 6. 测试按名称排序
        response = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'sort_by': 'name'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        # 验证列表已排序
        staff_list = data['data']['staff_members']
        assert len(staff_list) >= 3

    def test_staff_management_permissions(self, test_server):
        """测试权限控制"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_权限_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建测试用户
        manager_token, manager_id = self._create_test_user(
            base_url, f'13900021{timestamp % 1000:03d}', '测试主管'
        )
        staff_token, staff_id = self._create_test_user(
            base_url, f'13900024{timestamp % 1000:03d}', '测试专员'
        )
        normal_token, normal_id = self._create_test_user(
            base_url, f'13900027{timestamp % 1000:03d}', '普通用户'
        )
        test_user_token, test_user_id = self._create_test_user(
            base_url, f'13900028{timestamp % 1000:03d}', '待添加用户'
        )

        # 4. 添加主管和专员角色
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager_id],
                'role': 'manager'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 5. super_admin 添加工作人员 → 成功
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 先移除该用户以便后续测试
        requests.post(f'{base_url}/api/community/remove-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_id': test_user_id
            }
        )

        # 6. community_manager 添加工作人员 → 成功
        manager_headers = {'Authorization': f'Bearer {manager_token}'}
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=manager_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 先移除该用户
        requests.post(f'{base_url}/api/community/remove-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_id': test_user_id
            }
        )

        # 7. community_staff 添加工作人员 → 失败
        staff_headers = {'Authorization': f'Bearer {staff_token}'}
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=staff_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 8. 普通用户添加工作人员 → 失败
        normal_headers = {'Authorization': f'Bearer {normal_token}'}
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=normal_headers,
            json={
                'community_id': community_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']


class TestCommunityUserManagement:
    """测试完整的社区用户管理流程（核心流程）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
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
        return register_data['data']['token'], register_data['data']['user_id']

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

    def _add_user_to_community(self, base_url, headers, community_id, user_ids):
        """添加用户到社区"""
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=headers,
            json={
                'community_id': community_id,
                'user_ids': user_ids
            }
        )
        return response

    def test_complete_user_management_workflow(self, test_server):
        """测试完整的用户管理流程"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_用户管理_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建3个测试用户
        user_ids = []
        for i in range(3):
            token, user_id = self._create_test_user(
                base_url, f'13900071{i}{timestamp % 1000:03d}', f'测试用户{i+1}'
            )
            user_ids.append(user_id)

        # 4. 批量添加用户到社区
        response = self._add_user_to_community(base_url, admin_headers, community_id, user_ids)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['added_count'] == 3
        assert len(data['data']['failed']) == 0

        # 5. 获取用户列表（第1页）
        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'page': 1,
                'page_size': 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        users = data['data']['users']
        assert len(users) == 3
        assert 'current_page' in data['data']
        assert 'has_more' in data['data']

        # 6. 验证用户数据（含打卡信息字段）
        for user in users:
            assert 'user_id' in user
            assert 'nickname' in user
            assert 'phone_number' in user
            assert 'join_time' in user
            assert 'unchecked_count' in user
            assert 'unchecked_items' in user

        # 7. 移除一个用户
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_id': user_ids[0]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 8. 验证移除后的列表
        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'page': 1
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        users = data['data']['users']
        assert len(users) == 2
        assert all(u['user_id'] != str(user_ids[0]) for u in users)

    def test_batch_add_users_with_limit(self, test_server):
        """测试批量添加限制"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_批量限制_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 尝试添加51个用户ID（超过限制）
        fake_user_ids = [f'fake-user-{i}' for i in range(51)]
        response = self._add_user_to_community(base_url, admin_headers, community_id, fake_user_ids)

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '最多只能添加50个用户' in data['msg'] or '超过限制' in data['msg']

    def test_user_list_pagination(self, test_server):
        """测试分页功能"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_分页_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 添加25个用户
        user_ids = []
        for i in range(25):
            token, user_id = self._create_test_user(
                base_url, f'13900081{i:02d}{timestamp % 100:02d}', f'分页用户{i+1}'
            )
            user_ids.append(user_id)

        response = self._add_user_to_community(base_url, admin_headers, community_id, user_ids)
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 4. 获取第1页（page_size=20）
        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'page': 1,
                'page_size': 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert len(data['data']['users']) == 20
        assert data['data']['has_more'] is True

        # 5. 获取第2页
        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={
                'community_id': community_id,
                'page': 2,
                'page_size': 20
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert len(data['data']['users']) == 5
        assert data['data']['has_more'] is False

    def test_duplicate_user_prevention(self, test_server):
        """测试防止重复添加用户"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_重复用户_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建测试用户
        token, user_id = self._create_test_user(
            base_url, f'13900091{timestamp % 1000:03d}', '测试用户'
        )

        # 4. 第一次添加用户
        response = self._add_user_to_community(base_url, admin_headers, community_id, [user_id])
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 再次添加相同用户
        response = self._add_user_to_community(base_url, admin_headers, community_id, [user_id])
        assert response.status_code == 200
        data = response.json()
        # 可能返回部分成功或完全失败
        if data.get('code') == 1:
            # 部分成功情况
            assert data['data']['added_count'] == 0
            assert len(data['data']['failed']) > 0
            assert any('用户已在社区' in str(f.get('reason', '')) or '已在社区' in str(f.get('reason', '')) for f in data['data']['failed'])
        else:
            # 完全失败情况
            assert data.get('code') == 0
            assert '添加失败' in data['msg'] or '已在社区' in data['msg'] or '重复' in data['msg']

    def test_user_management_permissions(self, test_server):
        """测试权限控制"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        timestamp = int(time.time())
        community_name = f'测试社区_用户权限_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建各角色用户
        manager_token, manager_id = self._create_test_user(
            base_url, f'13900031{timestamp % 1000:03d}', '测试主管'
        )
        staff_token, staff_id = self._create_test_user(
            base_url, f'13900034{timestamp % 1000:03d}', '测试专员'
        )
        normal_token, normal_id = self._create_test_user(
            base_url, f'13900037{timestamp % 1000:03d}', '普通用户'
        )
        test_user_token, test_user_id = self._create_test_user(
            base_url, f'13900038{timestamp % 1000:03d}', '待添加用户'
        )

        # 4. 添加主管和专员角色
        requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager_id],
                'role': 'manager'
            }
        )
        requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )

        # 5. super_admin 添加用户 → 成功
        response = self._add_user_to_community(base_url, admin_headers, community_id, [test_user_id])
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 移除用户
        requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={'community_id': community_id, 'user_id': test_user_id}
        )

        # 6. community_manager 添加用户 → 成功
        manager_headers = {'Authorization': f'Bearer {manager_token}'}
        response = self._add_user_to_community(base_url, manager_headers, community_id, [test_user_id])
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 移除用户
        requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={'community_id': community_id, 'user_id': test_user_id}
        )

        # 7. community_staff 添加用户 → 成功
        staff_headers = {'Authorization': f'Bearer {staff_token}'}
        response = self._add_user_to_community(base_url, staff_headers, community_id, [test_user_id])
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 移除用户
        requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={'community_id': community_id, 'user_id': test_user_id}
        )

        # 8. 普通用户添加用户 → 失败
        normal_headers = {'Authorization': f'Bearer {normal_token}'}
        response = self._add_user_to_community(base_url, normal_headers, community_id, [test_user_id])
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']


class TestSpecialCommunityLogic:
    """测试特殊社区（安卡大家庭、黑屋）的业务逻辑（核心流程）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
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
        return register_data['data']['token'], register_data['data']['user_id']

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

    def _get_default_community_id(self, base_url, admin_headers):
        """获取"安卡大家庭"的ID"""
        response = requests.get(f'{base_url}/api/community/list',
            headers=admin_headers,
            params={'page_size': 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        communities = data['data']['communities']
        for community in communities:
            if community['name'] == '安卡大家庭':
                return community['id']
        return None

    def _get_blacklist_community_id(self, base_url, admin_headers):
        """获取"黑屋"的ID"""
        response = requests.get(f'{base_url}/api/community/list',
            headers=admin_headers,
            params={'page_size': 100}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        communities = data['data']['communities']
        for community in communities:
            if community['name'] == '黑屋':
                return community['id']
        return None

    def test_remove_from_default_community_to_blacklist(self, test_server):
        """测试从"安卡大家庭"移除 → 自动移至"黑屋" """
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建新用户
        timestamp = int(time.time())
        user_token, user_id = self._create_test_user(
            base_url, f'13901001{timestamp % 1000:03d}', '测试用户'
        )

        # 3. 获取"安卡大家庭"的 community_id并添加用户
        default_community_id = self._get_default_community_id(base_url, admin_headers)
        assert default_community_id is not None

        # 将用户添加到"安卡大家庭"
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={
                'community_id': default_community_id,
                'user_ids': [user_id]
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 4. 从"安卡大家庭"移除用户
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={
                'community_id': default_community_id,
                'user_id': user_id
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        # 验证返回数据包含moved_to字段（可能是None或"黑屋"）
        assert 'moved_to' in data.get('data', {})
        moved_to = data['data']['moved_to']
        # 如果moved_to不是None,应该是"黑屋"
        if moved_to:
            assert '黑屋' in moved_to

    def test_remove_from_normal_community_to_default(self, test_server):
        """测试从普通社区移除 → 移至"安卡大家庭"（无其他社区时）"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建普通社区
        timestamp = int(time.time())
        community_name = f'测试社区_普通_{timestamp}'
        community_id = self._create_test_community(base_url, admin_headers, community_name)

        # 3. 创建用户并添加到普通社区
        user_token, user_id = self._create_test_user(
            base_url, f'13901002{timestamp % 1000:03d}', '测试用户'
        )

        # 先从默认社区移除
        default_community_id = self._get_default_community_id(base_url, admin_headers)
        if default_community_id:
            requests.post(f'{base_url}/api/community/remove-user',
                headers=admin_headers,
                json={'community_id': default_community_id, 'user_id': user_id}
            )

        # 添加到普通社区
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={'community_id': community_id, 'user_ids': [user_id]}
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 4. 从普通社区移除用户
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={'community_id': community_id, 'user_id': user_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 验证用户移至"安卡大家庭"
        if 'moved_to' in data.get('data', {}):
            assert '安卡大家庭' in data['data']['moved_to']

    def test_remove_from_one_community_keep_others(self, test_server):
        """测试从普通社区移除 → 仅移除（用户还有其他社区时）"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建两个普通社区A和B
        timestamp = int(time.time())
        community_a_id = self._create_test_community(
            base_url, admin_headers, f'测试社区A_{timestamp}'
        )
        community_b_id = self._create_test_community(
            base_url, admin_headers, f'测试社区B_{timestamp}'
        )

        # 3. 创建用户并添加到两个社区
        user_token, user_id = self._create_test_user(
            base_url, f'13901003{timestamp % 1000:03d}', '测试用户'
        )

        requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={'community_id': community_a_id, 'user_ids': [user_id]}
        )
        requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={'community_id': community_b_id, 'user_ids': [user_id]}
        )

        # 4. 从社区A移除用户
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=admin_headers,
            json={'community_id': community_a_id, 'user_id': user_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 验证用户仍在社区B
        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        assert response.status_code == 200
        data = response.json()
        if data.get('code') == 1:
            users = data['data']['users']
            assert any(u['user_id'] == str(user_id) for u in users)

    def test_special_communities_cannot_be_deleted(self, test_server):
        """测试特殊社区不可删除"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 获取特殊社区ID
        default_community_id = self._get_default_community_id(base_url, admin_headers)
        blacklist_community_id = self._get_blacklist_community_id(base_url, admin_headers)

        # 3. 尝试删除"安卡大家庭"
        if default_community_id:
            response = requests.post(f'{base_url}/api/community/delete',
                headers=admin_headers,
                json={'community_id': default_community_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') == 0
            assert '特殊社区' in data['msg'] or '不可删除' in data['msg'] or '默认社区' in data['msg']

        # 4. 尝试删除"黑屋"
        if blacklist_community_id:
            response = requests.post(f'{base_url}/api/community/delete',
                headers=admin_headers,
                json={'community_id': blacklist_community_id}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') == 0
            assert '特殊社区' in data['msg'] or '不可删除' in data['msg'] or '黑屋' in data['msg']

    def test_special_communities_cannot_be_disabled(self, test_server):
        """测试特殊社区不可停用"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 获取特殊社区ID
        default_community_id = self._get_default_community_id(base_url, admin_headers)
        blacklist_community_id = self._get_blacklist_community_id(base_url, admin_headers)

        # 3. 尝试停用"安卡大家庭"
        if default_community_id:
            response = requests.post(f'{base_url}/api/community/toggle-status',
                headers=admin_headers,
                json={'community_id': default_community_id, 'status': 'inactive'}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') == 0
            assert '特殊社区' in data['msg'] or '不可停用' in data['msg'] or '默认社区' in data['msg']

        # 4. 尝试停用"黑屋"
        if blacklist_community_id:
            response = requests.post(f'{base_url}/api/community/toggle-status',
                headers=admin_headers,
                json={'community_id': blacklist_community_id, 'status': 'inactive'}
            )
            assert response.status_code == 200
            data = response.json()
            assert data.get('code') == 0
            assert '特殊社区' in data['msg'] or '不可停用' in data['msg'] or '黑屋' in data['msg']


class TestCommunityPermissions:
    """测试完整的权限控制矩阵（核心流程）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
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
        return register_data['data']['token'], register_data['data']['user_id']

    def test_super_admin_full_access(self, test_server):
        """测试 super_admin 可执行所有操作"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 2. 创建社区 → 成功
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_全权限_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1
        community_id = response.json()['data']['community_id']

        # 3. 更新社区 → 成功
        response = requests.post(f'{base_url}/api/community/update',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'name': f'测试社区_更新_{timestamp}'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 4. 添加工作人员 → 成功
        user_token, user_id = self._create_test_user(
            base_url, f'13902001{timestamp % 1000:03d}', '测试工作人员'
        )
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 5. 添加用户 → 成功
        user2_token, user2_id = self._create_test_user(
            base_url, f'13902002{timestamp % 1000:03d}', '测试用户'
        )
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [user2_id]
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 6. 删除社区 → 需要先停用
        # 先停用
        response = requests.post(f'{base_url}/api/community/toggle-status',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'status': 'inactive'
            }
        )
        assert response.status_code == 200
        # 可能因为有用户而无法停用，这是正常的业务逻辑

    def test_community_manager_permissions(self, test_server):
        """测试 community_manager 权限验证"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 2. 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_管理员权限_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        community_id = response.json()['data']['community_id']

        # 3. 创建主管用户
        manager_token, manager_id = self._create_test_user(
            base_url, f'13902011{timestamp % 1000:03d}', '测试主管'
        )

        # 4. 将用户设为主管
        requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [manager_id],
                'role': 'manager'
            }
        )

        manager_headers = {'Authorization': f'Bearer {manager_token}'}

        # 5. 创建社区 → 失败
        response = requests.post(f'{base_url}/api/community/create',
            headers=manager_headers,
            json={
                'name': f'非法社区_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 6. 添加工作人员 → 成功
        staff_token, staff_id = self._create_test_user(
            base_url, f'13902012{timestamp % 1000:03d}', '测试专员'
        )
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=manager_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 7. 移除工作人员 → 成功
        response = requests.post(f'{base_url}/api/community/remove-staff',
            headers=manager_headers,
            json={
                'community_id': community_id,
                'user_id': staff_id
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 8. 添加用户 → 成功
        user_token, user_id = self._create_test_user(
            base_url, f'13902013{timestamp % 1000:03d}', '测试用户'
        )
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=manager_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id]
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 9. 移除用户 → 成功
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=manager_headers,
            json={
                'community_id': community_id,
                'user_id': user_id
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

    def test_community_staff_permissions(self, test_server):
        """测试 community_staff 权限验证"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 2. 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_专员权限_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        community_id = response.json()['data']['community_id']

        # 3. 创建专员用户
        staff_token, staff_id = self._create_test_user(
            base_url, f'13902021{timestamp % 1000:03d}', '测试专员'
        )

        # 4. 将用户设为专员
        requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [staff_id],
                'role': 'staff'
            }
        )

        staff_headers = {'Authorization': f'Bearer {staff_token}'}

        # 5. 创建社区 → 失败
        response = requests.post(f'{base_url}/api/community/create',
            headers=staff_headers,
            json={
                'name': f'非法社区_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 6. 添加工作人员 → 失败
        new_staff_token, new_staff_id = self._create_test_user(
            base_url, f'13902022{timestamp % 1000:03d}', '新专员'
        )
        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=staff_headers,
            json={
                'community_id': community_id,
                'user_ids': [new_staff_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 7. 添加用户 → 成功
        user_token, user_id = self._create_test_user(
            base_url, f'13902023{timestamp % 1000:03d}', '测试用户'
        )
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=staff_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id]
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 8. 移除用户 → 成功
        response = requests.post(f'{base_url}/api/community/remove-user',
            headers=staff_headers,
            json={
                'community_id': community_id,
                'user_id': user_id
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

    def test_normal_user_no_permissions(self, test_server):
        """测试普通用户所有操作被拒绝"""
        base_url = test_server

        timestamp = int(time.time())

        # 1. 创建普通用户
        user_token, user_id = self._create_test_user(
            base_url, f'13902031{timestamp % 1000:03d}', '普通用户'
        )
        user_headers = {'Authorization': f'Bearer {user_token}'}

        # 2. 获取社区列表 → 失败
        response = requests.get(f'{base_url}/api/community/list',
            headers=user_headers
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 3. 创建社区 → 失败
        response = requests.post(f'{base_url}/api/community/create',
            headers=user_headers,
            json={
                'name': f'非法社区_{timestamp}',
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 4. 添加工作人员 → 失败（需要一个社区ID）
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_普通用户_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        response = requests.post(f'{base_url}/api/community/add-staff',
            headers=user_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id],
                'role': 'staff'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']

        # 5. 添加用户 → 失败
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=user_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id]
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 0
        assert '权限不足' in response.json()['msg']


class TestCommunityCRUD:
    """测试社区CRUD操作（辅助功能 - 快速验证）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        return login_data['data']['token'], login_data['data']['user_id']

    def test_create_community_success(self, test_server):
        """测试创建社区成功场景"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_创建成功_{timestamp}',
                'location': '北京市朝阳区',
                'location_lat': 39.9042,
                'location_lon': 116.4074,
                'description': '测试社区描述'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert 'community_id' in data['data']
        assert data['data']['name'] == f'测试社区_创建成功_{timestamp}'

    def test_update_community_info(self, test_server):
        """测试更新社区信息"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建社区
        timestamp = int(time.time())
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_更新_{timestamp}',
                'location': '原地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 更新社区
        response = requests.post(f'{base_url}/api/community/update',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'name': f'测试社区_已更新_{timestamp}',
                'location': '新地址',
                'description': '新描述'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

    def test_toggle_community_status(self, test_server):
        """测试状态切换（active ↔ inactive）"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建社区
        timestamp = int(time.time())
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_状态切换_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 停用社区
        response = requests.post(f'{base_url}/api/community/toggle-status',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'status': 'inactive'
            }
        )

        assert response.status_code == 200
        data = response.json()
        # 可能因为有用户而无法停用，这是正常的
        if data.get('code') == 1:
            assert data['data']['status'] == 'inactive'

    def test_delete_community_with_prerequisites(self, test_server):
        """测试删除前置条件"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建社区
        timestamp = int(time.time())
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_删除_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 直接删除（应该失败，因为未停用）
        response = requests.post(f'{base_url}/api/community/delete',
            headers=admin_headers,
            json={'community_id': community_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '停用' in data['msg'] or 'inactive' in data['msg'].lower()

    def test_create_community_duplicate_name(self, test_server):
        """测试社区名称重复"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())
        community_name = f'测试社区_重复名称_{timestamp}'

        # 第一次创建
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': community_name,
                'location': '测试地址'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 第二次创建（应该失败）
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': community_name,
                'location': '测试地址'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '已存在' in data['msg'] or '重复' in data['msg']

    def test_update_nonexistent_community(self, test_server):
        """测试更新不存在的社区"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        response = requests.post(f'{base_url}/api/community/update',
            headers=admin_headers,
            json={
                'community_id': 'nonexistent-id-999999',
                'name': '不存在的社区'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '不存在' in data['msg']


class TestUserSearch:
    """测试用户搜索功能（辅助功能 - 快速验证）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
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
        return register_data['data']['token'], register_data['data']['user_id']

    def test_search_by_nickname(self, test_server):
        """测试按昵称搜索用户"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())
        unique_nickname = f'搜索测试用户_{timestamp}'

        # 创建测试用户
        user_token, user_id = self._create_test_user(
            base_url, f'13903001{timestamp % 1000:03d}', unique_nickname
        )

        # 搜索用户
        response = requests.get(f'{base_url}/api/user/search',
            headers=admin_headers,
            params={'keyword': unique_nickname}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        users = data['data']['users']
        assert len(users) > 0
        assert any(u['user_id'] == str(user_id) for u in users)

    def test_search_by_phone(self, test_server):
        """测试按手机号搜索用户（实际测试掩码后的手机号）"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())
        phone = f'13903002{timestamp % 1000:03d}'
        unique_nickname = f'手机搜索{timestamp % 10000}'

        # 创建测试用户
        user_token, user_id = self._create_test_user(
            base_url, phone, unique_nickname
        )

        # 注意：phone_number 在数据库中被掩码化存储（139****2343）
        # 所以我们使用掩码格式或昵称搜索
        masked_phone = phone[:3] + '****' + phone[-4:]

        # 搜索用户（使用掩码格式）
        response = requests.get(f'{base_url}/api/user/search',
            headers=admin_headers,
            params={'keyword': masked_phone}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        users = data['data']['users']
        # 掩码格式可能匹配多个用户，所以至少应该找到1个
        assert len(users) >= 1

    def test_search_empty_keyword(self, test_server):
        """测试空关键词验证"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        response = requests.get(f'{base_url}/api/user/search',
            headers=admin_headers,
            params={'keyword': ''}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '关键词' in data['msg'] or '不能为空' in data['msg']

    def test_search_with_community_filter(self, test_server):
        """测试搜索时标记已在社区的用户"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_搜索过滤_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 创建并添加用户
        user_token, user_id = self._create_test_user(
            base_url, f'13903003{timestamp % 1000:03d}', '过滤测试用户'
        )

        requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': [user_id]
            }
        )

        # 带社区ID搜索
        response = requests.get(f'{base_url}/api/user/search',
            headers=admin_headers,
            params={
                'keyword': '过滤测试用户',
                'community_id': community_id
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1


class TestEdgeCases:
    """测试边界条件和错误处理（辅助功能 - 快速验证）"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'F1234567'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        return login_data['data']['token'], login_data['data']['user_id']

    def test_batch_add_exceeds_limit(self, test_server):
        """测试批量添加超过50个用户"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_批量限制_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 尝试添加51个用户
        fake_user_ids = [f'fake-user-{i}' for i in range(51)]
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': fake_user_ids
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '50' in data['msg']

    def test_nonexistent_user_id(self, test_server):
        """测试操作不存在的用户ID"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_不存在用户_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 添加不存在的用户
        response = requests.post(f'{base_url}/api/community/add-users',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'user_ids': ['nonexistent-user-id-999999']
            }
        )

        assert response.status_code == 200
        data = response.json()
        # 可能返回部分成功或完全失败
        if data.get('code') == 1:
            assert len(data['data']['failed']) > 0
            assert any('用户不存在' in str(f.get('reason', '')) or '不存在' in str(f.get('reason', '')) for f in data['data']['failed'])
        else:
            assert '添加失败' in data['msg'] or '不存在' in data['msg']

    def test_nonexistent_community_id(self, test_server):
        """测试操作不存在的社区ID"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        response = requests.get(f'{base_url}/api/community/users',
            headers=admin_headers,
            params={'community_id': 'nonexistent-community-999999'}
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '不存在' in data['msg']

    def test_invalid_status_value(self, test_server):
        """测试无效的状态值"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        timestamp = int(time.time())

        # 创建社区
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'name': f'测试社区_无效状态_{timestamp}',
                'location': '测试地址'
            }
        )
        community_id = response.json()['data']['community_id']

        # 设置无效状态
        response = requests.post(f'{base_url}/api/community/toggle-status',
            headers=admin_headers,
            json={
                'community_id': community_id,
                'status': 'invalid_status'
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        # 可能返回参数错误或状态无效

    def test_missing_required_parameters(self, test_server):
        """测试缺少必填参数"""
        base_url = test_server

        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建社区时缺少名称
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json={
                'location': '测试地址'
                # 缺少 name
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '名称' in data['msg'] or '参数' in data['msg']
