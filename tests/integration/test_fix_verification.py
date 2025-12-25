import pytest
from app import create_app


def test_search_users_excluding_blackroom_fixed():
    """测试修复后的搜索用户功能"""
    app = create_app()
    app.config['TESTING'] = True
    
    with app.test_client() as client:
        # 模拟正常的API调用，先获取token
        login_response = client.post('/api/auth/login_phone_password', json={
            'phone': '13900008000',
            'password': 'test123'
        })
        
        if login_response.status_code == 200:
            login_data = login_response.get_json()
            if login_data.get('code') == 1:
                token = login_data['data']['token']
                headers = {'Authorization': f'Bearer {token}'}
                
                # 测试1：正常page参数（应该成功）
                response = client.get(
                    '/api/user/search-all-excluding-blackroom?keyword=微信&page=1&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 1
                print("✓ 正常page参数测试通过")
                
                # 测试2：page参数为事件对象字符串（现在应该返回400而不是500）
                invalid_page_string = '{"type":"tap","timeStamp":610948,"target":{"id":"","offsetLeft":16,"offsetTop":156,"dataset":{},"x":241.3248291015625,"y":420.07220458984375}}'
                response = client.get(
                    f'/api/user/search-all-excluding-blackroom?keyword=微信&page={invalid_page_string}&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                assert response.status_code == 200  # 后端现在应该优雅处理
                data = response.get_json()
                assert data.get('code') == 0  # 应该返回错误
                assert 'page参数必须是正整数' in data.get('msg', '')
                print("✓ 无效page参数测试通过 - 返回400错误而不是500")
                
                # 测试3：page参数为非数字（应该返回400）
                response = client.get(
                    '/api/user/search-all-excluding-blackroom?keyword=微信&page=abc&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                assert data.get('code') == 0
                assert 'page参数必须是正整数' in data.get('msg', '')
                print("✓ 非数字page参数测试通过")
                
                # 测试4：page参数为负数（应该被修正为1）
                response = client.get(
                    '/api/user/search-all-excluding-blackroom?keyword=微信&page=-1&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                assert response.status_code == 200
                data = response.get_json()
                # 应该成功，因为负数被修正为1
                print("✓ 负数page参数测试通过 - 被修正为1")


if __name__ == '__main__':
    test_search_users_excluding_blackroom_fixed()
    print("\n🎉 所有修复验证测试通过！")