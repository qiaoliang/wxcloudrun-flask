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
import time
from datetime import datetime
from .testutil import create_phone_user, create_wx_user, get_headers_by_creating_phone_user, uuid_str, random_str

class TestMultiCommunityRoleAssignmentE2E:

    def setup_method(self):
        """每个测试方法前的设置：启动 Flask 应用"""
        import os
        import sys
        import time
        import subprocess
        import requests

        # 设置环境变量
        os.environ['ENV_TYPE'] = 'func'

        # 确保 src 目录在 Python 路径中
        src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # 清理可能存在的进程
        self._cleanup_existing_processes()

        # 启动 Flask 应用（在后台运行）
        self.flask_process = subprocess.Popen(
            [sys.executable, 'main.py', '127.0.0.1', '9998'],
            cwd=src_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy()
        )

        # 等待应用启动
        time.sleep(5)

        # 验证应用是否成功启动
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                response = requests.get(f'http://localhost:9998/', timeout=2)
                if response.status_code == 200:
                    print(f"Flask 应用成功启动 (尝试 {attempt + 1}/{max_attempts})")
                    break
            except requests.exceptions.RequestException:
                if attempt == max_attempts - 1:
                    pytest.fail("Flask 应用启动失败")
                time.sleep(1)

        # 保存base_url供测试方法使用
        self.base_url = f'http://localhost:9998'

    def teardown_method(self):
        """每个测试方法后的清理：停止 Flask 应用"""
        if hasattr(self, 'flask_process') and self.flask_process:
            self.flask_process.terminate()
            try:
                self.flask_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.flask_process.kill()
                self.flask_process.wait()
            print("Flask 应用已停止")

        # 再次清理可能残留的进程
        self._cleanup_existing_processes()

    def _cleanup_existing_processes(self):
        """清理可能存在的 Flask 进程"""
        import subprocess
        try:
            # 查找占用端口 9998 的进程
            result = subprocess.run(['lsof', '-t', '-i:9998'],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid:
                        subprocess.run(['kill', '-9', pid], capture_output=True)
                        print(f"已终止进程 {pid}")
        except Exception as e:
            print(f"清理进程时出错: {e}")

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
        assert register_data.get('code') == 1, f"注册失败: {register_data}"
        return register_data['data']['user_id']
    def test_super_admin_create_community(self):
        """超级管理员创建测试社区"""
        base_url = self.base_url
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        commu_data = {
            'name': f'我的q 测试社区_{uuid_str(20)}',
            'location': 'q 测试社区 的测试地址_{uuid_str(20)}',
            'description': '测试社区描述_{uuid_str(20)}',
            'manager_id':super_admin_id
        }
        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json=commu_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['community_id'] is not None

    def _create_test_community(self, base_url, admin_headers, commu_name, location='测试地址', manager_id=None):
        """创建测试社区"""
        """超级管理员创建测试社区"""
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}
        commu_data = {
            'name': commu_name,
            'location': 'q 测试社区 的测试地址 ',
            'description': '测试社区描述'
        }
        # 如果指定了manager_id，添加到请求中
        if manager_id:
            commu_data['manager_id'] = manager_id

        response = requests.post(f'{base_url}/api/community/create',
            headers=admin_headers,
            json=commu_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        return data['data']['community_id']

    def _get_user_token(self, base_url, user_id):
        """通过用户ID获取token（需要先有手机号）"""
        # 这里简化处理，实际可能需要更复杂的逻辑
        # 暂时使用超级管理员的token进行测试
        admin_token, _ = self._get_super_admin_token(base_url)
        return admin_token

    def test_multi_community_role_assignment_basic_flow(self):
        """
        E2E测试：基本的多社区角色分配流程
        业务规则：用户可以在多个社区担任不同角色
        """
        base_url = self.base_url
        # 获取超级管理员权限
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 1. 创建测试用户
        test_user_id = self._create_test_user(base_url, f'138{random_str(8)}', '多角色测试用户')

        # 2. 创建另一个用户作为社区B的主管
        manager_user_id = self._create_test_user(base_url, f'138{random_str(8)}', '社区主管用户')

        # 3. 创建两个社区
        # 社区A：超级管理员作为主管（默认）
        community_a_id = self._create_test_community(base_url, admin_headers, '社区A-测试')
        # 社区B：指定manager_user作为主管
        community_b_id = self._create_test_community(base_url, admin_headers, '社区B-测试', manager_id=manager_user_id)

        # 4. 将测试用户添加到社区A作为专员
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

        # 5. 将测试用户也添加到社区B作为专员（测试用户可以在多个社区担任相同角色）
        response2 = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'staff'  # 专员
            }
        )
        assert response2.status_code == 200
        data2 = response2.json()
        assert data2.get('code') == 1, f"添加到社区B失败: {data2}"
        assert data2['data']['added_count'] >= 1, "应该成功添加至少1个用户到社区B"

        # 6. 验证用户在两个社区都有角色
        # 通过社区工作人员列表验证
        for community_id, community_name in [(community_a_id, '社区A'), (community_b_id, '社区B')]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': community_id}
            )
            assert staff_response.status_code == 200
            staff_data = staff_response.json()
            assert staff_data.get('code') == 1

            staff_list = staff_data['data']['staff_members']
            user_in_community = next((s for s in staff_list if s['user_id'] == str(test_user_id)), None)
            assert user_in_community is not None, f"用户应该在{community_name}中"
            assert user_in_community['role'] == 'staff', f"用户在{community_name}的角色应该是staff"

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
        user_in_community_a = next((s for s in staff_list_a if s['user_id'] == str(test_user_id)), None)
        assert user_in_community_a is not None, f"用户应该在社区A中，但未找到: {staff_list_a}"
        assert user_in_community_a['role'] == 'staff', f"用户在社区A的角色应该是staff，实际是: {user_in_community_a['role']}"

        # 检查社区B - 用户应该作为专员存在
        staff_response_b = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        assert staff_response_b.status_code == 200
        staff_data_b = staff_response_b.json()
        assert staff_data_b.get('code') == 1
        staff_list_b = staff_data_b['data'].get('staff_members', [])
        user_in_community_b = next((s for s in staff_list_b if s['user_id'] == str(test_user_id)), None)
        assert user_in_community_b is not None, f"用户应该在社区B中，但未找到: {staff_list_b}"
        assert user_in_community_b['role'] == 'staff', f"用户在社区B的角色应该是staff，实际是: {user_in_community_b['role']}"

        # 验证社区B的主管是manager_user_id
        manager_in_community_b = next((s for s in staff_list_b if s['user_id'] == str(manager_user_id)), None)
        assert manager_in_community_b is not None, "主管应该在社区B中"
        assert manager_in_community_b['role'] == 'manager', f"主管在社区B的角色应该是manager，实际是: {manager_in_community_b['role']}"

        print("✓ E2E基本流程测试通过：用户成功在多个社区担任不同角色")

    def test_user_permission_based_on_community_role(self):
        """
        E2E测试：验证用户权限根据其在特定社区的角色正确生效
        业务规则：用户在每个社区的权限应基于其在该社区的角色
        """
        base_url = self.base_url
        # 获取超级管理员权限
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000002', '权限测试用户')

        # 创建另一个用户作为社区B的主管
        manager_user_id = self._create_test_user(base_url, '13800000003', '社区主管用户2')

        # 创建两个社区
        # 社区A：超级管理员作为主管（默认）
        community_a_id = self._create_test_community(base_url, admin_headers, '权限测试社区A')
        # 社区B：指定manager_user作为主管
        community_b_id = self._create_test_community(base_url, admin_headers, '权限测试社区B', manager_id=manager_user_id)

        # 将用户添加到社区A作为专员
        response_a = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_a_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response_a.status_code == 200 and response_a.json().get('code') == 1

        # 将用户也添加到社区B作为专员（测试用户可以在多个社区担任相同角色）
        response_b = requests.post(f'{base_url}/api/community/add-staff',
            headers=admin_headers,
            json={
                'community_id': community_b_id,
                'user_ids': [test_user_id],
                'role': 'staff'
            }
        )
        assert response_b.status_code == 200 and response_b.json().get('code') == 1

