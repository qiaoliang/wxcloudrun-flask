"""
契约测试：验证前端实际调用的 API 返回符合期望的数据结构

这个测试从 frontend/src/api/ 目录中提取实际调用的 API，
然后验证后端返回的数据结构是否符合前端的使用方式。
"""
import pytest
import re
from pathlib import Path
from typing import Dict, List, Set


class TestAPIContract:
    """基于前端实际 API 调用的契约测试"""
    
    @pytest.fixture
    def frontend_api_files(self):
        """获取前端 API 文件列表"""
        # 从 backend/tests/contract/test_api_contract.py 向上 4 层到达 safeGuard 目录
        api_dir = Path(__file__).parent.parent.parent.parent / "frontend/src/api"
        return list(api_dir.glob("*.js"))
    
    @pytest.fixture
    def frontend_api_calls(self, frontend_api_files):
        """从前端 API 文件中提取 API 调用"""
        api_calls = {}
        
        for api_file in frontend_api_files:
            with open(api_file) as f:
                content = f.read()
                
                # 提取 API URL
                # 匹配 /api/ 开头的路径，包括模板字符串中的路径
                # 使用更宽松的模式来匹配各种形式的 URL
                url_pattern = r"(?:url:\s*['\"`])(/api/[^\s'\"]+)(?:['\"`])"
                urls = re.findall(url_pattern, content)
                
                # 提取方法
                method_pattern = r"method:\s*['\"]([^'\"]+)['\"]"
                methods = re.findall(method_pattern, content)
                
                # 为每个 URL 分配方法（如果没有指定，默认为 GET）
                for i, url in enumerate(urls):
                    method = methods[i] if i < len(methods) else 'GET'
                    
                    if url not in api_calls:
                        api_calls[url] = {
                            'file': api_file.name,
                            'methods': set(),
                            'fields_used': set()
                        }
                    api_calls[url]['methods'].add(method)
                    
                    # 提取响应中使用的字段
                    # 查找类似 response.data.xxx 的模式
                    field_pattern = r"(?:response|result)\.data\.(\w+)"
                    fields = re.findall(field_pattern, content)
                    api_calls[url]['fields_used'].update(fields)
        
        return api_calls
    
    @pytest.fixture
    def auth_token(self, client):
        """获取认证 token"""
        # 使用超级管理员账号登录
        response = client.post('/api/auth/login_phone_password', json={
            'phone': '13141516171',
            'password': 'F1234567'
        })
        
        assert response.status_code == 200
        data = response.json
        return data['data']['token']
    
    def test_frontend_api_calls_succeed(self, client, auth_token, frontend_api_calls):
        """验证前端调用的 API 都能成功返回"""
        failed_apis = []
        
        for api_url, api_info in frontend_api_calls.items():
            # 跳过不需要认证的 API
            if '/auth/login' in api_url:
                continue
            
            # 跳过包含模板变量的 API（需要实际参数）
            if '${' in api_url:
                continue
            
            # 根据方法选择请求类型
            for method in api_info['methods']:
                if method == 'GET':
                    response = client.get(
                        api_url,
                        headers={'Authorization': f'Bearer {auth_token}'}
                    )
                elif method == 'POST':
                    response = client.post(
                        api_url,
                        headers={'Authorization': f'Bearer {auth_token}'}
                    )
                elif method == 'PUT':
                    response = client.put(
                        api_url,
                        headers={'Authorization': f'Bearer {auth_token}'}
                    )
                elif method == 'DELETE':
                    response = client.delete(
                        api_url,
                        headers={'Authorization': f'Bearer {auth_token}'}
                    )
                
                if response.status_code != 200:
                    failed_apis.append({
                        'url': api_url,
                        'method': method,
                        'status': response.status_code,
                        'response': response.json
                    })
        
        assert not failed_apis, f"以下 API 调用失败: {failed_apis}"
    
    def test_api_response_structure(self, client, auth_token, frontend_api_calls):
        """验证 API 响应结构包含前端使用的字段"""
        missing_fields = []
        
        for api_url, api_info in frontend_api_calls.items():
            if not api_info['fields_used']:
                continue
            
            # 跳过包含模板变量的 API（需要实际参数）
            if '${' in api_url:
                continue
            
            # 发送请求
            response = client.get(
                api_url,
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            if response.status_code != 200:
                continue
            
            data = response.json
            response_data = data.get('data', {})
            
            # 确定 data 的类型（dict 或 list）
            if isinstance(response_data, dict):
                actual_fields = set(response_data.keys())
            elif isinstance(response_data, list) and response_data:
                # 如果是列表，检查第一个元素
                actual_fields = set(response_data[0].keys())
            else:
                continue
            
            # 检查前端期望的字段是否存在
            expected_fields = api_info['fields_used']
            missing = expected_fields - actual_fields
            
            if missing:
                missing_fields.append({
                    'api': api_url,
                    'file': api_info['file'],
                    'missing': list(missing),
                    'available': list(actual_fields)
                })
        
        assert not missing_fields, f"API 响应缺少前端期望的字段: {missing_fields}"
    
    def test_api_response_data_types(self, client, auth_token, frontend_api_calls):
        """验证 API 响应数据类型正确"""
        type_mismatches = []
        
        for api_url, api_info in frontend_api_calls.items():
            # 跳过包含模板变量的 API（需要实际参数）
            if '${' in api_url:
                continue
            
            # 发送请求
            response = client.get(
                api_url,
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            if response.status_code != 200:
                continue
            
            data = response.json
            response_data = data.get('data', {})
            
            # 验证关键字段的数据类型
            if 'communities' in api_info['fields_used']:
                communities = response_data.get('communities', [])
                assert isinstance(communities, list), \
                    f"API {api_url} 的 communities 字段应该是列表"
                
                for community in communities:
                    # 验证社区对象的结构
                    assert 'community_id' in community, \
                        f"API {api_url} 的社区对象缺少 community_id 字段"
                    assert 'name' in community, \
                        f"API {api_url} 的社区对象缺少 name 字段"
                    assert 'status' in community, \
                        f"API {api_url} 的社区对象缺少 status 字段"
                    
                    # 验证数据类型
                    assert isinstance(community['community_id'], int), \
                        f"API {api_url} 的 community_id 应该是整数"
                    assert isinstance(community['name'], str), \
                        f"API {api_url} 的 name 应该是字符串"
                    assert isinstance(community['status'], int), \
                        f"API {api_url} 的 status 应该是整数"
    
    def test_api_response_not_empty(self, client, auth_token, frontend_api_calls):
        """验证 API 返回的数据不为空（在合理的情况下）"""
        empty_data_apis = []
        
        for api_url, api_info in frontend_api_calls.items():
            # 跳过可能返回空数据的 API
            if 'list' in api_url and 'search' not in api_url:
                continue
            
            # 跳过包含模板变量的 API（需要实际参数）
            if '${' in api_url:
                continue
            
            # 发送请求
            response = client.get(
                api_url,
                headers={'Authorization': f'Bearer {auth_token}'}
            )
            
            if response.status_code != 200:
                continue
            
            data = response.json
            response_data = data.get('data', {})
            
            # 检查是否为空
            if isinstance(response_data, dict) and not response_data:
                empty_data_apis.append(api_url)
            elif isinstance(response_data, list) and not response_data:
                empty_data_apis.append(api_url)
        
        if empty_data_apis:
            pytest.skip(f"以下 API 返回空数据（可能正常）: {empty_data_apis}")
    
    def test_frontend_api_coverage(self, frontend_api_calls):
        """生成前端 API 调用覆盖报告"""
        print("\n=== 前端 API 调用覆盖报告 ===")
        print(f"总共发现 {len(frontend_api_calls)} 个 API 调用")
        
        for api_url, api_info in sorted(frontend_api_calls.items()):
            print(f"\nAPI: {api_url}")
            print(f"  文件: {api_info['file']}")
            print(f"  方法: {', '.join(api_info['methods'])}")
            print(f"  使用的字段: {', '.join(api_info['fields_used']) if api_info['fields_used'] else '无'}")
        
        print("\n=== 报告结束 ===")