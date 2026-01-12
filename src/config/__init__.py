"""
配置模块
提供统一的配置管理接口
"""
from .domain import (
    AppConfig,
    DatabaseConfig,
    WeChatConfig,
    RedisConfig,
    EnvironmentType
)
from .loader import load_config
from .utils import EnvironmentHelper
from .port import get_port, get_env_type_from_port

__all__ = [
    'AppConfig',
    'DatabaseConfig',
    'WeChatConfig',
    'RedisConfig',
    'EnvironmentType',
    'load_config',
    'EnvironmentHelper',
    'get_port',
    'get_env_type_from_port'
]

# 全局配置实例
_app_config: AppConfig = None


def init_config(env_type: str = None) -> AppConfig:
    """
    初始化应用配置

    Args:
        env_type: 环境类型，如果不指定则从环境变量读取

    Returns:
        应用配置对象
    """
    global _app_config
    _app_config = load_config(env_type)
    return _app_config


def get_config() -> AppConfig:
    """
    获取应用配置

    Returns:
        应用配置对象

    Raises:
        RuntimeError: 如果配置未初始化
    """
    if _app_config is None:
        raise RuntimeError("配置未初始化，请先调用 init_config()")
    return _app_config


def should_use_mock_wechat() -> bool:
    """
    判断是否应该使用Mock微信API
    unit, func, function, uat 环境使用Mock，prod使用真实API
    """
    return EnvironmentHelper.is_unit() or EnvironmentHelper.is_function() or EnvironmentHelper.is_uat()


def should_use_real_sms() -> bool:
    """
    判断是否应该使用真实短信服务
    根据 SMS_PROVIDER 环境变量决定：
    - 'real'（不区分大小写）: 使用真实短信服务
    - 'mock'（不区分大小写）: 使用模拟短信服务
    - 其他或未设置：根据环境判断（prod和uat使用真实，其他使用模拟）
    """
    import os

    sms_provider = os.getenv('SMS_PROVIDER', '').lower()

    # 优先使用明确的配置（不区分大小写）
    if sms_provider == 'real':
        return True
    elif sms_provider == 'mock':
        return False

    # 如果没有明确配置，根据环境判断
    return EnvironmentHelper.is_uat() or EnvironmentHelper.is_production()


def get_database_config() -> dict:
    """
    获取数据库配置（兼容旧接口）

    Returns:
        数据库配置字典
    """
    config = get_config()
    return {
        'SQLALCHEMY_DATABASE_URI': config.database.uri,
        'TESTING': config.database.testing,
        'DEBUG': config.database.debug,
        'DATABASE_TYPE': config.database.database_type,
        'DATABASE_PATH': config.database.database_path
    }