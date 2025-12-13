"""
测试用户搜索API的scope参数功能
遵循TDD原则：先写失败的测试，再实现功能
"""

import pytest
import sys
import os

# 设置测试环境变量
os.environ['ENV_TYPE'] = 'unit'

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from main import create_app
from wxcloudrun import db
from wxcloudrun.model import User
from wxcloudrun.dao import query_user_by_openid
import jwt
from config_manager import get_token_secret


class TestUserSearchScope:
    """用户搜索scope参数测试类"""

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        test_app = create_app()
        test_app.config.update({
            'TESTING': True,
            'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'WTF_CSRF_ENABLED': False
        })
        
        with test_app.app_context():
            db.create_all()
            yield test_app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()

    @pytest.fixture
    def super_admin_user(self, app):
        """创建超级管理员用户"""
        user = User(
            wechat_openid='super_admin_wx',
            nickname='Super Admin',
            role=4,  # 超级管理员
            status=1
        )
        db.session.add(user)
        db.session.commit()
        return user

    @pytest.fixture
    def community_admin_user(self, app):
        """创建社区管理员用户"""
        user = User(
            wechat_openid='community_admin_wx',
            nickname='Community Admin',
            role=3,  # 社区管理员
            status=1
        )
        db.session.add(user)
        db.session.commit()
        return user

    @pytest.fixture
    def test_users(self, app):
        """创建测试用户"""
        users = [
            User(
                wechat_openid='user1_wx',
                nickname='Test User 1',
                phone_number='13800138001',
                role=2,
                status=1
            ),
            User(
                wechat_openid='user2_wx',
                nickname='Test User 2',
                phone_number='13800138002',
                role=2,
                status=1
            )
        ]
        for user in users:
            db.session.add(user)
        db.session.commit()
        return users

    def get_auth_headers(self, user):
        """获取用户认证头"""
        token_secret = get_token_secret()
        token = jwt.encode(
            {'openid': user.wechat_openid},
            token_secret,
            algorithm='HS256'
        )
        return {'Authorization': f'Bearer {token}'}

    def test_search_users_with_scope_all(self, client, super_admin_user, test_users):
        """测试超级管理员使用scope=all搜索所有用户"""
        headers = self.get_auth_headers(super_admin_user)
        
        response = client.get('/api/users/search?keyword=test&scope=all', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'users' in data['data']

    def test_search_users_with_scope_community(self, client, community_admin_user, test_users):
        """测试社区管理员使用scope=community搜索社区用户"""
        headers = self.get_auth_headers(community_admin_user)
        
        response = client.get('/api/users/search?keyword=test&scope=community&community_id=1', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'users' in data['data']

    def test_search_users_with_invalid_scope(self, client, super_admin_user):
        """测试无效的scope参数"""
        headers = self.get_auth_headers(super_admin_user)
        
        response = client.get('/api/users/search?keyword=test&scope=invalid', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 0
        assert 'Invalid scope parameter' in data['msg']

    def test_search_users_scope_all_without_permission(self, client, community_admin_user):
        """测试非超级管理员使用scope=all"""
        headers = self.get_auth_headers(community_admin_user)
        
        response = client.get('/api/users/search?keyword=test&scope=all', headers=headers)
        
        assert response.status_code == 403
        data = response.get_json()
        assert data['code'] == 0
        assert 'Only super admin can search all users' in data['msg']

    def test_search_users_scope_community_missing_community_id(self, client, community_admin_user):
        """测试scope=community但缺少community_id参数"""
        headers = self.get_auth_headers(community_admin_user)
        
        response = client.get('/api/users/search?keyword=test&scope=community', headers=headers)
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['code'] == 0
        assert 'Community ID required for community scope' in data['msg']

    def test_search_users_by_phone_number(self, client, super_admin_user, test_users):
        """测试通过手机号搜索用户"""
        headers = self.get_auth_headers(super_admin_user)
        
        # 搜索完整手机号
        response = client.get('/api/users/search?keyword=13800138001&scope=all', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'users' in data['data']

        # 搜索部分手机号
        response = client.get('/api/users/search?keyword=138&scope=all', headers=headers)
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 1
        assert 'users' in data['data']