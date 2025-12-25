import pytest
from app import create_app
from flask import request


def test_search_users_excluding_blackroom_with_invalid_page_parameter():
    """测试当page参数收到事件对象时的处理"""
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
                
                # 测试2：page参数为事件对象字符串（应该失败）
                invalid_page_string = '{"type":"tap","timeStamp":610948,"target":{"id":"","offsetLeft":16,"offsetTop":156,"dataset":{},"x":241.3248291015625,"y":420.07220458984375}}'
                response = client.get(
                    f'/api/user/search-all-excluding-blackroom?keyword=微信&page={invalid_page_string}&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                # 当前实现会返回500错误，修复后应该返回400错误
                assert response.status_code == 500
                
                # 测试3：page参数为非数字（应该失败）
                response = client.get(
                    '/api/user/search-all-excluding-blackroom?keyword=微信&page=abc&per_page=20&exclude_community_id=3',
                    headers=headers
                )
                # 当前实现会返回500错误，修复后应该返回400错误
                assert response.status_code == 500


if __name__ == '__main__':
    test_search_users_excluding_blackroom_with_invalid_page_parameter()