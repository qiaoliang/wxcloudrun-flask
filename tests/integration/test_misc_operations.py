"""
杂项功能集成测试
Happy path: 成功操作计数器、获取环境配置
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestMiscOperations(IntegrationTestBase):
    """杂项功能集成测试"""

    def test_increment_counter_success(self):
        """测试成功增加计数器"""
        client = self.get_test_client()

        # 发送增加计数请求
        response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 1
            }),
            content_type='application/json'
        )

        # 验证响应
        data = self.assert_api_success(response, ['id', 'count'])
        assert data['data']['id'] == 1
        assert data['data']['count'] == 1

    def test_reset_counter_success(self):
        """测试成功重置计数器"""
        client = self.get_test_client()

        # 先增加计数
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 2
            }),
            content_type='application/json'
        )

        # 发送重置计数请求
        response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'reset',
                'counter_id': 2
            }),
            content_type='application/json'
        )

        # 验证响应
        data = self.assert_api_success(response, ['id', 'count'])
        assert data['data']['id'] == 2
        assert data['data']['count'] == 0

    def test_get_counter_success(self):
        """测试成功获取计数器"""
        client = self.get_test_client()

        # 先增加计数
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 3
            }),
            content_type='application/json'
        )

        # 发送获取计数请求
        response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'get',
                'id': 3
            }),
            content_type='application/json'
        )

        # 验证响应
        data = self.assert_api_success(response, ['id', 'count'])
        assert data['data']['id'] == 3
        assert data['data']['count'] == 1

    def test_list_counters_success(self):
        """测试成功列出所有计数器"""
        client = self.get_test_client()

        # 创建几个计数器
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 4
            }),
            content_type='application/json'
        )
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 5
            }),
            content_type='application/json'
        )

        # 发送列出计数器请求
        response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'list'
            }),
            content_type='application/json'
        )

        # 验证响应
        data = self.assert_api_success(response, ['counters'])
        assert len(data['data']['counters']) >= 2

    def test_clear_counters_success(self):
        """测试成功清除所有计数器"""
        client = self.get_test_client()

        # 创建一些计数器
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 6
            }),
            content_type='application/json'
        )
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 7
            }),
            content_type='application/json'
        )

        # 发送清除所有计数器请求
        response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'clear'
            }),
            content_type='application/json'
        )

        # 验证响应
        data = self.assert_api_success(response, ['message'])
        assert data['data']['message'] == '所有计数器已清除'

        # 验证计数器已被清除
        list_response = client.post(
            '/api/count',
            data=json.dumps({
                'action': 'list'
            }),
            content_type='application/json'
        )
        list_data = json.loads(list_response.data)
        assert len(list_data['data']['counters']) == 0

    def test_get_counter_via_get_success(self):
        """测试通过GET方法获取计数器"""
        client = self.get_test_client()

        # 先创建计数器
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 8
            }),
            content_type='application/json'
        )

        # 通过GET方法获取计数器
        response = client.get('/api/count?id=8')

        # 验证响应
        data = self.assert_api_success(response, ['id', 'count'])
        assert data['data']['id'] == 8
        assert data['data']['count'] == 1

    def test_get_all_counters_via_get_success(self):
        """测试通过GET方法获取所有计数器"""
        client = self.get_test_client()

        # 创建几个计数器
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 9
            }),
            content_type='application/json'
        )
        client.post(
            '/api/count',
            data=json.dumps({
                'action': 'increment',
                'counter_id': 10
            }),
            content_type='application/json'
        )

        # 通过GET方法获取所有计数器
        response = client.get('/api/count')

        # 验证响应
        data = self.assert_api_success(response, ['counters'])
        assert len(data['data']['counters']) >= 2

    def test_get_environments_success(self):
        """测试成功获取环境配置信息"""
        client = self.get_test_client()

        # 发送获取环境配置请求
        response = client.get('/api/get_envs')

        # 验证响应
        data = self.assert_api_success(response, ['config_status', 'external_status', 'timestamp'])
        assert 'config_status' in data['data']
        assert 'external_status' in data['data']
        assert 'timestamp' in data['data']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])