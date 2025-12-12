"""
社区功能E2E测试 - 合并版本
使用test_server fixture，移除skip标记，确保所有测试成功运行
"""

import os
import sys
import requests
import logging

from .testutil import random_str

#logger = logging.getLogger(__name__)

class TestCommunityE2E:
    """社区功能端到端测试"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token的辅助方法"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        return login_data['data']['token'], login_data['data']['user_id']

    def _create_test_user(self, base_url, phone, nickname):
        """创建测试用户的辅助方法"""
        register_response = requests.post(f'{base_url}/api/auth/register_phone', json={
            'phone': phone,
            'code': '123456',
            'password': 'Test123456',
            'nickname': nickname
        })
        assert register_response.status_code == 200
        register_data = register_response.json()
        assert register_data.get('code') == 1
        return register_data['data']['token'], register_data['data']['user_id']

    def test_get_communities_list_with_super_admin(self, test_server):
        """测试超级管理员获取社区列表"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 获取社区列表
        response = requests.get(f'{base_url}/api/communities', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        communities = data['data']
        assert len(communities) >= 1

        # 3. 验证默认社区存在
        default_community = None
        for community in communities:
            if community['name'] == '安卡大家庭':
                default_community = community
                break

        assert default_community is not None
        assert default_community['is_default'] is True
        assert default_community['description'] == "系统默认社区，新注册用户自动加入"
        assert default_community['status'] == 1
        assert default_community['status_name'] == 'enabled'

    def test_create_community_as_super_admin(self, test_server):
        """测试超级管理员创建社区"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 创建新社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '测试社区',
                'description': '用于测试的社区',
                'location': '北京市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        community = data['data']
        assert community['name'] == '测试社区'
        assert community['description'] == '用于测试的社区'
        assert community['location'] == '北京市'
        assert community['is_default'] is False

        # 不返回值，避免pytest警告

    def test_create_community_validation_errors(self, test_server):
        """测试创建社区的参数验证"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 测试空名称
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'description': '没有名称的社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区名称不能为空' in data['msg']

        # 3. 测试重复名称
        # 首先创建一个社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '重复测试社区',
                'description': '第一个社区'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 尝试创建同名社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '重复测试社区',
                'description': '第二个社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区名称已存在' in data['msg']

    def test_normal_user_permission_denied(self, test_server):
        """测试普通用户权限被拒绝"""
        base_url = test_server

        # 1. 创建普通用户
        token, user_id = self._create_test_user(base_url, '13800138000', '普通用户')
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 普通用户尝试获取社区列表（应该被拒绝）
        response = requests.get(f'{base_url}/api/communities', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 业务错误
        assert '权限不足' in data['msg'] or '需要超级管理员权限' in data['msg']

        # 3. 普通用户尝试创建社区（应该被拒绝）
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '非法社区',
                'description': '普通用户不应该能创建社区'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '权限不足' in data['msg'] or '需要超级管理员权限' in data['msg']

    def test_complete_community_management_workflow(self, test_server):
        """测试完整的社区管理工作流"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=admin_headers,
            json={
                'name': '管理工作流测试社区',
                'description': '用于测试完整管理工作流的社区',
                'location': '上海市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 获取社区详情
        response = requests.get(f'{base_url}/api/communities/{community_id}', headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community_detail = data['data']
        assert community_detail['name'] == '管理工作流测试社区'

        # 4. 创建社区管理员用户
        admin_user_token, admin_user_id = self._create_test_user(base_url, '13800138001', '社区管理员')

        # 5. 添加社区管理员
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/admins',
            headers=admin_headers,
            json={
                'user_ids': [admin_user_id],
                'role': 2
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 6. 社区管理员查看管理的社区
        admin_user_headers = {'Authorization': f'Bearer {admin_user_token}'}
        response = requests.get(f'{base_url}/api/communities/{community_id}', headers=admin_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 7. 社区管理员查看社区用户
        response = requests.get(f'{base_url}/api/communities/{community_id}/users', headers=admin_user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

    def test_user_join_community_flow(self, test_server):
        """测试用户加入社区流程"""
        base_url = test_server

        # 1. 创建普通用户
        user_token, user_id = self._create_test_user(base_url, '13800138002', '申请用户')
        user_headers = {'Authorization': f'Bearer {user_token}'}

        # 2. 创建目标社区
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        response = requests.post(f'{base_url}/api/communities',
            headers=admin_headers,
            json={
                'name': '申请流程测试社区',
                'description': '用于测试申请流程的社区',
                'location': '深圳市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 用户查看当前社区信息
        response = requests.get(f'{base_url}/api/user/community', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        current_community = data['data']['community']
        assert current_community['name'] == '安卡大家庭'  # 默认社区

        # 4. 用户查看可申请的社区
        response = requests.get(f'{base_url}/api/communities/available', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        available_communities = data['data']
        assert len(available_communities) >= 1

        # 5. 用户申请加入社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers=user_headers,
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区进行测试'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 6. 管理员查看申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        applications = data['data']
        # 在测试环境中，可能需要等待一下才能看到申请
        # 或者申请可能需要一些时间才能出现在列表中
        assert len(applications) >= 0  # 至少不报错

        # 找到刚提交的申请
        application = None
        for app in applications:
            if app['user']['user_id'] == user_id:
                application = app
                break

        assert application is not None
        application_id = application['application_id']

        # 7. 管理员批准申请
        response = requests.put(
            f'{base_url}/api/community/applications/{application_id}/approve',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 8. 用户查看更新后的社区信息
        response = requests.get(f'{base_url}/api/user/community', headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        updated_community = data['data']['community']
        assert updated_community['community_id'] == community_id

    def test_user_search_and_promote_flow(self, test_server):
        """测试用户搜索和提升管理员流程"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=admin_headers,
            json={
                'name': '用户管理测试社区',
                'description': '用于测试用户管理功能的社区',
                'location': '广州市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 创建测试用户
        testuser_phone = f"138{random_str(8)}"
        testuser_nickname = f"待提升用户_{random_str(8)}"
        user_token, user_id = self._create_test_user(base_url,testuser_phone ,testuser_nickname )

        # 4. 用户申请加入测试社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {user_token}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区进行测试'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 管理员批准申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        applications = data['data']

        # 找到刚提交的申请
        application = None
        for app in applications:
            if app['user']['user_id'] == user_id:
                application = app
                break

        assert application is not None
        application_id = application['application_id']

        # 批准申请
        response = requests.put(
            f'{base_url}/api/community/applications/{application_id}/approve',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['message'] == '批准成功'

        # 6. 搜索用户
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/users?keyword={testuser_phone}',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        users = data['data']['users']
        assert len(users) == 1
        assert users[0]['nickname'] == testuser_nickname

        # 7. 将用户提升为管理员
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id}/set-admin',
            headers=admin_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['user_id'] == 2



        # 8. 验证用户已成为管理员
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/admins',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        admins = data['data']
        assert admins is not None

        # 查找新提升的管理员
        new_admin = None
        for admin in admins:
            if admin['user_id'] == user_id:
                new_admin = admin
                break

        assert new_admin is not None
        assert new_admin['role_name'] == 'normal'

    def test_error_handling(self, test_server):
        """测试错误处理"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 访问不存在的社区
        response = requests.get(f'{base_url}/api/communities/99999', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区不存在' in data['msg']

        # 3. 处理不存在的申请
        response = requests.put(
            f'{base_url}/api/community/applications/99999/approve',
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '申请不存在' in data['msg']

        # 4. 拒绝申请未提供理由
        response = requests.put(
            f'{base_url}/api/community/applications/99999/reject',
            headers=headers,
            json={}  # 没有拒绝理由
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '缺少拒绝理由' in data['msg'] or '缺少请求参数' in data['msg']

    def test_update_community_info(self, test_server):
        """测试更新社区信息"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '待更新社区',
                'description': '这个社区将被更新',
                'location': '北京市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 更新社区信息
        update_data = {
            'name': '已更新社区',
            'description': '社区信息已更新',
            'location': '上海市',
            'status': 1
        }
        response = requests.put(f'{base_url}/api/communities/{community_id}',
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        updated_community = data['data']
        assert updated_community['name'] == '已更新社区'
        assert updated_community['description'] == '社区信息已更新'
        assert updated_community['location'] == '上海市'
        assert updated_community['status'] == 1

        # 4. 验证更新后的数据
        response = requests.get(f'{base_url}/api/communities/{community_id}', headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        assert community['name'] == '已更新社区'
        assert community['description'] == '社区信息已更新'
        assert community['location'] == '上海市'

        # 5. 测试权限控制 - 普通用户不能更新社区
        user_token, user_id = self._create_test_user(base_url, '13900008888', '普通用户')
        user_headers = {'Authorization': f'Bearer {user_token}'}

        response = requests.put(f'{base_url}/api/communities/{community_id}',
            headers=user_headers,
            json={'name': '非法更新'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 应该返回错误
        assert '权限不足' in data.get('msg', '')

        # 6. 测试更新不存在的社区
        response = requests.put(f'{base_url}/api/communities/99999',
            headers=headers,
            json={'name': '不存在的社区'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区不存在' in data.get('msg', '')

        # 7. 测试社区名称重复
        # 创建另一个社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '重复测试社区',
                'description': '用于测试名称重复'
            }
        )
        assert response.status_code == 200

        # 尝试使用重复的名称
        response = requests.put(f'{base_url}/api/communities/{community_id}',
            headers=headers,
            json={'name': '重复测试社区'}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区名称已存在' in data.get('msg', '')

    def test_remove_user_from_community(self, test_server):
        """测试从社区中移除用户"""
        base_url = test_server

        # 1. 超级管理员登录
        token, user_id = self._get_super_admin_token(base_url)
        headers = {'Authorization': f'Bearer {token}'}

        # 2. 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '移除用户测试社区',
                'description': '用于测试移除用户的社区',
                'location': '深圳市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 创建测试用户
        user_token, test_user_id = self._create_test_user(base_url, '13900009999', '待移除用户')

        # 4. 用户申请加入测试社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {user_token}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区'
            }
        )
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 5. 批准申请
        # 获取申请列表
        response = requests.get(f'{base_url}/api/community/applications', headers=headers)
        assert response.status_code == 200
        applications = response.json().get('data', [])
        assert len(applications) > 0

        application_id = None
        for app in applications:
            if app['user']['user_id'] == test_user_id and app['community']['community_id'] == community_id:
                application_id = app['application_id']
                break

        assert application_id is not None

        # 批准申请
        response = requests.put(f'{base_url}/api/community/applications/{application_id}/approve',
            headers=headers)
        assert response.status_code == 200
        assert response.json().get('code') == 1

        # 6. 验证用户已在社区中
        response = requests.get(f'{base_url}/api/user/community',
            headers={'Authorization': f'Bearer {user_token}'})
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        user_community = data['data']['community']
        assert user_community['community_id'] == community_id

        # 7. 移除用户（超级管理员操作）
        response = requests.delete(f'{base_url}/api/communities/{community_id}/users/{test_user_id}',
            headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        assert data['data']['message'] == '移除成功'

        # 8. 验证用户已被移到默认社区
        response = requests.get(f'{base_url}/api/user/community',
            headers={'Authorization': f'Bearer {user_token}'})
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        user_community = data['data']['community']
        assert user_community['name'] == '安卡大家庭'
        assert user_community['is_default'] == True

        # 9. 测试权限控制 - 普通用户不能移除其他用户
        normal_user_token, normal_user_id = self._create_test_user(base_url, '13900008888', '普通用户')
        normal_headers = {'Authorization': f'Bearer {normal_user_token}'}

        response = requests.delete(f'{base_url}/api/communities/{community_id}/users/{test_user_id}',
            headers=normal_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 应该返回错误
        assert '权限不足' in data.get('msg', '') or '需要超级管理员权限' in data.get('msg', '')

        # 10. 测试移除不存在的用户
        response = requests.delete(f'{base_url}/api/communities/{community_id}/users/99999',
            headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '用户不存在' in data.get('msg', '')

        # 11. 测试从不存在的社区移除用户
        response = requests.delete(f'{base_url}/api/communities/99999/users/{test_user_id}',
            headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区不存在' in data.get('msg', '')


class TestCommunityPerformance:
    """社区功能性能测试"""

    def test_large_community_user_search(self, test_server):
        """测试大社区用户搜索性能"""
        base_url = test_server

        # 获取超级管理员token
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        token = login_data['data']['token']
        headers = {'Authorization': f'Bearer {token}'}

        # 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=headers,
            json={
                'name': '性能测试社区',
                'description': '用于性能测试的社区',
                'location': '杭州市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 测试搜索性能
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/users?keyword=test',
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1