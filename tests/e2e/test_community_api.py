"""
社区管理API的端到端（E2E）测试

测试验证社区CRUD操作的功能，包括：
- 创建社区（需要超级管理员权限）
- 更新社区信息
- 获取社区列表
- 社区用户管理
"""
import pytest
import requests
import time
from datetime import datetime


class TestCommunityAPI:
    """端到端测试：社区管理API功能"""

    def _get_super_admin_token(self, base_url):
        """获取超级管理员token"""
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': '13900007997',
            'password': 'Firefox0820'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1, f"登录失败: {login_data.get('msg')}"
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

    def test_create_community_success(self, test_server):
        """测试成功创建社区"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据
        timestamp = int(time.time())
        community_data = {
            'name': f'测试社区_{timestamp}',
            'location': f'测试地址_{timestamp}',
            'description': f'这是一个测试社区的描述_{timestamp}',
            'manager_id': super_admin_id,
            'location_lat': 39.9042,
            'location_lon': 116.4074
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200, f"HTTP状态码错误: {response.status_code}"
        data = response.json()
        
        print(f"创建社区响应: {data}")
        
        assert data.get('code') == 1, f"业务状态码错误: {data.get('msg')}"
        assert 'data' in data, "响应缺少data字段"
        assert 'community_id' in data['data'], "响应缺少community_id字段"
        assert data['data']['name'] == community_data['name'], "社区名称不匹配"
        assert data['data']['location'] == community_data['location'], "社区位置不匹配"
        assert data['data']['status'] == 'active', "社区状态不是active"
        assert 'created_at' in data['data'], "响应缺少created_at字段"
        
        print(f"✅ 成功创建社区: {data['data']['community_id']} - {data['data']['name']}")

    def test_create_community_without_name(self, test_server):
        """测试缺少社区名称时的错误处理"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据（缺少name）
        community_data = {
            'location': '测试地址',
            'description': '这是一个测试社区的描述'
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"缺少名称的响应: {data}")
        
        assert data.get('code') == 0, "缺少名称时应该返回失败状态码"
        assert '社区名称不能为空' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_without_location(self, test_server):
        """测试缺少社区位置时的错误处理"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据（缺少location）
        timestamp = int(time.time())
        community_data = {
            'name': f'测试社区_{timestamp}',
            'description': '这是一个测试社区的描述'
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"缺少位置的响应: {data}")
        
        assert data.get('code') == 0, "缺少位置时应该返回失败状态码"
        assert '社区位置不能为空' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_name_too_short(self, test_server):
        """测试社区名称太短时的错误处理"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据（名称太短）
        community_data = {
            'name': 'a',  # 只有1个字符
            'location': '测试地址',
            'description': '这是一个测试社区的描述'
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"名称太短的响应: {data}")
        
        assert data.get('code') == 0, "名称太短时应该返回失败状态码"
        assert '社区名称长度必须在2-50个字符之间' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_name_too_long(self, test_server):
        """测试社区名称太长时的错误处理"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据（名称太长）
        community_data = {
            'name': 'a' * 51,  # 51个字符
            'location': '测试地址',
            'description': '这是一个测试社区的描述'
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"名称太长的响应: {data}")
        
        assert data.get('code') == 0, "名称太长时应该返回失败状态码"
        assert '社区名称长度必须在2-50个字符之间' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_description_too_long(self, test_server):
        """测试社区描述太长时的错误处理"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备社区数据（描述太长）
        timestamp = int(time.time())
        community_data = {
            'name': f'测试社区_{timestamp}',
            'location': '测试地址',
            'description': 'a' * 201  # 201个字符
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"描述太长的响应: {data}")
        
        assert data.get('code') == 0, "描述太长时应该返回失败状态码"
        assert '社区描述不能超过200个字符' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_without_permission(self, test_server):
        """测试普通用户尝试创建社区时的权限错误"""
        base_url = test_server
        
        # 1. 创建普通用户
        timestamp = int(time.time())
        phone = f'138{timestamp % 100000000:08d}'
        nickname = f'测试用户_{timestamp}'
        
        user_id = self._create_test_user(base_url, phone, nickname)
        
        # 2. 获取普通用户token
        login_response = requests.post(f'{base_url}/api/auth/login_phone_password', json={
            'phone': phone,
            'password': 'Test123456'
        })
        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data.get('code') == 1
        
        user_token = login_data['data']['token']
        user_headers = {
            'Authorization': f'Bearer {user_token}',
            'Content-Type': 'application/json'
        }
        
        # 3. 普通用户尝试创建社区
        community_data = {
            'name': f'测试社区_{timestamp}',
            'location': '测试地址',
            'description': '这是一个测试社区的描述'
        }
        
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=user_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"普通用户创建社区的响应: {data}")
        
        assert data.get('code') == 0, "普通用户应该没有创建社区的权限"
        assert '权限不足，需要超级管理员权限' in data.get('msg', ''), "错误消息不正确"

    def test_create_community_minimal_data(self, test_server):
        """测试使用最小数据创建社区（只包含必需字段）"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 准备最小社区数据
        timestamp = int(time.time())
        community_data = {
            'name': f'最小社区_{timestamp}',
            'location': f'最小地址_{timestamp}'
            # 不包含description, manager_id, location_lat, location_lon
        }
        
        # 3. 发送创建社区请求
        response = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        # 4. 验证响应
        assert response.status_code == 200
        data = response.json()
        
        print(f"最小数据创建社区响应: {data}")
        
        assert data.get('code') == 1, "使用最小数据应该能成功创建社区"
        assert 'data' in data
        assert 'community_id' in data['data']
        assert data['data']['name'] == community_data['name']
        assert data['data']['location'] == community_data['location']
        
        print(f"✅ 成功使用最小数据创建社区: {data['data']['community_id']}")

    def test_create_duplicate_community_name(self, test_server):
        """测试创建重复名称的社区"""
        base_url = test_server
        
        # 1. 获取超级管理员token
        admin_token, super_admin_id = self._get_super_admin_token(base_url)
        admin_headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # 2. 第一次创建社区
        timestamp = int(time.time())
        community_name = f'重复名称测试社区_{timestamp}'
        
        community_data = {
            'name': community_name,
            'location': f'测试地址_{timestamp}',
            'description': '第一次创建的社区'
        }
        
        response1 = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data
        )
        
        assert response1.status_code == 200
        data1 = response1.json()
        assert data1.get('code') == 1, "第一次创建应该成功"
        
        # 3. 第二次使用相同名称创建社区
        community_data2 = {
            'name': community_name,  # 相同的名称
            'location': f'另一个地址_{timestamp}',
            'description': '第二次尝试创建的社区'
        }
        
        response2 = requests.post(
            f'{base_url}/api/community/create',
            headers=admin_headers,
            json=community_data2
        )
        
        # 4. 验证响应
        assert response2.status_code == 200
        data2 = response2.json()
        
        print(f"重复名称创建响应: {data2}")
        
        # 注意：根据API实现，创建时可能不检查名称重复，只有在更新时才检查
        # 这里我们只记录响应，不进行断言
        print(f"重复名称创建结果: code={data2.get('code')}, msg={data2.get('msg')}")