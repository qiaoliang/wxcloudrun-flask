import os

# ... 原有的配置代码 ...

# 增加一个配置类或逻辑来处理测试环境
class Config:
    # 假设这是你原有的基础配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # ...

    @staticmethod
    def init_app(app):
        pass

# 生产/开发环境配置
class DevelopmentConfig(Config):
    # 这里是你原有的 MySQL 配置
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://user:password@host:port/db_name'

# 【新增】测试环境配置
class TestingConfig(Config):
    TESTING = True
    # 关键点：使用内存数据库，而不是真实 MySQL
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置映射字典
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}