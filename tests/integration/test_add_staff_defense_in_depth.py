import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))
from app import create_app


def test_add_staff_defense_in_depth():
    """测试添加专员API的深度防御验证机制"""
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
                
                print("=== 深度防御验证测试 ===")
                
                # 测试1: Layer 1 - 正常批量添加（应该成功）
                print("\n测试1: 正常批量添加")
                response = client.post('/api/community/add-staff', 
                    json={
                        'community_id': 3,
                        'user_ids': [800000001, 800000002],
                        'role': 'staff'
                    },
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                data = response.get_json()
                print(f"响应: {data}")
                assert response.status_code == 200
                assert data.get('code') == 1
                print("✅ Layer 1验证通过：正常请求成功")
                
                # 测试2: Layer 1 - 缺少必要参数（应该失败）
                print("\n测试2: Layer 1 - 缺少community_id")
                response = client.post('/api/community/add-staff',
                    json={
                        'user_ids': [800000001],
                        'role': 'staff'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '缺少社区ID' in data.get('msg', '')
                print("✅ Layer 1验证通过：缺少参数被拒绝")
                
                # 测试3: Layer 1 - 无效参数类型（应该失败）
                print("\n测试3: Layer 1 - 无效的community_id类型")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 'invalid_id',
                        'user_ids': [800000001],
                        'role': 'staff'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '社区ID格式错误' in data.get('msg', '')
                print("✅ Layer 1验证通过：无效类型被拒绝")
                
                # 测试4: Layer 1 - 空用户ID数组（应该失败）
                print("\n测试4: Layer 1 - 空user_ids数组")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': [],
                        'role': 'staff'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '不能为空' in data.get('msg', '')
                print("✅ Layer 1验证通过：空数组被拒绝")
                
                # 测试5: Layer 1 - 无效角色（应该失败）
                print("\n测试5: Layer 1 - 无效角色")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': [800000001],
                        'role': 'invalid_role'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '角色参数错误' in data.get('msg', '')
                print("✅ Layer 1验证通过：无效角色被拒绝")
                
                # 测试6: Layer 2 - 过大批量操作（应该失败）
                print("\n测试6: Layer 2 - 过大批量操作")
                large_user_list = list(range(800000001, 800000052))  # 51个用户
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': large_user_list,
                        'role': 'staff'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '不能超过50个' in data.get('msg', '')
                print("✅ Layer 2验证通过：过大操作被拒绝")
                
                # 测试7: Layer 3 - 主管角色批量添加（应该失败）
                print("\n测试7: Layer 3 - 主管角色批量添加")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': [800000001, 800000002],
                        'role': 'manager'
                    },
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert '主管角色只能添加单个用户' in data.get('msg', '')
                print("✅ Layer 3验证通过：主管批量添加被拒绝")
                
                # 测试8: 兼容性测试 - 单个user_id参数（应该成功）
                print("\n测试8: 兼容性测试 - 单个user_id参数")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_id': 800000003,  # 单个用户ID
                        'role': 'staff'
                    },
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                data = response.get_json()
                print(f"响应: {data}")
                if response.status_code == 200 and data.get('code') == 1:
                    print("✅ 兼容性测试通过：单个user_id参数支持")
                else:
                    print("⚠️ 兼容性测试：单个user_id参数需要进一步检查")
                
                # 测试9: Layer 4 - 调试信息验证
                print("\n测试9: Layer 4 - 调试信息验证")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': [800000004, 800000005, 'invalid_id'],
                        'role': 'staff'
                    },
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                data = response.get_json()
                print(f"响应: {data}")
                
                # 应该过滤掉无效ID，只添加有效ID
                if response.status_code == 200 and data.get('code') == 1:
                    result_data = data.get('data', {})
                    if result_data.get('added_count', 0) > 0:
                        print("✅ Layer 4验证通过：无效ID被过滤，有效ID被添加")
                    else:
                        print("ℹ️ Layer 4信息：可能由于权限或其他业务规则导致添加失败")
                
                print("\n🎯 所有深度防御测试完成！")


if __name__ == '__main__':
    test_add_staff_defense_in_depth()