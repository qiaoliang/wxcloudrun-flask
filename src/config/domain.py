"""
配置领域模型
定义配置的数据结构和类型
"""
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class EnvironmentType(Enum):
    """环境类型枚举"""
    UNIT = 'unit'
    FUNCTION = 'function'
    UAT = 'uat'
    PROD = 'prod'


@dataclass
class DatabaseConfig:
    """数据库配置"""
    uri: str
    testing: bool
    debug: bool
    database_type: str
    database_path: Optional[str] = None


@dataclass
class WeChatConfig:
    """微信配置"""
    appid: str
    secret: str
    use_mock: bool


@dataclass
class RedisConfig:
    """Redis配置"""
    host: str
    port: int
    db: int
    password: Optional[str]
    use_fake: bool


@dataclass
class AppConfig:
    """应用配置"""
    environment: EnvironmentType
    database: DatabaseConfig
    wechat: WeChatConfig
    redis: RedisConfig
    port: int
    debug: bool
    token_secret: str
    phone_encryption_key: str