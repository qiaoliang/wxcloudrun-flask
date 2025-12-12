"""
测试设置用户为社区管理员的API
"""

import pytest
import requests
import logging
import uuid
import time

def random_str(length: int) -> str:
    """生成随机字符串"""
    # 最多 16 位数字
    length = length if length < 16 else 16
    timestamp = str(int(time.time() * 1000000))
    result = f"{timestamp}"
    return result[:length]

class TestSetAdminAPI:
    """测试设置用户为社区管理员API"""

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

    def test_set_admin_api(self, test_server):
        """测试设置用户为社区管理员API"""
        base_url = test_server

        # 1. 超级管理员登录
        admin_token, admin_id = self._get_super_admin_token(base_url)
        admin_headers = {'Authorization': f'Bearer {admin_token}'}

        # 2. 创建测试社区
        response = requests.post(f'{base_url}/api/communities',
            headers=admin_headers,
            json={
                'name': '管理员设置测试社区',
                'description': '用于测试管理员设置功能的社区',
                'location': '南京市'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        community = data['data']
        community_id = community['community_id']

        # 3. 创建测试用户
        test_user_phone = f"139{random_str(8)}"
        test_user_nickname = f"测试管理员_{random_str(8)}"
        user_token, user_id = self._create_test_user(base_url, test_user_phone, test_user_nickname)

        # 4. 用户申请加入测试社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {user_token}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区并成为管理员'
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 5. 批准用户申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        applications = data['data']

        # 找到刚提交的申请
        application = None
        for app in applications:
            if app['user']['user_id'] == user_id and app['community']['community_id'] == community_id:
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

        # 6. 测试设置用户为普通管理员 (role=2)
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id}/set-admin',
            headers=admin_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 7. 验证用户已成为管理员
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/admins',
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1
        admins = data['data']

        # 查找新设置的管理员
        new_admin = None
        for admin in admins:
            if admin['user_id'] == user_id:
                new_admin = admin
                break

        assert new_admin is not None
        assert new_admin['role_name'] == 'normal'  # role=2对应normal角色

        # 8. 测试重复设置管理员（应该失败）
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id}/set-admin',
            headers=admin_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 应该返回错误
        assert '用户已经是该社区的管理员' in data['msg']

        # 9. 测试设置用户为主管理员 (role=1)
        another_user_phone = f"138{random_str(8)}"
        another_user_nickname = f"主管理员_{random_str(8)}"
        another_user_token, another_user_id = self._create_test_user(base_url, another_user_phone, another_user_nickname)

        # 另一个用户申请加入社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {another_user_token}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区'
            }
        )
        assert response.status_code == 200

        # 批准申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        applications = response.json()['data']
        for app in applications:
            if app['user']['user_id'] == another_user_id:
                response = requests.put(
                    f'{base_url}/api/community/applications/{app["application_id"]}/approve',
                    headers=admin_headers
                )
                assert response.status_code == 200
                break

        # 设置为主管理员
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{another_user_id}/set-admin',
            headers=admin_headers,
            json={'role': 1}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 验证主管理员角色
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/admins',
            headers=admin_headers
        )
        admins = response.json()['data']
        main_admin = None
        for admin in admins:
            if admin['user_id'] == another_user_id:
                main_admin = admin
                break
        assert main_admin is not None
        assert main_admin['role_name'] == 'main'  # role=1对应main角色

        # 10. 测试权限控制 - 普通用户不能设置管理员
        normal_user_token, normal_user_id = self._create_test_user(base_url, '13700007777', '普通用户')
        normal_headers = {'Authorization': f'Bearer {normal_user_token}'}

        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id}/set-admin',
            headers=normal_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0  # 应该返回错误
        assert '权限不足' in data['msg']

        # 11. 测试设置不存在的用户为管理员
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/99999/set-admin',
            headers=admin_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '用户不存在' in data['msg']

        # 12. 测试在不存在的社区中设置管理员
        response = requests.post(
            f'{base_url}/api/communities/99999/users/{user_id}/set-admin',
            headers=admin_headers,
            json={'role': 2}
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 0
        assert '社区不存在' in data['msg']

        # 13. 测试无效的role参数
        test_user_phone2 = f"136{random_str(8)}"
        test_user_nickname2 = f"无效角色用户_{random_str(8)}"
        user_token2, user_id2 = self._create_test_user(base_url, test_user_phone2, test_user_nickname2)

        # 用户申请加入社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {user_token2}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区'
            }
        )
        assert response.status_code == 200

        # 批准申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        applications = response.json()['data']
        for app in applications:
            if app['user']['user_id'] == user_id2:
                response = requests.put(
                    f'{base_url}/api/community/applications/{app["application_id"]}/approve',
                    headers=admin_headers
                )
                assert response.status_code == 200
                break

        # 使用无效的role参数
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id2}/set-admin',
            headers=admin_headers,
            json={'role': 99}  # 无效的角色值
        )
        assert response.status_code == 200
        data = response.json()
        # 根据实现，无效role应该默认为staff(2)，所以应该成功
        assert data.get('code') == 1

        # 14. 测试不提供role参数（应该使用默认值2）
        test_user_phone3 = f"135{random_str(8)}"
        test_user_nickname3 = f"默认角色用户_{random_str(8)}"
        user_token3, user_id3 = self._create_test_user(base_url, test_user_phone3, test_user_nickname3)

        # 用户申请加入社区
        response = requests.post(f'{base_url}/api/community/applications',
            headers={'Authorization': f'Bearer {user_token3}'},
            json={
                'community_id': community_id,
                'reason': '我想加入这个社区'
            }
        )
        assert response.status_code == 200

        # 批准申请
        response = requests.get(f'{base_url}/api/community/applications', headers=admin_headers)
        applications = response.json()['data']
        for app in applications:
            if app['user']['user_id'] == user_id3:
                response = requests.put(
                    f'{base_url}/api/community/applications/{app["application_id"]}/approve',
                    headers=admin_headers
                )
                assert response.status_code == 200
                break

        # 不提供role参数
        response = requests.post(
            f'{base_url}/api/communities/{community_id}/users/{user_id3}/set-admin',
            headers=admin_headers,
            json={}  # 空的JSON，不提供role
        )
        assert response.status_code == 200
        data = response.json()
        assert data.get('code') == 1

        # 验证默认设置为普通管理员
        response = requests.get(
            f'{base_url}/api/communities/{community_id}/admins',
            headers=admin_headers
        )
        admins = response.json()['data']
        default_admin = None
        for admin in admins:
            if admin['user_id'] == user_id3:
                default_admin = admin
                break
        assert default_admin is not None
        assert default_admin['role_name'] == 'normal'  # 默认为normal角色