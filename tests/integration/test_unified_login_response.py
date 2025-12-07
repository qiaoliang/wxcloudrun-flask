"""
测试统一登录响应格式 (pytest版本)
"""
import sys
import os

import pytest

# 添加src路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wxcloudrun import db, app
from wxcloudrun.model import User
from wxcloudrun.views import _format_user_login_response


@pytest.fixture
def setup_db():
    """设置测试数据库"""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    with app.app_context():
        db.create_all()
        yield
        db.session.remove()
        db.drop_all()


class TestUnifiedLoginResponse:
    """统一登录响应格式测试"""
    
    def test_format_login_response_new_user(self, setup_db):
        """测试新用户登录响应格式"""
        # 创建测试用户
        user = User(
            wechat_openid="test_wx",
            phone_number="138****0001",
            phone_hash="test_phone",
            nickname="Test User",
            avatar_url="http://test.com/avatar.jpg",
            role=1,
            status=1
        )
        db.session.add(user)
        db.session.commit()
        
        # 格式化响应
        response = _format_user_login_response(
            user, "test_token", "test_refresh_token", is_new_user=True
        )
        
        # 验证响应字段
        assert response['token'] == "test_token"
        assert response['refresh_token'] == "test_refresh_token"
        assert response['user_id'] == user.user_id
        assert response['wechat_openid'] == "test_wx"
        assert response['phone_number'] == "138****0001"
        assert response['nickname'] == "Test User"
        assert response['avatar_url'] == "http://test.com/avatar.jpg"
        assert response['role'] == "solo"
        assert response['login_type'] == "new_user"
    
    def test_format_login_response_existing_user(self, setup_db):
        """测试老用户登录响应格式"""
        # 创建测试用户
        user = User(
            wechat_openid="test_wx2",
            phone_number=None,
            phone_hash=None,
            nickname="Test User 2",
            avatar_url=None,
            role=2,
            status=1
        )
        db.session.add(user)
        db.session.commit()
        
        # 格式化响应
        response = _format_user_login_response(
            user, "test_token2", "test_refresh_token2", is_new_user=False
        )
        
        # 验证响应字段
        assert response['token'] == "test_token2"
        assert response['refresh_token'] == "test_refresh_token2"
        assert response['user_id'] == user.user_id
        assert response['wechat_openid'] == "test_wx2"
        assert response['phone_number'] is None
        assert response['nickname'] == "Test User 2"
        assert response['avatar_url'] is None
        assert response['role'] == "supervisor"
        assert response['login_type'] == "existing_user"