"""
手机认证服务
处理手机号码注册、登录和JWT令牌生成
"""

import os
import secrets
import datetime
import logging
from typing import Dict, Optional, Tuple
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# 确保环境变量已加载
load_dotenv()

from wxcloudrun.utils.phone_encryption import (
    validate_and_normalize_phone,
    encrypt_phone_number,
    get_phone_hash
)
from wxcloudrun.services.sms_service import get_sms_service
from wxcloudrun.model import User, PhoneAuth
from wxcloudrun.dao import insert_user, update_user_by_id, query_user_by_phone
import config

# 配置日志
logger = logging.getLogger(__name__)


class PhoneAuthService:
    """手机认证服务类"""
    
    def __init__(self):
        self.sms_service = get_sms_service()
        self.token_expiry_hours = 2  # 访问令牌2小时过期
        self.refresh_token_days = 7  # 刷新令牌7天过期
    
    def send_verification_code(self, phone_number: str) -> Tuple[bool, str, Optional[str]]:
        """
        发送短信验证码
        
        Args:
            phone_number: 手机号码
            
        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 消息, 验证码(仅模拟模式))
        """
        # 验证并标准化手机号码
        is_valid, error_msg, normalized_phone = validate_and_normalize_phone(phone_number)
        if not is_valid:
            return False, error_msg, None
        
        # 检查手机号码是否已注册
        existing_user = query_user_by_phone(normalized_phone)
        if existing_user:
            return False, "该手机号码已注册，请直接登录", None
        
        # 发送验证码
        success, message, code = self.sms_service.send_verification_code(normalized_phone)
        
        if success:
            logger.info(f"验证码已发送到手机号: {normalized_phone}")
            return True, "验证码发送成功", code
        else:
            logger.error(f"验证码发送失败: {message}")
            return False, message, None
    
    def verify_code_and_register(self, phone_number: str, verification_code: str, 
                                nickname: str = None, avatar_url: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """
        验证验证码并注册用户
        
        Args:
            phone_number: 手机号码
            verification_code: 验证码
            nickname: 用户昵称
            avatar_url: 用户头像URL
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 用户信息)
        """
        # 验证并标准化手机号码
        is_valid, error_msg, normalized_phone = validate_and_normalize_phone(phone_number)
        if not is_valid:
            return False, error_msg, None
        
        # 验证验证码
        success, message = self.sms_service.verify_code(normalized_phone, verification_code)
        if not success:
            return False, message, None
        
        # 检查手机号码是否已注册
        existing_user = query_user_by_phone(normalized_phone)
        if existing_user:
            return False, "该手机号码已注册", None
        
        try:
            # 创建用户
            user = self._create_phone_user(normalized_phone, nickname, avatar_url)
            if not user:
                return False, "用户创建失败", None
            
            # 生成JWT令牌
            tokens = self._generate_tokens(user)
            
            logger.info(f"手机号 {normalized_phone} 注册成功")
            return True, "注册成功", {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'auth_type': user.auth_type,
                'tokens': tokens
            }
            
        except Exception as e:
            logger.error(f"注册用户失败: {str(e)}")
            return False, f"注册失败: {str(e)}", None
    
    def login_with_password(self, phone_number: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        使用手机号和密码登录
        
        Args:
            phone_number: 手机号码
            password: 密码
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 用户信息)
        """
        # 验证并标准化手机号码
        is_valid, error_msg, normalized_phone = validate_and_normalize_phone(phone_number)
        if not is_valid:
            return False, error_msg, None
        
        # 查找用户
        user = query_user_by_phone(normalized_phone)
        if not user:
            return False, "用户不存在", None
        
        # 检查是否有手机认证
        if not hasattr(user, 'phone_auth') or not user.phone_auth:
            return False, "该用户未启用手机认证", None
        
        phone_auth = user.phone_auth
        
        # 检查账户是否被锁定
        if phone_auth.is_locked:
            return False, "账户已被锁定，请稍后再试", None
        
        # 检查认证方式是否支持密码
        if phone_auth.auth_methods not in ['password', 'both']:
            return False, "该账户不支持密码登录", None
        
        # 验证密码
        if not check_password_hash(phone_auth.password_hash, password):
            # 增加失败次数
            phone_auth.increment_failed_attempts()
            from wxcloudrun import db
            db.session.commit()
            
            if phone_auth.is_locked:
                return False, "密码错误次数过多，账户已被锁定", None
            else:
                remaining_attempts = 5 - phone_auth.failed_attempts
                return False, f"密码错误，还有{remaining_attempts}次尝试机会", None
        
        # 重置失败次数
        phone_auth.reset_failed_attempts()
        
        # 更新最后登录时间
        phone_auth.last_login_at = datetime.datetime.now()
        
        # 生成JWT令牌
        tokens = self._generate_tokens(user)
        
        logger.info(f"手机号 {normalized_phone} 密码登录成功")
        return True, "登录成功", {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'auth_type': user.auth_type,
            'auth_methods': phone_auth.auth_methods,
            'tokens': tokens
        }
    
    def login_with_sms(self, phone_number: str, verification_code: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        使用手机号和短信验证码登录
        
        Args:
            phone_number: 手机号码
            verification_code: 验证码
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 用户信息)
        """
        # 验证并标准化手机号码
        is_valid, error_msg, normalized_phone = validate_and_normalize_phone(phone_number)
        if not is_valid:
            return False, error_msg, None
        
        # 验证验证码
        success, message = self.sms_service.verify_code(normalized_phone, verification_code)
        if not success:
            return False, message, None
        
        # 查找用户
        user = query_user_by_phone(normalized_phone)
        if not user:
            return False, "用户不存在，请先注册", None
        
        # 检查是否有手机认证
        if not hasattr(user, 'phone_auth') or not user.phone_auth:
            return False, "该用户未启用手机认证", None
        
        phone_auth = user.phone_auth
        
        # 检查认证方式是否支持短信
        if phone_auth.auth_methods not in ['sms', 'both']:
            return False, "该账户不支持短信登录", None
        
        # 更新最后登录时间
        phone_auth.last_login_at = datetime.datetime.now()
        
        # 生成JWT令牌
        tokens = self._generate_tokens(user)
        
        logger.info(f"手机号 {normalized_phone} 短信登录成功")
        return True, "登录成功", {
            'user_id': user.user_id,
            'nickname': user.nickname,
            'auth_type': user.auth_type,
            'auth_methods': phone_auth.auth_methods,
            'tokens': tokens
        }
    
    def set_password(self, user_id: int, password: str) -> Tuple[bool, str]:
        """
        设置用户密码
        
        Args:
            user_id: 用户ID
            password: 密码
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        try:
            from wxcloudrun import db
            
            # 查找用户
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return False, "用户不存在"
            
            # 检查是否有手机认证
            if not hasattr(user, 'phone_auth') or not user.phone_auth:
                # 创建手机认证记录
                phone_auth = PhoneAuth(
                    user_id=user_id,
                    phone_number=user.phone_number,  # 这里应该是加密的手机号
                    auth_methods='password',
                    is_verified=True
                )
                db.session.add(phone_auth)
            else:
                phone_auth = user.phone_auth
            
            # 设置密码
            phone_auth.password_hash = generate_password_hash(password)
            
            # 如果之前只有短信认证，现在改为两种方式都支持
            if phone_auth.auth_methods == 'sms':
                phone_auth.auth_methods = 'both'
            
            # 更新用户认证类型
            if user.auth_type == 'wechat':
                user.auth_type = 'both'
            else:
                user.auth_type = 'phone'
            
            db.session.commit()
            logger.info(f"用户 {user_id} 密码设置成功")
            return True, "密码设置成功"
            
        except Exception as e:
            logger.error(f"设置密码失败: {str(e)}")
            return False, f"设置密码失败: {str(e)}"
    
    def refresh_token(self, refresh_token_str: str) -> Tuple[bool, str, Optional[Dict]]:
        """
        刷新访问令牌
        
        Args:
            refresh_token_str: 刷新令牌
            
        Returns:
            Tuple[bool, str, Optional[Dict]]: (是否成功, 消息, 新令牌)
        """
        try:
            from wxcloudrun import db
            
            # 查找用户
            user = User.query.filter_by(refresh_token=refresh_token_str).first()
            if not user:
                return False, "无效的刷新令牌", None
            
            # 检查刷新令牌是否过期
            if user.refresh_token_expire and user.refresh_token_expire < datetime.datetime.now():
                # 清除过期的刷新令牌
                user.refresh_token = None
                user.refresh_token_expire = None
                db.session.commit()
                return False, "刷新令牌已过期", None
            
            # 生成新的令牌
            tokens = self._generate_tokens(user)
            
            logger.info(f"用户 {user.user_id} 令牌刷新成功")
            return True, "令牌刷新成功", tokens
            
        except Exception as e:
            logger.error(f"刷新令牌失败: {str(e)}")
            return False, f"刷新令牌失败: {str(e)}", None
    
    def _create_phone_user(self, phone_number: str, nickname: str = None, 
                          avatar_url: str = None) -> Optional[User]:
        """创建手机用户"""
        try:
            from wxcloudrun import db
            
            # 加密手机号码
            encrypted_phone = encrypt_phone_number(phone_number)
            
            # 创建用户
            user = User(
                wechat_openid=None,  # 手机用户没有微信OpenID
                phone_number=encrypted_phone,
                nickname=nickname or f"用户{phone_number[-4:]}",
                avatar_url=avatar_url,
                auth_type='phone',
                is_solo_user=True,  # 默认为独居者
                status=1  # 正常状态
            )
            
            # 使用DAO插入用户
            insert_user(user)
            
            # 创建手机认证记录
            phone_auth = PhoneAuth(
                user_id=user.user_id,
                phone_number=encrypted_phone,
                auth_methods='sms',  # 默认只支持短信登录
                is_verified=True
            )
            
            db.session.add(phone_auth)
            db.session.commit()
            
            logger.info(f"手机用户创建成功: {user.user_id}")
            return user
            
        except Exception as e:
            logger.error(f"创建手机用户失败: {str(e)}")
            from wxcloudrun import db
            db.session.rollback()
            return None
    
    def _generate_tokens(self, user: User) -> Dict:
        """生成JWT令牌"""
        # 生成访问令牌
        token_payload = {
            'user_id': user.user_id,
            'phone_number': user.phone_number,  # 这里是加密的手机号
            'auth_type': user.auth_type,
            'exp': datetime.datetime.now() + datetime.timedelta(hours=self.token_expiry_hours),
            'iat': datetime.datetime.now()
        }
        
        token_secret = config.TOKEN_SECRET
        access_token = jwt.encode(token_payload, token_secret, algorithm='HS256')
        
        # 生成刷新令牌
        refresh_token = secrets.token_urlsafe(32)
        refresh_token_expire = datetime.datetime.now() + datetime.timedelta(days=self.refresh_token_days)
        
        # 更新用户的刷新令牌
        user.refresh_token = refresh_token
        user.refresh_token_expire = refresh_token_expire
        
        from wxcloudrun import db
        db.session.commit()
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': self.token_expiry_hours * 3600,  # 秒
            'token_type': 'Bearer'
        }


# 全局服务实例
_phone_auth_service = None


def get_phone_auth_service() -> PhoneAuthService:
    """获取手机认证服务实例"""
    global _phone_auth_service
    if _phone_auth_service is None:
        _phone_auth_service = PhoneAuthService()
    return _phone_auth_service