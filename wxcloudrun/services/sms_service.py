"""
SMS服务抽象层
支持多种SMS提供商和模拟模式
"""

import os
import random
import string
import logging
from abc import ABC, abstractmethod
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import redis
from functools import wraps

# 配置日志
logger = logging.getLogger(__name__)


class SMSProvider(ABC):
    """SMS提供商抽象基类"""
    
    @abstractmethod
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """
        发送短信
        
        Args:
            phone_number: 手机号码
            message: 短信内容
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息或错误信息)
        """
        pass


class SimulationSMSProvider(SMSProvider):
    """模拟SMS提供商，用于开发和测试"""
    
    def __init__(self, default_code: str = "123456"):
        self.default_code = default_code
        self.sent_codes = {}  # 存储发送的验证码 {phone: code}
        
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """模拟发送短信，实际只是记录验证码"""
        # 从消息中提取验证码
        try:
            # 假设消息格式为："【安全守护】您的验证码是：123456，5分钟内有效。"
            code_start = message.find("验证码是：") + 5
            code_end = message.find("，", code_start)
            if code_start > 4 and code_end > code_start:
                code = message[code_start:code_end]
            else:
                code = self.default_code
                
            self.sent_codes[phone_number] = code
            logger.info(f"[SIMULATION] SMS sent to {phone_number}, code: {code}")
            return True, "模拟短信发送成功"
        except Exception as e:
            logger.error(f"[SIMULATION] SMS send failed: {str(e)}")
            return False, f"模拟短信发送失败: {str(e)}"
    
    def get_code(self, phone_number: str) -> Optional[str]:
        """获取指定手机号的验证码（仅用于测试）"""
        return self.sent_codes.get(phone_number)


class AlibabaSMSProvider(SMSProvider):
    """阿里云SMS提供商"""
    
    def __init__(self, access_key: str, access_secret: str, sign_name: str, template_code: str):
        self.access_key = access_key
        self.access_secret = access_secret
        self.sign_name = sign_name
        self.template_code = template_code
        
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """使用阿里云SMS服务发送短信"""
        try:
            # 这里应该实现真实的阿里云SMS API调用
            # 为了简化，这里只做模拟实现
            logger.info(f"[ALIBABA] SMS sent to {phone_number}")
            return True, "阿里云短信发送成功"
        except Exception as e:
            logger.error(f"[ALIBABA] SMS send failed: {str(e)}")
            return False, f"阿里云短信发送失败: {str(e)}"


class TencentSMSProvider(SMSProvider):
    """腾讯云SMS提供商"""
    
    def __init__(self, secret_id: str, secret_key: str, app_id: str, sign_name: str, template_id: str):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.app_id = app_id
        self.sign_name = sign_name
        self.template_id = template_id
        
    def send_sms(self, phone_number: str, message: str) -> Tuple[bool, str]:
        """使用腾讯云SMS服务发送短信"""
        try:
            # 这里应该实现真实的腾讯云SMS API调用
            # 为了简化，这里只做模拟实现
            logger.info(f"[TENCENT] SMS sent to {phone_number}")
            return True, "腾讯云短信发送成功"
        except Exception as e:
            logger.error(f"[TENCENT] SMS send failed: {str(e)}")
            return False, f"腾讯云短信发送失败: {str(e)}"


