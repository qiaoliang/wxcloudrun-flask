import os

# 是否开启debug模式
DEBUG = True

# 读取数据库环境变量
username = os.environ.get("MYSQL_USERNAME", 'root')
password = os.environ.get("MYSQL_PASSWORD", 'root')
db_address = os.environ.get("MYSQL_ADDRESS", '127.0.0.1:3306')

# 微信小程序配置
WX_APPID = os.environ.get("WX_APPID", '')
WX_SECRET = os.environ.get("WX_SECRET", '')

# JWT配置
TOKEN_SECRET = os.environ.get("TOKEN_SECRET", '42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f')
