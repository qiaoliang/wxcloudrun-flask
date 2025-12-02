#!/usr/bin/env python3
"""
数据库初始化脚本
用于在Docker容器启动时初始化数据库和运行迁移
"""

import os
import time
import sys
import pymysql
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
pymysql.install_as_MySQLdb()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置信息
MYSQL_USERNAME = os.environ.get('MYSQL_USERNAME', 'root')
MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', 'rootpassword')
MYSQL_ADDRESS = os.environ.get('MYSQL_ADDRESS', 'mysql-db:3306')
DATABASE_NAME = 'flask_demo'

def wait_for_mysql():
    """等待MySQL服务启动"""
    max_retries = 60
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # 尝试连接到MySQL服务器（不指定数据库）
            engine = create_engine(f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_ADDRESS}/')
            with engine.connect() as connection:
                logger.info("MySQL服务已启动")
                return True
        except OperationalError as e:
            retry_count += 1
            logger.warning(f"等待MySQL服务启动... ({retry_count}/{max_retries})")
            time.sleep(1)
    
    logger.error("MySQL服务启动超时")
    return False

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        engine = create_engine(f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_ADDRESS}/')
        with engine.connect() as connection:
            # 检查数据库是否存在
            result = connection.execute(text(f"SHOW DATABASES LIKE '{DATABASE_NAME}'"))
            if result.fetchone() is None:
                logger.info(f"创建数据库: {DATABASE_NAME}")
                connection.execute(text(f"CREATE DATABASE {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                connection.commit()
                logger.info("数据库创建成功")
            else:
                logger.info(f"数据库 {DATABASE_NAME} 已存在")
        return True
    except Exception as e:
        logger.error(f"创建数据库失败: {str(e)}")
        return False

def run_migrations():
    """运行数据库迁移"""
    logger.info("开始运行数据库迁移...")
    try:
        from flask import Flask
        import config
        
        logger.info("创建Flask应用...")
        # 创建临时Flask应用
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_ADDRESS}/{DATABASE_NAME}?charset=utf8mb4'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        logger.info("初始化SQLAlchemy...")
        from flask_sqlalchemy import SQLAlchemy
        
        db = SQLAlchemy(app)
        
        logger.info("导入模型...")
        # 导入模型以确保迁移能找到它们
        with app.app_context():
            from wxcloudrun import model
            logger.info("模型导入成功")
            
            logger.info("开始创建数据库表...")
            # 直接创建所有表
            db.create_all()
            logger.info("数据库表创建完成")
        return True
    except Exception as e:
        logger.error(f"运行迁移失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def main():
    """主函数"""
    logger.info("开始数据库初始化...")
    
    # 1. 等待MySQL服务启动
    if not wait_for_mysql():
        sys.exit(1)
    
    # 2. 创建数据库
    if not create_database_if_not_exists():
        sys.exit(1)
    
    # 3. 运行迁移
    if not run_migrations():
        sys.exit(1)
    
    logger.info("数据库初始化完成")

if __name__ == '__main__':
    main()