"""
社区功能单元测试
"""

import pytest
import os
import sys
from datetime import datetime
from unittest.mock import patch, MagicMock

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from wxcloudrun import create_app, db
from wxcloudrun.model import User, Community, CommunityAdmin, CommunityApplication
from wxcloudrun.community_service import CommunityService


class TestCommunityModel:
    """社区模型测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_community(self):
        """测试创建社区"""
        # 创建用户
        user = User(
            wechat_openid='test_openid',
            nickname='测试用户',
            role=4  # 超级管理员
        )
        db.session.add(user)
        db.session.commit()
        
        # 创建社区
        community = Community(
            name='测试社区',
            description='这是一个测试社区',
            creator_user_id=user.user_id
        )
        db.session.add(community)
        db.session.commit()
        
        assert community.community_id is not None
        assert community.name == '测试社区'
        assert community.status == 1  # 默认启用
        assert community.is_default is False  # 默认非默认社区
        assert community.status_name == 'enabled'
    
    def test_community_status_mapping(self):
        """测试社区状态映射"""
        # 测试启用状态
        community = Community(name='测试', status=1)
        assert community.status_name == 'enabled'
        
        # 测试禁用状态
        community.status = 2
        assert community.status_name == 'disabled'
        
        # 测试未知状态
        community.status = 999
        assert community.status_name == 'unknown'
    
    def test_create_community_admin(self):
        """测试创建社区管理员"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        db.session.add_all([user, community])
        db.session.commit()
        
        # 创建管理员
        admin = CommunityAdmin(
            community_id=community.community_id,
            user_id=user.user_id,
            role=1  # 主管理员
        )
        db.session.add(admin)
        db.session.commit()
        
        assert admin.admin_id is not None
        assert admin.role == 1
        assert admin.role_name == 'primary'
    
    def test_community_admin_role_mapping(self):
        """测试管理员角色映射"""
        admin = CommunityAdmin()
        
        # 测试主管理员
        admin.role = 1
        assert admin.role_name == 'primary'
        
        # 测试普通管理员
        admin.role = 2
        assert admin.role_name == 'normal'
        
        # 测试未知角色
        admin.role = 999
        assert admin.role_name == 'unknown'
    
    def test_create_community_application(self):
        """测试创建社区申请"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        db.session.add_all([user, community])
        db.session.commit()
        
        # 创建申请
        application = CommunityApplication(
            user_id=user.user_id,
            target_community_id=community.community_id,
            reason='我想加入这个社区'
        )
        db.session.add(application)
        db.session.commit()
        
        assert application.application_id is not None
        assert application.status == 1  # 默认待审核
        assert application.status_name == 'pending'
    
    def test_community_application_status_mapping(self):
        """测试申请状态映射"""
        application = CommunityApplication()
        
        # 测试待审核
        application.status = 1
        assert application.status_name == 'pending'
        
        # 测试已批准
        application.status = 2
        assert application.status_name == 'approved'
        
        # 测试已拒绝
        application.status = 3
        assert application.status_name == 'rejected'
        
        # 测试未知状态
        application.status = 999
        assert application.status_name == 'unknown'


class TestUserCommunityMethods:
    """用户社区相关方法测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_is_community_admin(self):
        """测试是否为社区管理员"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        db.session.add_all([user, community])
        db.session.commit()
        
        # 未设置社区时
        assert not user.is_community_admin()
        
        # 设置用户社区但不是管理员
        user.community_id = community.community_id
        db.session.commit()
        assert not user.is_community_admin()
        
        # 设置为管理员
        admin = CommunityAdmin(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(admin)
        db.session.commit()
        assert user.is_community_admin()
    
    def test_is_primary_admin(self):
        """测试是否为主管理员"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        db.session.add_all([user, community])
        db.session.commit()
        
        # 设置为普通管理员
        admin = CommunityAdmin(
            community_id=community.community_id,
            user_id=user.user_id,
            role=2  # 普通管理员
        )
        db.session.add(admin)
        db.session.commit()
        assert not user.is_primary_admin()
        
        # 升级为主管理员
        admin.role = 1
        db.session.commit()
        assert user.is_primary_admin()
    
    def test_super_admin_permissions(self):
        """测试超级管理员权限"""
        # 创建超级管理员
        super_admin = User(
            wechat_openid='admin_openid',
            nickname='超级管理员',
            role=4  # 超级管理员
        )
        db.session.add(super_admin)
        db.session.commit()
        
        # 超级管理员应该拥有所有社区的管理权限
        assert super_admin.is_community_admin()
        assert super_admin.is_primary_admin()
        assert super_admin.can_manage_community(999)  # 任意社区ID
    
    def test_apply_to_community(self):
        """测试申请加入社区"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        db.session.add_all([user, community])
        db.session.commit()
        
        # 申请加入社区
        success, message = user.apply_to_community(community.community_id, '测试申请')
        assert success
        assert '申请已提交' in message
        
        # 检查申请记录
        application = CommunityApplication.query.filter_by(
            user_id=user.user_id,
            target_community_id=community.community_id
        ).first()
        assert application is not None
        assert application.reason == '测试申请'
        
        # 重复申请应该失败
        success, message = user.apply_to_community(community.community_id)
        assert not success
        assert '待处理的申请' in message
    
    def test_get_managed_communities(self):
        """测试获取管理的社区列表"""
        # 创建用户和多个社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community1 = Community(name='社区1')
        community2 = Community(name='社区2')
        community3 = Community(name='社区3')
        db.session.add_all([user, community1, community2, community3])
        db.session.commit()
        
        # 设置为部分社区的管理员
        admin1 = CommunityAdmin(community_id=community1.community_id, user_id=user.user_id)
        admin2 = CommunityAdmin(community_id=community2.community_id, user_id=user.user_id)
        db.session.add_all([admin1, admin2])
        db.session.commit()
        
        # 获取管理的社区
        managed = user.get_managed_communities()
        assert len(managed) == 2
        assert community1 in managed
        assert community2 in managed
        assert community3 not in managed


class TestCommunityService:
    """社区服务测试"""
    
    def setup_method(self):
        """测试前准备"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def teardown_method(self):
        """测试后清理"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    @patch.dict(os.environ, {'PHONE_ENC_SECRET': 'test_secret'})
    def test_get_or_create_default_community(self):
        """测试获取或创建默认社区"""
        # 第一次调用应该创建社区
        community = CommunityService.get_or_create_default_community()
        assert community is not None
        assert community.name == '安卡大家庭'
        assert community.is_default is True
        
        # 第二次调用应该返回现有社区
        community2 = CommunityService.get_or_create_default_community()
        assert community.community_id == community2.community_id
    
    @patch.dict(os.environ, {'PHONE_ENC_SECRET': 'test_secret'})
    def test_ensure_super_admin_exists(self):
        """测试确保超级管理员存在"""
        # 调用方法创建超级管理员
        admin = CommunityService._ensure_super_admin_exists()
        assert admin is not None
        assert admin.role == 4
        assert admin.phone_number == '13900007997'
        
        # 验证密码哈希正确
        from hashlib import sha256
        pwd_hash = sha256(f"Firefox0820:{admin.password_salt}".encode('utf-8')).hexdigest()
        assert admin.password_hash == pwd_hash
    
    def test_create_community(self):
        """测试创建社区"""
        # 创建用户
        user = User(wechat_openid='test_openid', nickname='测试用户')
        db.session.add(user)
        db.session.commit()
        
        # 创建社区
        community = CommunityService.create_community(
            name='新社区',
            description='社区描述',
            creator_id=user.user_id,
            location='北京'
        )
        
        assert community is not None
        assert community.name == '新社区'
        assert community.creator_user_id == user.user_id
        
        # 创建者应该自动成为主管理员
        admin = CommunityAdmin.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert admin is not None
        assert admin.role == 1
    
    def test_add_community_admin(self):
        """测试添加社区管理员"""
        # 创建用户和社区
        user1 = User(wechat_openid='test_openid1', nickname='用户1')
        user2 = User(wechat_openid='test_openid2', nickname='用户2')
        community = Community(name='测试社区')
        db.session.add_all([user1, user2, community])
        db.session.commit()
        
        # 添加管理员
        admin = CommunityService.add_community_admin(
            community_id=community.community_id,
            user_id=user2.user_id,
            role=2  # 普通管理员
        )
        
        assert admin is not None
        assert admin.user_id == user2.user_id
        assert admin.role == 2
    
    def test_remove_community_admin(self):
        """测试移除社区管理员"""
        # 创建用户和社区
        user1 = User(wechat_openid='test_openid1', nickname='用户1')
        user2 = User(wechat_openid='test_openid2', nickname='用户2')
        community = Community(name='测试社区')
        admin1 = CommunityAdmin(community_id=community.community_id, user_id=user1.user_id, role=1)
        admin2 = CommunityAdmin(community_id=community.community_id, user_id=user2.user_id, role=2)
        db.session.add_all([user1, user2, community, admin1, admin2])
        db.session.commit()
        
        # 移除普通管理员
        CommunityService.remove_community_admin(
            community_id=community.community_id,
            user_id=user2.user_id
        )
        
        # 检查管理员已被移除
        admin = CommunityAdmin.query.filter_by(
            community_id=community.community_id,
            user_id=user2.user_id
        ).first()
        assert admin is None
    
    def test_process_application_approve(self):
        """测试批准申请"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        application = CommunityApplication(
            user_id=user.user_id,
            target_community_id=community.community_id,
            status=1  # 待审核
        )
        db.session.add_all([user, community, application])
        db.session.commit()
        
        # 批准申请
        CommunityService.process_application(
            application_id=application.application_id,
            approve=True,
            processor_id=user.user_id
        )
        
        # 检查申请状态
        db.session.refresh(application)
        assert application.status == 2  # 已批准
        
        # 检查用户已加入社区
        db.session.refresh(user)
        assert user.community_id == community.community_id
    
    def test_process_application_reject(self):
        """测试拒绝申请"""
        # 创建用户和社区
        user = User(wechat_openid='test_openid', nickname='测试用户')
        community = Community(name='测试社区')
        application = CommunityApplication(
            user_id=user.user_id,
            target_community_id=community.community_id,
            status=1  # 待审核
        )
        db.session.add_all([user, community, application])
        db.session.commit()
        
        # 拒绝申请
        CommunityService.process_application(
            application_id=application.application_id,
            approve=False,
            processor_id=user.user_id,
            rejection_reason='不符合要求'
        )
        
        # 检查申请状态
        db.session.refresh(application)
        assert application.status == 3  # 已拒绝
        assert application.rejection_reason == '不符合要求'
        
        # 检查用户未加入社区
        db.session.refresh(user)
        assert user.community_id is None
    
    @patch.dict(os.environ, {'PHONE_ENC_SECRET': 'test_secret'})
    def test_search_community_users_by_phone(self):
        """测试通过电话号码搜索社区用户"""
        # 创建用户和社区
        user1 = User(
            wechat_openid='test_openid1',
            nickname='用户1',
            phone_number='13800138000'
        )
        user2 = User(
            wechat_openid='test_openid2',
            nickname='用户2',
            phone_number='13800138001'
        )
        community = Community(name='测试社区')
        db.session.add_all([user1, user2, community])
        db.session.commit()
        
        # 设置用户所属社区
        user1.community_id = community.community_id
        user2.community_id = community.community_id
        db.session.commit()
        
        # 搜索用户
        from hashlib import sha256
        phone_secret = os.getenv('PHONE_ENC_SECRET', 'test_secret')
        phone_hash = sha256(f"{phone_secret}:13800138000".encode('utf-8')).hexdigest()
        user1.phone_hash = phone_hash
        phone_hash = sha256(f"{phone_secret}:13800138001".encode('utf-8')).hexdigest()
        user2.phone_hash = phone_hash
        db.session.commit()
        
        # 搜索测试
        pagination = CommunityService.search_community_users(
            community_id=community.community_id,
            keyword='13800138000'
        )
        
        assert len(pagination.items) == 1
        assert pagination.items[0].user_id == user1.user_id
    
    def test_search_community_users_by_nickname(self):
        """测试通过昵称搜索社区用户"""
        # 创建用户和社区
        user1 = User(wechat_openid='test_openid1', nickname='张三')
        user2 = User(wechat_openid='test_openid2', nickname='张小明')
        user3 = User(wechat_openid='test_openid3', nickname='李四')
        community = Community(name='测试社区')
        db.session.add_all([user1, user2, user3, community])
        db.session.commit()
        
        # 设置用户所属社区
        user1.community_id = community.community_id
        user2.community_id = community.community_id
        user3.community_id = community.community_id
        db.session.commit()
        
        # 搜索包含"张"的用户
        pagination = CommunityService.search_community_users(
            community_id=community.community_id,
            keyword='张'
        )
        
        # 应该找到2个用户
        assert len(pagination.items) == 2
        nicknames = [u.nickname for u in pagination.items]
        assert '张三' in nicknames
        assert '张小明' in nicknames
    
    def test_get_available_communities(self):
        """测试获取可申请的社区列表"""
        # 创建社区
        default_community = Community(name='安卡大家庭', is_default=True)
        enabled_community = Community(name='可用社区', status=1, is_default=False)
        disabled_community = Community(name='禁用社区', status=2, is_default=False)
        db.session.add_all([default_community, enabled_community, disabled_community])
        db.session.commit()
        
        # 获取可申请社区
        available = CommunityService.get_available_communities()
        
        # 应该只返回启用且非默认的社区
        assert len(available) == 1
        assert available[0].name == '可用社区'


if __name__ == '__main__':
    pytest.main([__file__])