import pytest
from app import create_app


def test_staff_list_refresh_after_adding():
    """测试添加专员后列表刷新问题"""
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
                
                print("=== 专员列表刷新测试 ===")
                
                # 测试1: 获取当前专员列表
                print("\n测试1: 获取当前专员列表")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        staff_list = data.get('data', {}).get('staff', [])
                        print(f"当前专员数量: {len(staff_list)}")
                        print(f"专员列表: {[s.get('nickname', s.get('name', '未知')) for s in staff_list[:3]]}")
                
                # 测试2: 添加新专员
                print("\n测试2: 添加新专员")
                response = client.post('/api/community/add-staff',
                    json={
                        'community_id': 3,
                        'user_ids': [800000001],
                        'role': 'staff'
                    },
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    print(f"添加结果: {data}")
                    if data.get('code') == 1:
                        added_count = data.get('data', {}).get('added_count', 0)
                        print(f"成功添加专员数量: {added_count}")
                
                # 测试3: 再次获取专员列表验证刷新
                print("\n测试3: 验证专员列表刷新")
                response = client.get('/api/community/staff/list-enhanced',
                    params={'community_id': 3},
                    headers=headers
                )
                print(f"状态码: {response.status_code}")
                if response.status_code == 200:
                    data = response.get_json()
                    if data.get('code') == 1:
                        staff_list = data.get('data', {}).get('staff', [])
                        print(f"刷新后专员数量: {len(staff_list)}")
                        print(f"专员列表: {[s.get('nickname', s.get('name', '未知')) for s in staff_list[:3]]}")
                        
                        # 验证是否包含新添加的专员
                        new_staff_found = any(
                            s.get('user_id') == 800000001 or 
                            s.get('phone_number', '').endswith('80000001')
                            for s in staff_list
                        )
                        
                        if new_staff_found:
                            print("✅ 后端数据正确：新专员已添加到列表")
                        else:
                            print("❌ 后端数据问题：新专员未在列表中找到")
                
                print("\n🎯 测试结论:")
                print("- 如果后端API正确返回新专员，说明后端逻辑正常")
                print("- 前端问题在于confirmAddStaff函数是模拟实现")
                print("- 需要修复前端的数据刷新机制")


if __name__ == '__main__':
    test_staff_list_refresh_after_adding()