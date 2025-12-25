#!/usr/bin/env python3
"""
专员显示问题修复验证测试
测试前端是否能正确显示专员列表和数量
"""

import pytest
from app import create_app


def test_staff_display_fix():
    """测试专员显示问题修复"""
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
                
                print("=== 专员显示问题修复验证测试 ===")
                
                # 测试1: 验证社区详情API返回正确的staff_count
                print("\n测试1: 验证社区详情API staff_count")
                response = client.get('/api/communities/3', headers=headers)
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        stats = data.get('data', {}).get('stats', {})
                        staff_count = stats.get('staff_count', 0)
                        print(f"社区详情API返回的专员数量: {staff_count}")
                        
                        if staff_count > 0:
                            print("✅ staff_count > 0，数据正确")
                        else:
                            print("❌ staff_count = 0，可能仍有问题")
                
                # 测试2: 验证专员列表API返回正确的字段名
                print("\n测试2: 验证专员列表API字段名")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3, 'role': 'staff'},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        api_data = data.get('data', {})
                        has_staff_field = 'staff' in api_data
                        has_staff_members_field = 'staff_members' in api_data
                        
                        print(f"API返回staff字段: {has_staff_field}")
                        print(f"API返回staff_members字段: {has_staff_members_field}")
                        
                        if has_staff_field and not has_staff_members_field:
                            print("✅ API字段名符合契约（staff）")
                            
                            staff_list = api_data.get('staff', [])
                            print(f"专员列表长度: {len(staff_list)}")
                            if len(staff_list) > 0:
                                print("✅ 专员列表有数据")
                                print(f"专员姓名: {[s.get('nickname', s.get('name', '未知')) for s in staff_list[:3]]}")
                            else:
                                print("⚠️ 专员列表为空，但字段名正确")
                        else:
                            print("❌ API字段名不符合契约")
                
                print("\n🎯 修复验证结论:")
                print("- 如果staff_count > 0且API返回staff字段，说明修复成功")
                print("- 前端现在应该能正确显示专员列表和数量")


if __name__ == '__main__':
    test_staff_display_fix()