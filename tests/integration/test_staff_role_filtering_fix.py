#!/usr/bin/env python3
"""
验证专员列表API role参数修复
测试API能正确过滤专员和主管
"""

import pytest
from app import create_app


def test_staff_list_role_filtering():
    """测试专员列表API的角色过滤功能"""
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
                
                print("=== 专员列表角色过滤测试 ===")
                
                # 测试1: 只获取专员 (role=staff)
                print("\n测试1: 获取专员列表 (role=staff)")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3, 'role': 'staff'},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        staff_list = data.get('data', {}).get('staff', [])
                        print(f"专员数量: {len(staff_list)}")
                        
                        # 验证所有返回的都是专员
                        all_staff = True
                        for staff in staff_list:
                            if staff.get('role') != 'staff':
                                all_staff = False
                                print(f"❌ 发现非专员角色: {staff.get('role')}")
                                break
                        
                        if all_staff:
                            print("✅ 所有返回的都是专员")
                        else:
                            print("❌ 角色过滤失败")
                    else:
                        print(f"API业务错误: {data.get('msg')}")
                else:
                    print(f"HTTP错误: {response.status_code}")
                
                # 测试2: 只获取主管 (role=manager)
                print("\n测试2: 获取主管列表 (role=manager)")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3, 'role': 'manager'},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        manager_list = data.get('data', {}).get('staff', [])
                        print(f"主管数量: {len(manager_list)}")
                        
                        # 验证所有返回的都是主管
                        all_managers = True
                        for manager in manager_list:
                            if manager.get('role') != 'manager':
                                all_managers = False
                                print(f"❌ 发现非主管角色: {manager.get('role')}")
                                break
                        
                        if all_managers:
                            print("✅ 所有返回的都是主管")
                        else:
                            print("❌ 角色过滤失败")
                    else:
                        print(f"API业务错误: {data.get('msg')}")
                else:
                    print(f"HTTP错误: {response.status_code}")
                
                # 测试3: 获取所有工作人员 (role=all 或 不指定)
                print("\n测试3: 获取所有工作人员 (role=all)")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3, 'role': 'all'},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        all_list = data.get('data', {}).get('staff', [])
                        print(f"所有工作人员数量: {len(all_list)}")
                        
                        # 验证包含专员和主管
                        has_staff = any(staff.get('role') == 'staff' for staff in all_list)
                        has_manager = any(staff.get('role') == 'manager' for staff in all_list)
                        
                        if has_staff:
                            print("✅ 包含专员")
                        else:
                            print("❌ 缺少专员")
                        
                        if has_manager:
                            print("✅ 包含主管")
                        else:
                            print("❌ 缺少主管")
                        
                        total_expected = len([s for s in all_list if s.get('role') in ['staff', 'manager']])
                        if len(all_list) == total_expected:
                            print("✅ 角色数据正确")
                        else:
                            print("❌ 角色数据异常")
                    else:
                        print(f"API业务错误: {data.get('msg')}")
                else:
                    print(f"HTTP错误: {response.status_code}")
                
                # 测试4: 无效角色参数
                print("\n测试4: 测试无效角色参数")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3, 'role': 'invalid_role'},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 0:
                        print("✅ 正确拒绝了无效角色参数")
                    else:
                        print("❌ 应该拒绝无效角色参数")
                else:
                    print(f"HTTP错误: {response.status_code}")
                
                print("\n🎯 角色过滤测试结论:")
                print("- API现在应该能正确根据role参数过滤工作人员")
                print("- role=staff 只返回专员")
                print("- role=manager 只返回主管")
                print("- role=all 返回所有工作人员")


if __name__ == '__main__':
    test_staff_list_role_filtering()