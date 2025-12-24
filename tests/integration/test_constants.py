"""
测试常量定义
统一管理测试中使用的常量数据，避免硬编码
"""

import os
import secrets
from typing import Dict, Any


class TestConstants:
    """测试常量类 - 统一管理测试常量数据"""
    
    # ==================== 认证相关常量 ====================
    
    # 默认测试密码
    DEFAULT_PASSWORD = "Firefox0820"
    
    # 默认密码盐（用于测试）
    @classmethod
    def generate_password_salt(cls) -> str:
        """生成测试用的密码盐"""
        return f"test_salt_{secrets.token_hex(4)}"
    
    # 默认手机加密密钥
    PHONE_ENC_SECRET = os.getenv('PHONE_ENC_SECRET', 'test_secret_key_for_testing')
    
    # ==================== 用户相关常量 ====================
    
    # 默认头像URL模板
    AVATAR_URL_TEMPLATE = "https://test-avatar.example.com/user_{}.jpg"
    
    @classmethod
    def generate_avatar_url(cls, user_id: str = None) -> str:
        """生成测试头像URL"""
        if user_id is None:
            user_id = secrets.token_hex(8)
        return cls.AVATAR_URL_TEMPLATE.format(user_id)
    
    # 默认用户信息模板
    DEFAULT_NICKNAME_TEMPLATE = "测试用户_{}"
    DEFAULT_USERNAME_TEMPLATE = "testuser_{}"
    
    @classmethod
    def generate_nickname(cls, suffix: str = None) -> str:
        """生成测试昵称"""
        if suffix is None:
            suffix = secrets.token_hex(4)
        return cls.DEFAULT_NICKNAME_TEMPLATE.format(suffix)
    
    @classmethod
    def generate_username(cls, suffix: str = None) -> str:
        """生成测试用户名"""
        if suffix is None:
            suffix = secrets.token_hex(4)
        return cls.DEFAULT_USERNAME_TEMPLATE.format(suffix)
    
    # ==================== 社区相关常量 ====================
    
    # 默认社区信息模板
    DEFAULT_COMMUNITY_NAME_TEMPLATE = "测试社区_{}"
    DEFAULT_COMMUNITY_DESCRIPTION_TEMPLATE = "用于测试的社区：{}"
    
    @classmethod
    def generate_community_name(cls, suffix: str = None) -> str:
        """生成测试社区名称"""
        if suffix is None:
            suffix = secrets.token_hex(4)
        return cls.DEFAULT_COMMUNITY_NAME_TEMPLATE.format(suffix)
    
    @classmethod
    def generate_community_description(cls, name: str = None) -> str:
        """生成测试社区描述"""
        if name is None:
            name = cls.generate_community_name()
        return cls.DEFAULT_COMMUNITY_DESCRIPTION_TEMPLATE.format(name)
    
    # ==================== 验证码相关常量 ====================
    
    # 测试验证码
    TEST_VERIFICATION_CODE = "123456"
    INVALID_VERIFICATION_CODE = "999999"
    
    # ==================== JWT相关常量 ====================
    
    # 测试Token密钥
    TOKEN_SECRET = os.getenv('TOKEN_SECRET', 'test_token_secret_for_testing')
    
    # ==================== API响应常量 ====================
    
    # 标准成功响应
    SUCCESS_RESPONSE = {"code": 1, "msg": "success"}
    
    # 标准错误响应
    ERROR_RESPONSE_TEMPLATE = {"code": 0, "msg": "{}"}
    
    @classmethod
    def generate_error_response(cls, msg: str) -> Dict[str, Any]:
        """生成错误响应"""
        return {"code": 0, "msg": msg}
    
    # ==================== 系统用户常量 ====================
    
    # 超级管理员固定信息（不可更改）
    SUPER_ADMIN_PHONE = "13900007997"
    SUPER_ADMIN_NICKNAME = "系统超级管理员"
    SUPER_ADMIN_NAME = "系统超级管理员"
    SUPER_ADMIN_ROLE = 4
    
    # ==================== 测试环境常量 ====================
    
    # 测试环境标识
    TEST_ENV_TYPE = "unit"
    
    # 测试数据库配置
    TEST_DATABASE_URL = "sqlite:///:memory:"
    
    # ==================== 调试和日志常量 ====================
    
    # 测试日志级别
    TEST_LOG_LEVEL = "INFO"
    
    # 测试会话标识
    @classmethod
    def generate_session_id(cls) -> str:
        """生成测试会话ID"""
        return f"test_session_{secrets.token_hex(8)}"


# 便捷实例
TEST_CONSTANTS = TestConstants()