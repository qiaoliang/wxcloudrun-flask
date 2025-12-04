import os
from config_manager import load_environment_config, get_database_config

# 加载环境配置
load_environment_config()

# 获取数据库配置
db_config = get_database_config()
DEBUG = db_config.get('DEBUG', False)

# 根据环境配置设置数据库连接
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'root')
db_address = os.environ.get("MYSQL_ADDRESS", '127.0.0.1:3306')

# 微信小程序配置
WX_APPID = os.environ.get("WX_APPID", '')
WX_SECRET = os.environ.get("WX_SECRET", '')
