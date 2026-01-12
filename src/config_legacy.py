"""
配置模块（向后兼容）
使用新的配置系统，同时保持旧接口的兼容性
"""
import os
import sys

# 添加当前目录到路径，避免循环导入
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.loader import load_config

# 初始化配置
app_config = load_config()

# Flask 配置（向后兼容）
DEBUG = app_config.debug

# Flask-SQLAlchemy配置
SQLALCHEMY_DATABASE_URI = app_config.database.uri
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'echo': os.getenv('SQL_DEBUG', 'False').lower() == 'true'
}

# 微信小程序配置
WX_APPID = app_config.wechat.appid
WX_SECRET = app_config.wechat.secret

# 端口配置
PORT = app_config.port

# Token 配置
TOKEN_SECRET = app_config.token_secret

# 手机号加密密钥
PHONE_ENCRYPTION_KEY = app_config.phone_encryption_key
