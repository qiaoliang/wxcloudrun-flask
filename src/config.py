import os
from config_manager import load_environment_config, get_database_config

# 加载环境配置
load_environment_config()

# 获取数据库配置
db_config = get_database_config()
DEBUG = db_config.get('DEBUG', False)

# 微信小程序配置
WX_APPID = os.environ.get("WX_APPID", '')
WX_SECRET = os.environ.get("WX_SECRET", '')
