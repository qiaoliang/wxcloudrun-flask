"""
速率限制中间件
提供基于不同维度的速率限制功能
"""

import os
import time
import redis
import logging
import json
from typing import Dict, Optional, Tuple, Callable
from functools import wraps
from flask import request, g, jsonify
from datetime import datetime, timedelta

# 配置日志
logger = logging.getLogger(__name__)


class RateLimiter:
    """速率限制器"""

    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.default_window = 3600  # 默认1小时
        self.default_limit = 100    # 默认100次

    def _get_client_ip(self) -> str:
        """获取客户端IP地址"""
        # 优先从代理头获取真实IP
        if request.headers.get('X-Forwarded-For'):
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        elif request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        else:
            return request.remote_addr or 'unknown'

    def _get_key(self, key_type: str, identifier: str, window: int) -> str:
        """生成速率限制键"""
        return f"rate_limit:{key_type}:{identifier}:{window}"

    def is_allowed(self, key_type: str, identifier: str, limit: int, window: int) -> Tuple[bool, Dict]:
        """
        检查是否允许请求

        Args:
            key_type: 限制类型（ip, phone, user等）
            identifier: 标识符（IP地址、手机号、用户ID等）
            limit: 限制次数
            window: 时间窗口（秒）

        Returns:
            Tuple[bool, Dict]: (是否允许, 限制信息)
        """
        if not self.redis_client:
            # 如果没有Redis，允许所有请求
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': int(time.time() + window),
                'retry_after': None
            }

        key = self._get_key(key_type, identifier, window)

        try:
            # 获取当前计数
            current_count = self.redis_client.get(key)

            if current_count is None:
                # 首次请求
                pipe = self.redis_client.pipeline()
                pipe.setex(key, window, 1)
                pipe.execute()

                return True, {
                    'allowed': True,
                    'limit': limit,
                    'remaining': limit - 1,
                    'reset_time': int(time.time() + window),
                    'retry_after': None
                }
            else:
                current_count = int(current_count)

                if current_count >= limit:
                    # 超过限制
                    ttl = self.redis_client.ttl(key)
                    return False, {
                        'allowed': False,
                        'limit': limit,
                        'remaining': 0,
                        'reset_time': int(time.time() + ttl),
                        'retry_after': ttl
                    }
                else:
                    # 增加计数
                    pipe = self.redis_client.pipeline()
                    pipe.incr(key)
                    pipe.execute()

                    return True, {
                        'allowed': True,
                        'limit': limit,
                        'remaining': limit - current_count - 1,
                        'reset_time': int(time.time() + self.redis_client.ttl(key)),
                        'retry_after': None
                    }

        except Exception as e:
            logger.error(f"速率限制检查失败: {str(e)}")
            # Redis出错时允许请求
            return True, {
                'allowed': True,
                'limit': limit,
                'remaining': limit - 1,
                'reset_time': int(time.time() + window),
                'retry_after': None
            }

    def reset_limit(self, key_type: str, identifier: str, window: int) -> bool:
        """重置速率限制"""
        if not self.redis_client:
            return True

        key = self._get_key(key_type, identifier, window)
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"重置速率限制失败: {str(e)}")
            return False


class SMRateLimiter(RateLimiter):
    """短信专用速率限制器"""

    def __init__(self, redis_client: redis.Redis = None):
        super().__init__(redis_client)
        # 短信发送限制配置
        self.sms_limits = {
            'per_phone_per_hour': (3, 3600),    # 每个手机号每小时3次
            'per_ip_per_hour': (10, 3600),     # 每个IP每小时10次
            'per_phone_per_day': (10, 86400),  # 每个手机号每天10次
            'global_per_minute': (100, 60),    # 全局每分钟100次
        }

    def check_sms_limit(self, phone_number: str, ip_address: str = None) -> Tuple[bool, str, Dict]:
        """
        检查短信发送限制

        Args:
            phone_number: 手机号码
            ip_address: IP地址（可选）

        Returns:
            Tuple[bool, str, Dict]: (是否允许, 错误信息, 限制信息)
        """
        if ip_address is None:
            ip_address = self._get_client_ip()

        # 检查各种限制
        checks = [
            ('phone_hour', phone_number, *self.sms_limits['per_phone_per_hour']),
            ('phone_day', phone_number, *self.sms_limits['per_phone_per_day']),
            ('ip_hour', ip_address, *self.sms_limits['per_ip_per_hour']),
            ('global', 'global', *self.sms_limits['global_per_minute']),
        ]

        for key_type, identifier, limit, window in checks:
            allowed, info = self.is_allowed(key_type, identifier, limit, window)
            if not allowed:
                # 根据限制类型返回相应的错误信息
                if key_type == 'phone_hour':
                    error_msg = f"该手机号发送次数过多，请{info['retry_after']//60}分钟后再试"
                elif key_type == 'phone_day':
                    error_msg = f"该手机号今日发送次数已达上限，请明天再试"
                elif key_type == 'ip_hour':
                    error_msg = f"您的IP发送次数过多，请{info['retry_after']//60}分钟后再试"
                elif key_type == 'global':
                    error_msg = "系统繁忙，请稍后再试"
                else:
                    error_msg = f"发送频率过高，请{info['retry_after']}秒后再试"

                return False, error_msg, info

        return True, "", {
            'allowed': True,
            'limits': {
                'phone_per_hour': self.sms_limits['per_phone_per_hour'][0],
                'phone_per_day': self.sms_limits['per_phone_per_day'][0],
                'ip_per_hour': self.sms_limits['per_ip_per_hour'][0],
            }
        }


