"""
测试工具函数
提供统一的测试工具，避免重复代码，遵循KISS和DRY原则
"""

import os
import sys
import pytest
from typing import Optional, Dict, Any
from hashlib import sha256

# 导入测试常量
from test_constants import TEST_CONSTANTS

# 导入测试数据生成器
from test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname,
    generate_unique_username
)


class TestUserFactory:
    """统一的测试用户创建工厂"""
    
    @staticmethod
    def create_user(session=None, role=1, phone_number=None, password=None, test_context=None, **kwargs):
        """
        创建测试用户的统一方法
        
        Args:
            session: 数据库会话（unit测试需要，integration测试可选）
            role: 用户角色（1=普通用户, 2=社区专员, 3=社区主管, 4=超级管理员）
            phone_number: 手机号码，如果为None则自动生成
            password: 密码，如果为None则使用默认密码
            test_context: 测试上下文，用于生成唯一数据
            **kwargs: 其他用户属性
            
        Returns:
            创建的用户对象
        """
        # 导入数据库模型
        from database.flask_models import User
        
        # 生成唯一数据
        if phone_number is None:
            phone_number = generate_unique_phone_number(test_context or 'test_user')
        
        if password is None:
            password = TEST_CONSTANTS.DEFAULT_PASSWORD
        
        # 生成其他唯一标识
        open_id = generate_unique_openid(phone_number, test_context or 'test_user')
        nickname = generate_unique_nickname(test_context or 'test_user')
        username = generate_unique_username(test_context or 'test_user')
        
        # 生成密码哈希
        password_salt = TEST_CONSTANTS.generate_password_salt()
        password_hash = sha256(f"{password}:{password_salt}".encode('utf-8')).hexdigest()
        
        # 生成手机哈希
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        # 构建用户数据
        user_data = {
            'wechat_openid': open_id,
            'phone_number': phone_number,
            'phone_hash': phone_hash,
            'nickname': nickname,
            'name': username,
            'avatar_url': TEST_CONSTANTS.generate_avatar_url(phone_number),
            'role': role,
            'status': 1,
            'password_salt': password_salt,
            'password_hash': password_hash,
            'verification_status': 2,
        }
        user_data.update(kwargs)
        
        # 创建用户对象
        user = User(**user_data)
        
        # 如果有session，直接保存到数据库
        if session:
            session.add(user)
            session.commit()
        
        return user


class TestCommunityFactory:
    """统一的测试社区创建工厂"""
    
    @staticmethod
    def create_community(session=None, name=None, description=None, creator_id=None, **kwargs):
        """
        创建测试社区的统一方法
        
        Args:
            session: 数据库会话
            name: 社区名称，如果为None则自动生成
            description: 社区描述，如果为None则自动生成
            creator_id: 创建者ID
            **kwargs: 其他社区属性
            
        Returns:
            创建的社区对象
        """
        from database.flask_models import Community
        
        if name is None:
            name = TEST_CONSTANTS.generate_community_name()
        
        if description is None:
            description = TEST_CONSTANTS.generate_community_description(name)
        
        community_data = {
            'name': name,
            'description': description,
            'status': 1,
        }
        community_data.update(kwargs)
        
        if creator_id:
            community_data['creator_id'] = creator_id
        
        community = Community(**community_data)
        
        if session:
            session.add(community)
            session.commit()
        
        return community


class RolePermissionTester:
    """角色权限测试工具"""
    
    @staticmethod
    def create_user_with_role(test_instance, role: int, test_context: str = None, community_id: int = None):
        """
        创建指定角色的用户并建立社区关系
        
        Args:
            test_instance: 测试实例（需要app和db属性）
            role: 用户角色
            test_context: 测试上下文
            community_id: 社区ID
            
        Returns:
            创建的用户对象
        """
        with test_instance.app.app_context():
            user = TestUserFactory.create_user(
                session=test_instance.db.session,
                role=role,
                test_context=test_context
            )
            
            # 如果提供了社区ID，建立用户-社区关系
            if community_id:
                user.community_id = community_id
                test_instance.db.session.commit()
            
            return user
    
    @staticmethod
    def test_user_permissions(test_instance, user, expected_role: int, expected_role_name: str):
        """
        测试用户权限的通用方法
        
        Args:
            test_instance: 测试实例
            user: 用户对象
            expected_role: 期望的角色值
            expected_role_name: 期望的角色名称
        """
        response = test_instance.make_authenticated_request(
            'GET',
            '/api/user/profile',
            phone_number=user.phone_number,
            password=TEST_CONSTANTS.DEFAULT_PASSWORD
        )
        
        data = test_instance.assert_api_success(response, expected_data_keys=['role', 'role_name'])
        assert data['data']['role'] == expected_role, f"角色应该是{expected_role}，实际是: {data['data']['role']}"
        assert data['data']['role_name'] == expected_role_name, f"角色名称应该是'{expected_role_name}'，实际是: {data['data']['role_name']}"


class AuthRequestHelper:
    """认证请求辅助工具"""
    
    @staticmethod
    def create_auth_client(test_instance, user_role: int = 1, test_context: str = None):
        """
        创建已认证的测试客户端
        
        Args:
            test_instance: 测试实例
            user_role: 用户角色
            test_context: 测试上下文
            
        Returns:
            (client, user) 元组
        """
        with test_instance.app.app_context():
            user = TestUserFactory.create_user(
                session=test_instance.db.session,
                role=user_role,
                test_context=test_context
            )
            
            token = test_instance.get_jwt_token(
                phone_number=user.phone_number,
                password=TEST_CONSTANTS.DEFAULT_PASSWORD
            )
            
            client = test_instance.get_test_client()
            client.environ_base['HTTP_AUTHORIZATION'] = f'Bearer {token}'
            
            return client, user
    
    @staticmethod
    def make_role_based_request(test_instance, role: int, endpoint: str, method: str = 'GET', data: Any = None, test_context: str = None):
        """
        基于角色的认证请求
        
        Args:
            test_instance: 测试实例
            role: 用户角色
            endpoint: API端点
            method: HTTP方法
            data: 请求数据
            test_context: 测试上下文
            
        Returns:
            响应对象
        """
        with test_instance.app.app_context():
            user = TestUserFactory.create_user(
                session=test_instance.db.session,
                role=role,
                test_context=test_context
            )
            
            return test_instance.make_authenticated_request(
                method,
                endpoint,
                data=data,
                phone_number=user.phone_number,
                password=TEST_CONSTANTS.DEFAULT_PASSWORD
            )


# 向后兼容的函数
def create_test_user(test_session=None, role=1, test_context="test_user", **kwargs):
    """向后兼容的测试用户创建函数"""
    return TestUserFactory.create_user(
        session=test_session,
        role=role,
        test_context=test_context,
        **kwargs
    )


def create_test_community(test_session=None, name_suffix=None, **kwargs):
    """向后兼容的测试社区创建函数"""
    name = TEST_CONSTANTS.generate_community_name(name_suffix) if name_suffix else None
    return TestCommunityFactory.create_community(
        session=test_session,
        name=name,
        **kwargs
    )