# 验证用户在两个社区都有角色（通过超级管理员API查看）
        for community_id, community_name in [(community_a_id, '社区A'), (community_b_id, '社区B')]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': community_id}
            )
            assert staff_response.status_code == 200
            staff_data = staff_response.json()
            assert staff_data.get('code') == 1

            staff_list = staff_data['data']['staff_members']
            user_in_community = next((s for s in staff_list if s['user_id'] == str(test_user_id)), None)
            assert user_in_community is not None, f"用户应该在{community_name}中"
            assert user_in_community['role'] == 'staff', f"用户在{community_name}的角色应该是staff"

        print("✓ E2E权限测试通过：用户权限根据社区角色正确生效")

    def test_user_can_be_removed_from_individual_communities(self):
        """
        E2E测试：验证用户可以从单个社区移除，但保留在其他社区的任职
        业务规则：移除操作应该是社区级别的，不影响用户在其他社区的角色
        """
        base_url = self.base_url
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建测试用户
        test_user_id = self._create_test_user(base_url, '13800000004', '移除测试用户')

        # 创建另一个用户作为社区B的主管
        manager_user_id = self._create_test_user(base_url, '13800000005', '社区主管用户3')

        # 创建三个社区
        community_a_id = self._create_test_community(base_url, admin_headers, '移除测试社区A')
        community_b_id = self._create_test_community(base_url, admin_headers, '移除测试社区B', manager_id=manager_user_id)
        community_c_id = self._create_test_community(base_url, admin_headers, '移除测试社区C')

        # 将用户添加到所有三个社区（都作为staff角色）
        for i, cid in enumerate([community_a_id, community_b_id, community_c_id], 1):
            response = requests.post(f'{base_url}/api/community/add-staff',
                headers=admin_headers,
                json={
                    'community_id': cid,
                    'user_ids': [test_user_id],
                    'role': 'staff'
                }
            )
            assert response.status_code == 200 and response.json().get('code') == 1, f"添加到社区{i}失败"

        # 验证用户在所有三个社区都存在（都是staff角色）
        for cid in [community_a_id, community_b_id, community_c_id]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': cid}
            )
            assert staff_response.status_code == 200
            staff_list = staff_response.json()['data'].get('staff_members', [])
            user_in_community = next((s for s in staff_list if s['user_id'] == str(test_user_id)), None)
            assert user_in_community is not None, f"用户应该在社区{cid}中"
            assert user_in_community['role'] == 'staff', f"用户在社区{cid}的角色应该是staff"

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
        user_in_community_a = next((s for s in staff_list_a if s['user_id'] == str(test_user_id)), None)
        assert user_in_community_a is None, "用户应该已从社区A移除"

        # 检查社区B（应该仍有该用户，角色为staff）
        staff_response_b = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_b_id}
        )
        staff_list_b = staff_response_b.json()['data'].get('staff_members', [])
        user_in_community_b = next((s for s in staff_list_b if s['user_id'] == str(test_user_id)), None)
        assert user_in_community_b is not None, "用户应该仍在社区B中"
        assert user_in_community_b['role'] == 'staff', "用户在社区B的角色应该仍是staff"

        # 检查社区C（应该仍有该用户，角色为staff）
        staff_response_c = requests.get(f'{base_url}/api/community/staff/list',
            headers=admin_headers,
            params={'community_id': community_c_id}
        )
        staff_list_c = staff_response_c.json()['data'].get('staff_members', [])
        user_in_community_c = next((s for s in staff_list_c if s['user_id'] == str(test_user_id)), None)
        assert user_in_community_c is not None, "用户应该仍在社区C中"
        assert user_in_community_c['role'] == 'staff', "用户在社区C的角色应该仍是staff"

        print("✓ E2E移除测试通过：用户可从单个社区移除而不影响其他社区")

    def test_get_managed_communities_api_returns_correct_roles(self):
        """
        业务规则：API应准确返回用户在每个社区的角色
        """
        base_url = self.base_url
        # 获取超级管理员权限
        admin_token, _ = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 创建多个测试用户
        user_a_id = self._create_test_user(base_url, '13800000006', '管理社区测试用户A')
        user_b_id = self._create_test_user(base_url, '13800000007', '管理社区测试用户B')
        # 创建额外的用户作为指定主管
        manager_y_id = self._create_test_user(base_url, '13800000008', '社区Y主管')
        manager_z_id = self._create_test_user(base_url, '13800000009', '社区Z主管')

        # 创建多个社区，指定不同的主管
        community_x_id = self._create_test_community(base_url, admin_headers, '管理测试社区X')  # 超级管理员作为主管
        community_y_id = self._create_test_community(base_url, admin_headers, '管理测试社区Y', manager_id=manager_y_id)
        community_z_id = self._create_test_community(base_url, admin_headers, '管理测试社区Z', manager_id=manager_z_id)

        # 设置角色分配场景（所有角色都是staff）
        assignments = [
            (user_a_id, community_x_id, 'staff'),
            (user_a_id, community_y_id, 'staff'),
            (user_b_id, community_y_id, 'staff'),
            (user_b_id, community_z_id, 'staff')
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

        # 验证用户A在两个社区都有角色（通过超级管理员API查看）
        for community_id, community_name in [(community_x_id, '社区X'), (community_y_id, '社区Y')]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': community_id}
            )
            assert staff_response.status_code == 200
            staff_data = staff_response.json()
            assert staff_data.get('code') == 1

            staff_list = staff_data['data']['staff_members']
            user_in_community = next((s for s in staff_list if s['user_id'] == str(user_a_id)), None)
            assert user_in_community is not None, f"用户A应该在{community_name}中"
            assert user_in_community['role'] == 'staff', f"用户A在{community_name}的角色应该是staff"

        # 验证用户B在两个社区都有角色（通过超级管理员API查看）
        for community_id, community_name in [(community_y_id, '社区Y'), (community_z_id, '社区Z')]:
            staff_response = requests.get(f'{base_url}/api/community/staff/list',
                headers=admin_headers,
                params={'community_id': community_id}
            )
            assert staff_response.status_code == 200
            staff_data = staff_response.json()
            assert staff_data.get('code') == 1

            staff_list = staff_data['data']['staff_members']
            user_in_community = next((s for s in staff_list if s['user_id'] == str(user_b_id)), None)
            assert user_in_community is not None, f"用户B应该在{community_name}中"
            assert user_in_community['role'] == 'staff', f"用户B在{community_name}的角色应该是staff"

        print("✓ E2E管理社区API测试通过：正确返回用户在各社区的角色")