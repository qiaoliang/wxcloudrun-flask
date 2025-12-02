# tests/test_user_search_api.py
import pytest
import json
from wxcloudrun import app, db
from wxcloudrun.model import User


class TestUserSearchAPI:
    """用户搜索API测试"""
    
    def test_search_users_minimum_length(self, client):
        """测试搜索关键词最小长度限制"""
        # 模拟登录用户
        with app.test_request_context():
            # 设置g.current_user
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/users/search?nickname=a')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert data['data']['users'] == []  # 小于2个字符应返回空列表
    
    def test_search_users_empty_nickname(self, client):
        """测试空昵称搜索"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/users/search?nickname=')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert data['data']['users'] == []
    
    def test_search_users_success(self, client, setup_users):
        """测试成功搜索用户"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/users/search?nickname=测试')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'users' in data['data']
            assert len(data['data']['users']) > 0
            
            # 检查返回的用户数据结构
            user = data['data']['users'][0]
            assert 'user_id' in user
            assert 'nickname' in user
            assert 'avatar_url' in user
            assert 'is_supervisor' in user
            assert 'permissions' in user
    
    def test_search_users_exclude_self(self, client, setup_users):
        """测试搜索结果排除自己"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/users/search?nickname=用户1')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            # 应该不返回自己
            for user in data['data']['users']:
                assert user['user_id'] != 1
    
    def test_search_users_limit(self, client, setup_users):
        """测试搜索结果数量限制"""
        with app.test_request_context():
            from flask import g
            g.current_user = type('User', (), {'user_id': 1})()
            
            response = client.get('/api/users/search?nickname=用户&limit=5')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert data['code'] == 1
            assert len(data['data']['users']) <= 5


@pytest.fixture
def setup_users():
    """设置测试用户数据"""
    with app.app_context():
        # 创建测试用户
        users = [
            User(
                user_id=1,
                wechat_openid='test1',
                nickname='用户1',
                is_supervisor=True,
                status=1
            ),
            User(
                user_id=2,
                wechat_openid='test2',
                nickname='测试用户2',
                is_supervisor=True,
                status=1
            ),
            User(
                user_id=3,
                wechat_openid='test3',
                nickname='用户3',
                is_supervisor=False,
                status=1
            )
        ]
        
        for user in users:
            db.session.add(user)
        db.session.commit()
        
        yield
        
        # 清理测试数据
        for user in users:
            db.session.delete(user)
        db.session.commit()