import os
import logging
import sys
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 检查环境变量文件
ENV_TYPE = os.environ.get('ENV_TYPE','prod')

ENV_TYPE = ENV_TYPE.strip().lower()

if ENV_TYPE not in ['prod','function', 'unit']:
    logger.error(f"ENV_TYPE 必须是 'prod'、'function' 或 'unit'，当前值: {ENV_TYPE}")
    sys.exit(1)

# 加载环境变量文件
if ENV_TYPE == 'prod':
    load_dotenv(f'.env')
else:
    load_dotenv(f'.env.{ENV_TYPE}', override=True)

db_address = os.environ.get('MYSQL_ADDRESS')
username = os.environ.get('MYSQL_USERNAME')
password = os.environ.get('MYSQL_PASSWORD')
db_name = os.environ.get('MYSQL_DATABASE')
db_connection_template = os.environ.get('DB_CONNECTION_TEMPLATE')  # 直接从环境变量获取完整的数据库URI
if not db_connection_template:
    logger.error("DB_CONNECTION_TEMPLATE 未设置")
    sys.exit(1)
db_info = {
    "db_address": db_address,
    "username": username,
    "password": password,
    "db_name": db_name
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
DB_RETRY_COUNT = int(os.environ.get('DB_RETRY_COUNT', '3'))
DB_RETRY_DELAY = float(os.environ.get('DB_RETRY_DELAY', '1.0'))
DEBUG = os.environ.get('DEBUG', 'false').lower() == 'true'

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 0))

# SMS_PROVIDER
SMS_PROVIDER = os.environ.get('SMS_PROVIDER', 'aliyun')

## ALIBABA_SMS
ALIBABA_SMS_ACCESS_KEY = os.environ.get('ALIBABA_SMS_ACCESS_KEY')
ALIBABA_SMS_ACCESS_SECRET = os.environ.get('ALIBABA_SMS_ACCESS_SECRET')
ALIBABA_SMS_SIGN_NAME = os.environ.get('ALIBABA_SMS_SIGN_NAME', '安全守护')
ALIBABA_SMS_TEMPLATE_CODE = os.environ.get('ALIBABA_SMS_TEMPLATE_CODE')

## TENCENT_SMS
TENCENT_SMS_SECRET_ID = os.environ.get('TENCENT_SMS_SECRET_ID')
TENCENT_SMS_SECRET_KEY = os.environ.get('TENCENT_SMS_SECRET_KEY')
TENCENT_SMS_APP_ID = os.environ.get('TENCENT_SMS_APP_ID')
TENCENT_SMS_SIGN_NAME = os.environ.get('TENCENT_SMS_SIGN_NAME', '安全守护')
TENCENT_SMS_TEMPLATE_ID = os.environ.get('TENCENT_SMS_TEMPLATE_ID')

# 集成测试配置
DOCKER_STARTUP_TIMEOUT=180