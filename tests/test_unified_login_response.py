#!/usr/bin/env python3
"""
测试统一登录响应格式
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from datetime import datetime, timedelta
import unittest
from wxcloudrun import db, app
from wxcloudrun.model import User
from wxcloudrun.views import _format_user_login_response

class TestUnifiedLoginResponse(unittest.TestCase):
    
    def setUp(self):
        """设置测试环境"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        with app.app_context():
            db.create_all()
    
    def tearDown(self):
        """清理测试环境"""
        with app.app_context():
            db.session.remove()
            db.drop_all()
    
    def test_format_login_response_new_user(self):
        """测试新用户登录响应格式"""
        with app.app_context():
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
            self.assertEqual(response['token'], "test_token")
            self.assertEqual(response['refresh_token'], "test_refresh_token")
            self.assertEqual(response['user_id'], user.user_id)
            self.assertEqual(response['wechat_openid'], "test_wx")
            self.assertEqual(response['phone_number'], "138****0001")
            self.assertEqual(response['nickname'], "Test User")
            self.assertEqual(response['avatar_url'], "http://test.com/avatar.jpg")
            self.assertEqual(response['role'], "solo")
            self.assertEqual(response['login_type'], "new_user")
    
    def test_format_login_response_existing_user(self):
        """测试老用户登录响应格式"""
        with app.app_context():
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
            self.assertEqual(response['token'], "test_token2")
            self.assertEqual(response['refresh_token'], "test_refresh_token2")
            self.assertEqual(response['user_id'], user.user_id)
            self.assertEqual(response['wechat_openid'], "test_wx2")
            self.assertIsNone(response['phone_number'])
            self.assertEqual(response['nickname'], "Test User 2")
            self.assertIsNone(response['avatar_url'])
            self.assertEqual(response['role'], "supervisor")
            self.assertEqual(response['login_type'], "existing_user")

if __name__ == '__main__':
    unittest.main()