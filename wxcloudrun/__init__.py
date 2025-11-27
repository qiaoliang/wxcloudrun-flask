from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
import config
import os

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 初始化web应用
app = Flask(__name__, instance_relative_config=True)
app.config['DEBUG'] = config.DEBUG

# 检查是否为测试环境，如果是则使用SQLite，否则使用MySQL
if os.environ.get('FLASK_ENV') == 'testing' or os.environ.get('PYTEST_CURRENT_TEST'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # 测试时使用SQLite内存数据库
    app.config['TESTING'] = True
else:
    # 设定数据库链接
    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://{}:{}@{}/flask_demo'.format(config.username, config.password,
                                                                                 config.db_address)

# 初始化DB操作对象
db = SQLAlchemy(app)

# 加载控制器
from wxcloudrun import views

# 加载配置
app.config.from_object('config')

# 创建数据库表
from wxcloudrun.model import Counters
with app.app_context():
    db.create_all()
