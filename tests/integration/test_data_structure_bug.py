import pytest
from app import create_app


def test_search_users_data_structure_mismatch():
    """测试搜索用户时的数据结构不匹配问题"""
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
                
                # 测试API返回的数据结构
                response = client.get(
                    '/api/user/search-all-excluding-blackroom?keyword=微信&page=1&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 1
                
                # 验证返回的数据结构
                response_data = data.get('data', {})
                
                # 当前后端返回扁平化结构
                assert 'users' in response_data
                assert 'total' in response_data
                assert 'page' in response_data
                assert 'per_page' in response_data
                assert 'has_next' in response_data
                
                # 前端期望的pagination对象不存在（这是bug的原因）
                assert 'pagination' not in response_data
                
                # 验证数据类型
                assert isinstance(response_data['users'], list)
                assert isinstance(response_data['total'], int)
                assert isinstance(response_data['page'], int)
                assert isinstance(response_data['per_page'], int)
                assert isinstance(response_data['has_next'], bool)
                
                print("✓ 数据结构验证通过")
                print(f"✓ 用户数量: {len(response_data['users'])}")
                print(f"✓ 总数: {response_data['total']}")
                print(f"✓ 当前页: {response_data['page']}")
                print(f"✓ 每页数量: {response_data['per_page']}")
                print(f"✓ 是否有下一页: {response_data['has_next']}")


if __name__ == '__main__':
    test_search_users_data_structure_mismatch()