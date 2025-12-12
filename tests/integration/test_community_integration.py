"""
社区功能集成测试
"""

import pytest
import os
import sys
import json
import jwt
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wxcloudrun import app, db
from wxcloudrun.model import User, Community, CommunityAdmin, CommunityApplication
from wxcloudrun.community_service import CommunityService
from config_manager import get_token_secret


class TestCommunityAPI:
    """社区API集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # 创建测试用户
        self.create_test_users()
        
        # 创建测试社区
        self.create_test_communities()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def create_test_users(self):
        """创建测试用户"""
        # 超级管理员
        self.super_admin = User(
            wechat_openid='super_admin_openid',
            nickname='超级管理员',
            role=4
        )
        db.session.add(self.super_admin)
        
        # 社区管理员
        self.community_admin = User(
            wechat_openid='community_admin_openid',
            nickname='社区管理员',
            role=3
        )
        db.session.add(self.community_admin)
        
        # 普通用户
        self.normal_user = User(
            wechat_openid='normal_user_openid',
            nickname='普通用户',
            role=1
        )
        db.session.add(self.normal_user)
        
        db.session.commit()
    
    def create_test_communities(self):
        """创建测试社区"""
        # 测试社区1
        self.community1 = Community(
            name='测试社区1',
            description='第一个测试社区',
            creator_user_id=self.super_admin.user_id
        )
        db.session.add(self.community1)
        
        # 测试社区2
        self.community2 = Community(
            name='测试社区2',
            description='第二个测试社区',
            creator_user_id=self.super_admin.user_id
        )
        db.session.add(self.community2)
        
        db.session.commit()
        
        # 设置社区管理员
        admin_role = CommunityAdmin(
            community_id=self.community1.community_id,
            user_id=self.community_admin.user_id,
            role=1  # 主管理员
        )
        db.session.add(admin_role)
        
        # 设置普通用户所属社区
        self.normal_user.community_id = self.community1.community_id
        db.session.commit()
    
    def generate_token(self, user):
        """生成JWT token"""
        payload = {
            'openid': user.wechat_openid,
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(hours=2)
        }
        token_secret = get_token_secret()
        return jwt.encode(payload, token_secret, algorithm='HS256')
    
    def test_get_communities_super_admin(self):
        """测试超级管理员获取社区列表"""
        token = self.generate_token(self.super_admin)
        response = self.client.get(
            '/api/communities',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0  # 成功响应
        assert len(data['data']) == 2  # 两个测试社区
    
    def test_get_communities_normal_user_forbidden(self):
        """测试普通用户获取社区列表（应该被拒绝）"""
        token = self.generate_token(self.normal_user)
        response = self.client.get(
            '/api/communities',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 0  # 业务错误
        assert '权限不足' in data['msg']
    
    def test_get_community_detail(self):
        """测试获取社区详情"""
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community1.community_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        community_data = data['data']
        assert community_data['name'] == '测试社区1'
        assert 'admins' in community_data
        assert len(community_data['admins']) == 1
    
    def test_get_community_detail_forbidden(self):
        """测试获取其他社区详情（应该被拒绝）"""
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community2.community_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] == 0
        assert '权限不足' in data['msg']
    
    def test_get_community_admins(self):
        """测试获取社区管理员列表"""
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community1.community_id}/admins',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        admins = data['data']
        assert len(admins) == 1
        assert admins[0]['nickname'] == '社区管理员'
    
    def test_add_community_admins(self):
        """测试添加社区管理员"""
        # 创建新用户
        new_user = User(
            wechat_openid='new_user_openid',
            nickname='新用户',
            role=1
        )
        db.session.add(new_user)
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.post(
            f'/api/communities/{self.community1.community_id}/admins',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'user_ids': [new_user.user_id],
                'role': 2  # 普通管理员
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        results = data['data']
        assert len(results) == 1
        assert results[0]['success'] is True
    
    def test_remove_community_admin(self):
        """测试移除社区管理员"""
        # 先添加一个管理员
        new_user = User(
            wechat_openid='admin_to_remove',
            nickname='待移除管理员',
            role=1
        )
        db.session.add(new_user)
        db.session.commit()
        
        admin_role = CommunityAdmin(
            community_id=self.community1.community_id,
            user_id=new_user.user_id,
            role=2
        )
        db.session.add(admin_role)
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.delete(
            f'/api/communities/{self.community1.community_id}/admins/{new_user.user_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        assert '移除成功' in data['data']['message']
    
    def test_get_community_users(self):
        """测试获取社区用户列表"""
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community1.community_id}/users',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        users_data = data['data']
        assert users_data['total'] == 1  # 一个普通用户
        assert len(users_data['users']) == 1
        assert users_data['users'][0]['nickname'] == '普通用户'
    
    def test_search_community_users_by_phone(self):
        """测试通过电话号码搜索社区用户"""
        # 设置用户的电话号码
        self.normal_user.phone_number = '13800138000'
        from hashlib import sha256
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'default_secret')
        phone_hash = sha256(f"{phone_secret}:13800138000".encode('utf-8')).hexdigest()
        self.normal_user.phone_hash = phone_hash
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community1.community_id}/users?keyword=13800138000',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        users = data['data']['users']
        assert len(users) == 1
        assert users[0]['nickname'] == '普通用户'
    
    def test_search_community_users_by_nickname(self):
        """测试通过昵称搜索社区用户"""
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            f'/api/communities/{self.community1.community_id}/users?keyword=普通',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        users = data['data']['users']
        assert len(users) == 1
        assert users[0]['nickname'] == '普通用户'
    
    def test_set_user_as_admin(self):
        """测试将用户设为管理员"""
        token = self.generate_token(self.community_admin)
        response = self.client.post(
            f'/api/communities/{self.community1.community_id}/users/{self.normal_user.user_id}/set-admin',
            headers={'Authorization': f'Bearer {token}'},
            json={'role': 2}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        assert '设置成功' in data['data']['message']
    
    def test_create_community_application(self):
        """测试创建社区申请"""
        token = self.generate_token(self.normal_user)
        response = self.client.post(
            '/api/community/applications',
            headers={'Authorization': f'Bearer {token}'},
            json={
                'community_id': self.community2.community_id,
                'reason': '我想加入这个社区'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        assert '申请已提交' in data['data']['message']
    
    def test_get_community_applications(self):
        """测试获取社区申请列表"""
        # 创建申请
        application = CommunityApplication(
            user_id=self.normal_user.user_id,
            target_community_id=self.community2.community_id,
            reason='测试申请'
        )
        db.session.add(application)
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.get(
            '/api/community/applications',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        applications = data['data']
        assert len(applications) == 1
        assert applications[0]['reason'] == '测试申请'
    
    def test_approve_application(self):
        """测试批准申请"""
        # 创建申请
        application = CommunityApplication(
            user_id=self.normal_user.user_id,
            target_community_id=self.community2.community_id,
            status=1  # 待审核
        )
        db.session.add(application)
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.put(
            f'/api/community/applications/{application.application_id}/approve',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        assert '批准成功' in data['data']['message']
        
        # 检查用户已加入新社区
        db.session.refresh(self.normal_user)
        assert self.normal_user.community_id == self.community2.community_id
    
    def test_reject_application(self):
        """测试拒绝申请"""
        # 创建申请
        application = CommunityApplication(
            user_id=self.normal_user.user_id,
            target_community_id=self.community2.community_id,
            status=1  # 待审核
        )
        db.session.add(application)
        db.session.commit()
        
        token = self.generate_token(self.community_admin)
        response = self.client.put(
            f'/api/community/applications/{application.application_id}/reject',
            headers={'Authorization': f'Bearer {token}'},
            json={'rejection_reason': '不符合要求'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        assert '拒绝成功' in data['data']['message']
        
        # 检查申请状态
        db.session.refresh(application)
        assert application.status == 3  # 已拒绝
        assert application.rejection_reason == '不符合要求'
    
    def test_get_user_community(self):
        """测试获取用户社区信息"""
        token = self.generate_token(self.normal_user)
        response = self.client.get(
            '/api/user/community',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        user_community = data['data']
        assert user_community['community']['name'] == '测试社区1'
        assert user_community['is_admin'] is False
        assert user_community['is_primary_admin'] is False
    
    def test_get_available_communities(self):
        """测试获取可申请的社区列表"""
        token = self.generate_token(self.normal_user)
        response = self.client.get(
            '/api/communities/available',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['code'] != 0
        communities = data['data']
        assert len(communities) == 1  # 只有一个非默认社区
        assert communities[0]['name'] == '测试社区2'


class TestCommunityWorkflow:
    """社区工作流集成测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # 初始化默认社区
        CommunityService.get_or_create_default_community()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_registration_auto_assignment(self):
        """测试用户注册自动分配社区"""
        from wxcloudrun.views.auth import _format_user_login_response
        import jwt
        
        # 模拟微信登录
        with patch('wxcloudrun.wxchat_api.get_user_info_by_code') as mock_wx_api:
            mock_wx_api.return_value = {
                'openid': 'test_new_user_openid',
                'session_key': 'test_session_key'
            }
            
            response = self.client.post('/api/login', json={
                'code': 'test_code',
                'nickname': '新用户',
                'avatar_url': 'http://test.com/avatar.jpg'
            })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] != 0
            
            # 检查用户是否自动分配到默认社区
            user = User.query.filter_by(wechat_openid='test_new_user_openid').first()
            assert user is not None
            assert user.community_id is not None
            
            community = Community.query.get(user.community_id)
            assert community.name == '安卡大家庭'
    
    def test_community_application_flow(self):
        """测试完整的社区申请流程"""
        # 创建用户
        user = User(
            wechat_openid='applicant_openid',
            nickname='申请人',
            role=1
        )
        db.session.add(user)
        db.session.commit()
        
        # 创建新社区
        creator = User(
            wechat_openid='creator_openid',
            nickname='创建者',
            role=3
        )
        db.session.add(creator)
        db.session.commit()
        
        community = CommunityService.create_community(
            name='新社区',
            description='一个新社区',
            creator_id=creator.user_id
        )
        
        # 1. 用户提交申请
        user_token = self.generate_token(user)
        response = self.client.post('/api/community/applications', 
            headers={'Authorization': f'Bearer {user_token}'},
            json={
                'community_id': community.community_id,
                'reason': '我想加入这个社区'
            }
        )
        assert response.status_code == 200
        
        # 2. 管理员查看申请
        admin_token = self.generate_token(creator)
        response = self.client.get('/api/community/applications',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        applications = data['data']
        assert len(applications) == 1
        application_id = applications[0]['application_id']
        
        # 3. 管理员批准申请
        response = self.client.put(f'/api/community/applications/{application_id}/approve',
            headers={'Authorization': f'Bearer {admin_token}'}
        )
        assert response.status_code == 200
        
        # 4. 检查用户已加入社区
        db.session.refresh(user)
        assert user.community_id == community.community_id
        
        # 5. 用户查看社区信息
        response = self.client.get('/api/user/community',
            headers={'Authorization': f'Bearer {user_token}'}
        )
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['data']['community']['name'] == '新社区'
    
    def generate_token(self, user):
        """生成JWT token"""
        payload = {
            'openid': user.wechat_openid,
            'user_id': user.user_id,
            'exp': datetime.utcnow() + timedelta(hours=2)
        }
        token_secret = get_token_secret()
        return jwt.encode(payload, token_secret, algorithm='HS256')


if __name__ == '__main__':
    pytest.main([__file__])