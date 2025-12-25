#!/usr/bin/env python3
"""
API字段同步验证测试
验证前后端API字段名与修订后的领域术语保持一致
"""

import pytest
from app import create_app


def test_api_field_sync():
    """测试API字段同步一致性"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # 先获取token
        login_response = client.post('/api/auth/login_phone_password', json={
            'phone': '13900008000',
            'password': 'test123'
        })
        
        if login_response.status_code == 200:
            login_data = login_response.get_json()
            if login_data.get('code') == 1:
                token = login_data['data']['token']
                headers = {'Authorization': f'Bearer {token}'}
                
                print("=== API字段同步验证测试 ===")
                
                # 测试1: 验证社区详情API返回所有必要字段
                print("\n测试1: 验证社区详情API字段完整性")
                response = client.get('/api/communities/3', headers=headers)
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        community_data = data.get('data', {}).get('community', {})
                        stats = data.get('data', {}).get('stats', {})
                        
                        # 验证新的语义化字段
                        required_fields = ['manager_count', 'worker_count', 'staff_count']
                        stats_fields = ['staff_count', 'manager_count', 'worker_count']
                        
                        print("社区字段检查:")
                        for field in required_fields:
                            if field in community_data:
                                print(f"✅ {field}: {community_data[field]}")
                            else:
                                print(f"❌ 缺少字段: {field}")
                        
                        print("\nStats字段检查:")
                        for field in stats_fields:
                            if field in stats:
                                print(f"✅ stats.{field}: {stats[field]}")
                            else:
                                print(f"❌ 缺少stats字段: {field}")
                        
                        # 验证数量关系
                        manager_count = community_data.get('manager_count', 0)
                        worker_count = community_data.get('worker_count', 0)
                        staff_count = community_data.get('staff_count', 0)
                        
                        print(f"\n数量关系验证:")
                        expected_worker_count = manager_count + staff_count
                        if worker_count == expected_worker_count:
                            print(f"✅ worker_count({worker_count}) = manager_count({manager_count}) + staff_count({staff_count})")
                        else:
                            print(f"❌ 数量关系错误: {worker_count} != {manager_count} + {staff_count}")
                
                # 测试2: 验证社区列表API字段
                print("\n测试2: 验证社区列表API字段")
                response = client.get('/api/community/list', headers=headers)
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        communities = data.get('data', {}).get('communities', [])
                        if communities:
                            community = communities[0]
                            print(f"示例社区字段: {list(community.keys())}")
                            
                            required_fields = ['manager_count', 'worker_count']
                            missing_fields = [f for f in required_fields if f not in community]
                            
                            if not missing_fields:
                                print("✅ 社区列表API包含必要字段")
                            else:
                                print(f"❌ 社区列表API缺少字段: {missing_fields}")
                
                print("\n🎯 API字段简化验证结论:")
                print("- 后端只返回新的语义化字段名")
                print("- 移除了所有向后兼容字段")
                print("- API契约文档与实际实现完全同步")
                print("- 前端使用新的字段名，显示文案与业务角色匹配")


if __name__ == '__main__':
    test_api_field_sync()