# 全局速率限制器实例
_rate_limiter = None
_sms_rate_limiter = None


def get_rate_limiter() -> RateLimiter:
    """获取速率限制器实例"""
    global _rate_limiter
    if _rate_limiter is None:
        # 初始化Redis客户端
        try:
            # 检查是否为测试环境
            if os.environ.get('ENV_TYPE').lower() != 'prod':
                # 测试环境使用fakeredis
                try:
                    import fakeredis
                    redis_client = fakeredis.FakeRedis(decode_responses=True)
                    redis_client.ping()  # 测试连接
                except ImportError:
                    logger.warning("fakeredis未安装，测试环境速率限制功能将不可用")
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
            logger.warning("Redis连接失败，速率限制功能将不可用")
            redis_client = None

        _rate_limiter = RateLimiter(redis_client)
    return _rate_limiter


def get_sms_rate_limiter() -> SMRateLimiter:
    """获取短信速率限制器实例"""
    global _sms_rate_limiter
    if _sms_rate_limiter is None:
        # 初始化Redis客户端
        try:
            # 检查是否为测试环境
            # 检查是否为测试环境
            if os.environ.get('ENV_TYPE').lower() != 'prod':
                # 测试环境使用fakeredis
                try:
                    import fakeredis
                    redis_client = fakeredis.FakeRedis(decode_responses=True)
                    redis_client.ping()  # 测试连接
                except ImportError:
                    logger.warning("fakeredis未安装，测试环境短信速率限制功能将不可用")
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
            logger.warning("Redis连接失败，短信速率限制功能将不可用")
            redis_client = None

        _sms_rate_limiter = SMRateLimiter(redis_client)
    return _sms_rate_limiter


def rate_limit(key_type: str, limit: int, window: int, identifier_func: Callable = None):
    """
    速率限制装饰器

    Args:
        key_type: 限制类型
        limit: 限制次数
        window: 时间窗口（秒）
        identifier_func: 标识符获取函数，默认使用客户端IP
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            rate_limiter = get_rate_limiter()

            # 获取标识符
            if identifier_func:
                identifier = identifier_func(request)
            else:
                identifier = rate_limiter._get_client_ip()

            # 检查限制
            allowed, info = rate_limiter.is_allowed(key_type, identifier, limit, window)

            if not allowed:
                # 返回429状态码
                response = jsonify({
                    'code': 0,
                    'data': {},
                    'msg': f"请求过于频繁，请{info['retry_after']}秒后再试"
                })
                response.status_code = 429
                # 添加速率限制头
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])
                response.headers['Retry-After'] = str(info['retry_after'])
                return response

            # 添加速率限制头到响应
            response = func(*args, **kwargs)
            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset_time'])

            return response
        return wrapper
    return decorator


def sms_rate_limit(phone_key: str = 'phone'):
    """
    短信速率限制装饰器

    Args:
        phone_key: 请求中手机号码的键名
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            sms_limiter = get_sms_rate_limiter()

            # 获取手机号码
            phone_number = None
            if request.is_json:
                phone_number = request.json.get(phone_key)
            else:
                phone_number = request.form.get(phone_key)

            if not phone_number:
                response = jsonify({
                    'code': 0,
                    'data': {},
                    'msg': '手机号码不能为空'
                })
                response.status_code = 400
                return response

            # 检查短信限制
            allowed, error_msg, info = sms_limiter.check_sms_limit(phone_number)

            if not allowed:
                response = jsonify({
                    'code': 0,
                    'data': {},
                    'msg': error_msg
                })
                response.status_code = 429
                # 添加速率限制头
                response.headers['X-RateLimit-Limit'] = str(info.get('limit', 0))
                response.headers['X-RateLimit-Remaining'] = str(info.get('remaining', 0))
                response.headers['X-RateLimit-Reset'] = str(info.get('reset_time', 0))
                response.headers['Retry-After'] = str(info.get('retry_after', 0))
                return response

            # 执行原函数
            response = func(*args, **kwargs)

            # 添加速率限制信息到响应头
            if hasattr(response, 'headers') and info.get('limits'):
                response.headers['X-SMS-Limits'] = json.dumps(info['limits'])

            return response
        return wrapper
    return decorator