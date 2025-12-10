"""
角色更新API端点测试
"""

import pytest
import os
import sys
import json
from unittest.mock import patch

# 设置环境变量为单元测试环境
os.environ['ENV_TYPE'] = 'unit'

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wxcloudrun import app, db
from wxcloudrun.model import User, Community, CommunityAdmin
from wxcloudrun.views.community import (
    _check_super_admin_permission,
    _check_community_admin_permission
)


class TestRoleUpdateAPI:
    """角色更新API测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = app
        self.app.config['TESTING'] = True
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        self.client = self.app.test_client()
        
        # 创建测试用户
        self.super_admin = User(
            wechat_openid='super_admin_openid',
            nickname='超级管理员',
            role=4
        )
        self.community_admin = User(
            wechat_openid='community_admin_openid',
            nickname='社区管理员',
            role=3
        )
        self.test_admin = User(
            wechat_openid='test_admin_openid',
            nickname='测试管理员',
            role=3
        )
        db.session.add_all([self.super_admin, self.community_admin, self.test_admin])
        db.session.commit()
        
        # 创建测试社区
        self.community = Community(
            name='测试社区',
            creator_user_id=self.super_admin.user_id
        )
        db.session.add(self.community)
        db.session.commit()
        
        # 添加社区管理员
        self.community_admin_record = CommunityAdmin(
            community_id=self.community.community_id,
            user_id=self.test_admin.user_id,
            role=2  # 社区专员
        )
        db.session.add(self.community_admin_record)
        db.session.commit()
        
        # 创建模拟token
        self.super_admin_token = f"fake_token_{self.super_admin.user_id}"
        self.community_admin_token = f"fake_token_{self.community_admin.user_id}"
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def patch_verify_token(self, user_id):
        """模拟token验证"""
        def mock_verify_token():
            return {'user_id': user_id}, None
        return mock_verify_token
    
    def test_update_admin_role_success(self):
        """测试成功更新管理员角色"""
        # 模拟超级管理员token验证
        with patch('wxcloudrun.views.community.verify_token', 
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{self.test_admin.user_id}/role',
                data=json.dumps({'role': 1}),
                content_type='application/json'
            )
            
            # 检查响应
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 1
            assert 'message' in data['data']
            
            # 验证数据库中的角色已更新
            updated_admin = CommunityAdmin.query.filter_by(
                community_id=self.community.community_id,
                user_id=self.test_admin.user_id
            ).first()
            assert updated_admin.role == 1
    
    def test_update_admin_role_invalid_role(self):
        """测试更新为无效角色"""
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{self.test_admin.user_id}/role',
                data=json.dumps({'role': 3}),  # 无效角色
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert 'Invalid role' in data['msg']
    
    def test_update_admin_role_non_super_admin(self):
        """测试非超级管理员尝试更新角色"""
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.community_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{self.test_admin.user_id}/role',
                data=json.dumps({'role': 1}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert '需要超级管理员权限' in data['msg']
    
    def test_update_admin_role_user_not_admin(self):
        """测试更新非社区管理员的用户角色"""
        non_admin_user = User(
            wechat_openid='non_admin_openid',
            nickname='非管理员用户',
            role=2
        )
        db.session.add(non_admin_user)
        db.session.commit()
        
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{non_admin_user.user_id}/role',
                data=json.dumps({'role': 1}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert '不是该社区的管理员' in data['msg']
    
    def test_update_admin_role_remove_last_supervisor(self):
        """测试尝试移除最后一个社区主管"""
        # 将测试管理员设为唯一的主管
        self.community_admin_record.role = 1
        db.session.commit()
        
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{self.test_admin.user_id}/role',
                data=json.dumps({'role': 2}),  # 尝试降级为专员
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert '不能移除最后一个社区主管' in data['msg']
    
    def test_update_admin_role_community_not_found(self):
        """测试社区不存在"""
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                '/api/communities/99999/admins/{}/role'.format(self.test_admin.user_id),
                data=json.dumps({'role': 1}),
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert '社区不存在' in data['msg']
    
    def test_update_admin_role_missing_role_parameter(self):
        """测试缺少角色参数"""
        with patch('wxcloudrun.views.community.verify_token',
                   side_effect=self.patch_verify_token(self.super_admin.user_id)):
            
            response = self.client.put(
                f'/api/communities/{self.community.community_id}/admins/{self.test_admin.user_id}/role',
                data=json.dumps({}),  # 缺少role参数
                content_type='application/json'
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['code'] == 0
            assert '缺少请求参数' in data['msg']


if __name__ == '__main__':
    pytest.main([__file__])