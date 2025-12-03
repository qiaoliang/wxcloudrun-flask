import os
import logging
import sys
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查环境变量文件
ENV_TYPE = os.environ.get('ENV_TYPE','unit')

if not ENV_TYPE:
    logger.warning("ENV_TYPE 未设置")
    sys.exit(1)
else:
    ENV_TYPE = ENV_TYPE.strip().lower()

# 加载环境变量文件
load_dotenv(f'.env.{ENV_TYPE}')

# 读取数据库配置
db_address = os.environ.get('DB_ADDRESS')
username = os.environ.get('DB_USERNAME')
password = os.environ.get('DB_PASSWORD')

db_connection_template = os.environ.get('DB_CONNECTION_TEMPLATE')  # 直接从环境变量获取完整的数据库URI
if not db_connection_template:
    logger.error("DB_CONNECTION_TEMPLATE 未设置")
    sys.exit(1)

db_info = {
    "db_address": db_address,
    "username": username,
    "password": password
}
DB_CONNECTION_URI = db_connection_template.format(**db_info)


# 读取微信小程序配置
WX_APPID = os.environ.get('WX_APPID')
WX_SECRET = os.environ.get('WX_SECRET')

# 读取 JWT token 密钥
TOKEN_SECRET = os.environ.get('TOKEN_SECRET')

# 读取手机号码加密密钥
PHONE_ENCRYPTION_KEY = os.environ.get('PHONE_ENCRYPTION_KEY')

# 环境相关变量
AUTO_RUN_MIGRATIONS = os.environ.get('AUTO_RUN_MIGRATIONS', 'false').lower() == 'true'
AUTO_CREATE_TABLES = os.environ.get('AUTO_CREATE_TABLES', 'false').lower() == 'true'
DB_RETRY_COUNT = int(os.environ.get('DB_RETRY_COUNT', '3'))
DB_RETRY_DELAY = float(os.environ.get('DB_RETRY_DELAY', '1.0'))
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

## Flask环境设置为单元测试模式
IS_FLASK_ENV = os.environ.get("IS_FLASK_ENV")