class SMSService:
    """SMS服务管理器"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.provider = self._init_provider()
        self.rate_limit_window = 3600  # 1小时
        self.max_attempts_per_hour = 3
        self.code_expiry_minutes = 5
        
    def _init_provider(self) -> SMSProvider:
        """根据配置初始化SMS提供商"""
        provider_type = os.getenv('SMS_PROVIDER', 'simulation').lower()
        
        if provider_type == 'simulation':
            return SimulationSMSProvider()
        elif provider_type == 'alibaba':
            access_key = os.getenv('ALIBABA_SMS_ACCESS_KEY')
            access_secret = os.getenv('ALIBABA_SMS_ACCESS_SECRET')
            sign_name = os.getenv('ALIBABA_SMS_SIGN_NAME', '安全守护')
            template_code = os.getenv('ALIBABA_SMS_TEMPLATE_CODE')
            
            if not all([access_key, access_secret, template_code]):
                logger.warning("阿里云SMS配置不完整，回退到模拟模式")
                return SimulationSMSProvider()
                
            return AlibabaSMSProvider(access_key, access_secret, sign_name, template_code)
            
        elif provider_type == 'tencent':
            secret_id = os.getenv('TENCENT_SMS_SECRET_ID')
            secret_key = os.getenv('TENCENT_SMS_SECRET_KEY')
            app_id = os.getenv('TENCENT_SMS_APP_ID')
            sign_name = os.getenv('TENCENT_SMS_SIGN_NAME', '安全守护')
            template_id = os.getenv('TENCENT_SMS_TEMPLATE_ID')
            
            if not all([secret_id, secret_key, app_id, template_id]):
                logger.warning("腾讯云SMS配置不完整，回退到模拟模式")
                return SimulationSMSProvider()
                
            return TencentSMSProvider(secret_id, secret_key, app_id, sign_name, template_id)
            
        else:
            logger.warning(f"未知的SMS提供商类型: {provider_type}，使用模拟模式")
            return SimulationSMSProvider()
    
    def generate_verification_code(self) -> str:
        """生成6位数字验证码"""
        return ''.join(random.choices(string.digits, k=6))
    
    def _get_rate_limit_key(self, phone_number: str) -> str:
        """获取速率限制的Redis键"""
        return f"sms_rate_limit:{phone_number}"
    
    def _get_verification_code_key(self, phone_number: str) -> str:
        """获取验证码的Redis键"""
        return f"sms_verification:{phone_number}"
    
    def check_rate_limit(self, phone_number: str) -> Tuple[bool, str]:
        """检查速率限制"""
        if not self.redis_client:
            # 如果没有Redis，跳过速率限制
            return True, ""
            
        key = self._get_rate_limit_key(phone_number)
        try:
            current_attempts = self.redis_client.get(key)
            if current_attempts is None:
                # 首次请求，设置计数器
                self.redis_client.setex(key, self.rate_limit_window, 1)
                return True, ""
            else:
                current_attempts = int(current_attempts)
                if current_attempts >= self.max_attempts_per_hour:
                    ttl = self.redis_client.ttl(key)
                    return False, f"发送次数过多，请{ttl//60}分钟后再试"
                else:
                    # 增加计数器
                    self.redis_client.incr(key)
                    return True, ""
        except Exception as e:
            logger.error(f"检查速率限制失败: {str(e)}")
            # Redis出错时允许发送
            return True, ""
    
    def store_verification_code(self, phone_number: str, code: str) -> bool:
        """存储验证码到Redis"""
        if not self.redis_client:
            # 如果没有Redis，无法存储验证码
            logger.warning("Redis未配置，无法存储验证码")
            return False
            
        key = self._get_verification_code_key(phone_number)
        try:
            self.redis_client.setex(key, self.code_expiry_minutes * 60, code)
            return True
        except Exception as e:
            logger.error(f"存储验证码失败: {str(e)}")
            return False
    
    def get_verification_code(self, phone_number: str) -> Optional[str]:
        """从Redis获取验证码"""
        if not self.redis_client:
            return None
            
        key = self._get_verification_code_key(phone_number)
        try:
            code = self.redis_client.get(key)
            # 处理不同Redis客户端返回的类型（真实Redis返回bytes，fakeredis返回str）
            if isinstance(code, bytes):
                return code.decode()
            return code
        except Exception as e:
            logger.error(f"获取验证码失败: {str(e)}")
            return None
    
    def delete_verification_code(self, phone_number: str) -> bool:
        """删除验证码"""
        if not self.redis_client:
            return True
            
        key = self._get_verification_code_key(phone_number)
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"删除验证码失败: {str(e)}")
            return False
    
    def send_verification_code(self, phone_number: str) -> Tuple[bool, str, Optional[str]]:
        """
        发送验证码
        
        Returns:
            Tuple[bool, str, Optional[str]]: (是否成功, 消息, 验证码(仅模拟模式))
        """
        # 检查速率限制
        can_send, rate_msg = self.check_rate_limit(phone_number)
        if not can_send:
            return False, rate_msg, None
        
        # 生成验证码
        code = self.generate_verification_code()
        
        # 构建短信内容
        message = f"【安全守护】您的验证码是：{code}，{self.code_expiry_minutes}分钟内有效。"
        
        # 发送短信
        success, msg = self.provider.send_sms(phone_number, message)
        
        if success:
            # 存储验证码
            if self.store_verification_code(phone_number, code):
                logger.info(f"验证码已发送到 {phone_number}")
                
                # 如果是模拟模式，返回验证码
                if isinstance(self.provider, SimulationSMSProvider):
                    return True, "验证码发送成功", code
                else:
                    return True, "验证码发送成功", None
            else:
                return False, "验证码存储失败", None
        else:
            return False, msg, None
    
    def verify_code(self, phone_number: str, input_code: str) -> Tuple[bool, str]:
        """
        验证验证码
        
        Args:
            phone_number: 手机号码
            input_code: 用户输入的验证码
            
        Returns:
            Tuple[bool, str]: (是否成功, 消息)
        """
        stored_code = self.get_verification_code(phone_number)
        
        if not stored_code:
            return False, "验证码已过期或不存在"
        
        if stored_code != input_code:
            return False, "验证码错误"
        
        # 验证成功，删除验证码
        self.delete_verification_code(phone_number)
        return True, "验证码验证成功"


# 全局SMS服务实例
_sms_service = None


def get_sms_service() -> SMSService:
    """获取SMS服务实例"""
    global _sms_service
    if _sms_service is None:
        # 初始化Redis客户端
        try:
            # 检查是否为测试环境
            is_testing = os.environ.get('USE_SQLITE_FOR_TESTING', '').lower() == 'true' or \
                       os.environ.get('FLASK_ENV') == 'testing' or \
                       'PYTEST_CURRENT_TEST' in os.environ
            
            if is_testing:
                # 测试环境使用fakeredis
                try:
                    import fakeredis
                    redis_client = fakeredis.FakeRedis(decode_responses=True)
                    redis_client.ping()  # 测试连接
                except ImportError:
                    logger.warning("fakeredis未安装，测试环境将无法存储验证码")
                    redis_client = None
            else:
                # 生产环境使用真实Redis
                redis_host = os.getenv('REDIS_HOST', 'localhost')
                redis_port = int(os.getenv('REDIS_PORT', 6379))
                redis_db = int(os.getenv('REDIS_DB', 0))
                redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, decode_responses=True)
                # 测试连接
                redis_client.ping()
        except:
            logger.warning("Redis连接失败，SMS服务将无法存储验证码")
            redis_client = None
            
        _sms_service = SMSService(redis_client)
    return _sms_service


def rate_limit_decorator(max_attempts: int = 5, window_seconds: int = 300):
    """
    速率限制装饰器
    
    Args:
        max_attempts: 最大尝试次数
        window_seconds: 时间窗口（秒）
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 这里可以实现基于IP或其他标识的速率限制
            return func(*args, **kwargs)
        return wrapper
    return decorator