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
    max_retries = 120
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

def create_tables():
    """直接创建数据库表"""
    logger.info("开始创建数据库表...")
    try:
        import pymysql
        import sys
        
        # 添加项目路径到sys.path
        sys.path.insert(0, '/app')
        
        # 直接使用pymysql创建表
        logger.info("连接数据库...")
        connection = pymysql.connect(
            host=MYSQL_ADDRESS.split(':')[0],
            port=int(MYSQL_ADDRESS.split(':')[1]),
            user=MYSQL_USERNAME,
            password=MYSQL_PASSWORD,
            database=DATABASE_NAME,
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 删除所有旧表
        logger.info("删除所有旧表...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DROP TABLE IF EXISTS sms_verification_codes")
        cursor.execute("DROP TABLE IF EXISTS phone_auth")
        cursor.execute("DROP TABLE IF EXISTS rule_supervisions")
        cursor.execute("DROP TABLE IF EXISTS checkin_records")
        cursor.execute("DROP TABLE IF EXISTS checkin_rules")
        cursor.execute("DROP TABLE IF EXISTS users")
        cursor.execute("DROP TABLE IF EXISTS Counters")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        # 创建Counters表
        logger.info("创建Counters表...")
        cursor.execute("""
            CREATE TABLE Counters (
                id INT PRIMARY KEY,
                count INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建users表
        logger.info("创建users表...")
        cursor.execute("""
            CREATE TABLE users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                wechat_openid VARCHAR(128) UNIQUE,
                phone_number VARCHAR(500) UNIQUE,
                nickname VARCHAR(100),
                avatar_url VARCHAR(500),
                name VARCHAR(100),
                work_id VARCHAR(50),
                is_solo_user BOOLEAN DEFAULT TRUE,
                is_supervisor BOOLEAN DEFAULT FALSE,
                is_community_worker BOOLEAN DEFAULT FALSE,
                role INT DEFAULT 1,
                status INT DEFAULT 1,
                verification_status INT DEFAULT 0,
                verification_materials TEXT,
                community_id INT,
                auth_type ENUM('wechat', 'phone', 'both') DEFAULT 'wechat' NOT NULL,
                linked_accounts TEXT,
                refresh_token VARCHAR(255),
                refresh_token_expire DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_openid (wechat_openid),
                INDEX idx_phone (phone_number),
                INDEX idx_role (role),
                INDEX idx_status (status),
                INDEX idx_verification_status (verification_status),
                INDEX idx_users_auth_type (auth_type),
                INDEX idx_users_refresh_token (refresh_token)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建checkin_rules表
        logger.info("创建checkin_rules表...")
        cursor.execute("""
            CREATE TABLE checkin_rules (
                rule_id INT AUTO_INCREMENT PRIMARY KEY,
                solo_user_id INT NOT NULL,
                rule_name VARCHAR(100) NOT NULL,
                icon_url VARCHAR(500),
                frequency_type INT NOT NULL DEFAULT 0,
                time_slot_type INT NOT NULL DEFAULT 4,
                custom_time TIME,
                week_days INT DEFAULT 127,
                status INT DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (solo_user_id) REFERENCES users(user_id),
                INDEX idx_solo_user_rules (solo_user_id),
                INDEX idx_frequency_type (frequency_type),
                INDEX idx_time_slot_type (time_slot_type),
                INDEX idx_rule_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建checkin_records表
        logger.info("创建checkin_records表...")
        cursor.execute("""
            CREATE TABLE checkin_records (
                record_id INT AUTO_INCREMENT PRIMARY KEY,
                rule_id INT NOT NULL,
                solo_user_id INT NOT NULL,
                checkin_time DATETIME,
                status INT DEFAULT 0,
                planned_time DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (rule_id) REFERENCES checkin_rules(rule_id),
                FOREIGN KEY (solo_user_id) REFERENCES users(user_id),
                INDEX idx_rule_records (rule_id),
                INDEX idx_solo_user_records (solo_user_id),
                INDEX idx_planned_time (planned_time),
                INDEX idx_checkin_time (checkin_time),
                INDEX idx_record_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建rule_supervisions表
        logger.info("创建rule_supervisions表...")
        cursor.execute("""
            CREATE TABLE rule_supervisions (
                rule_supervision_id INT AUTO_INCREMENT PRIMARY KEY,
                rule_id INT NOT NULL,
                solo_user_id INT NOT NULL,
                supervisor_user_id INT NOT NULL,
                status INT DEFAULT 0,
                invitation_message TEXT,
                invited_by_user_id INT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                responded_at DATETIME,
                FOREIGN KEY (rule_id) REFERENCES checkin_rules(rule_id),
                FOREIGN KEY (solo_user_id) REFERENCES users(user_id),
                FOREIGN KEY (supervisor_user_id) REFERENCES users(user_id),
                FOREIGN KEY (invited_by_user_id) REFERENCES users(user_id),
                INDEX idx_rule_supervision (rule_id, supervisor_user_id),
                INDEX idx_solo_supervisions (solo_user_id, status),
                INDEX idx_supervisor_invitations (supervisor_user_id, status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建phone_auth表
        logger.info("创建phone_auth表...")
        cursor.execute("""
            CREATE TABLE phone_auth (
                phone_auth_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                phone_number VARCHAR(500) UNIQUE NOT NULL,
                password_hash VARCHAR(255),
                auth_methods ENUM('password', 'sms', 'both') DEFAULT 'sms' NOT NULL,
                is_verified BOOLEAN DEFAULT FALSE NOT NULL,
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                failed_attempts INT DEFAULT 0 NOT NULL,
                locked_until DATETIME,
                last_login_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                INDEX idx_phone_number (phone_number),
                INDEX idx_user_id (user_id),
                INDEX idx_is_verified (is_verified)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 创建sms_verification_codes表（Redis不可用时的备用存储）
        logger.info("创建sms_verification_codes表...")
        cursor.execute("""
            CREATE TABLE sms_verification_codes (
                code_id INT AUTO_INCREMENT PRIMARY KEY,
                phone_number VARCHAR(500) NOT NULL,
                code VARCHAR(10) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                expires_at DATETIME NOT NULL,
                used BOOLEAN DEFAULT FALSE,
                INDEX idx_phone_code (phone_number, code),
                INDEX idx_expires_at (expires_at),
                INDEX idx_phone_number (phone_number)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        # 插入初始数据
        logger.info("插入初始数据...")
        cursor.execute("""
            INSERT INTO Counters (id, count) VALUES (1, 0)
        """)
        
        connection.commit()
        
        # 检查表是否创建成功
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        logger.info(f"创建的表: {[table[0] for table in tables]}")
        
        cursor.close()
        connection.close()
        
        logger.info("数据库表创建成功")
        return True
        
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False

def create_tables_directly():
    """直接创建数据库表"""
    try:
        from flask import Flask
        from flask_sqlalchemy import SQLAlchemy
        import pymysql
        
        logger.info("创建Flask应用...")
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{MYSQL_USERNAME}:{MYSQL_PASSWORD}@{MYSQL_ADDRESS}/{DATABASE_NAME}?charset=utf8mb4'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        logger.info("初始化SQLAlchemy...")
        db = SQLAlchemy(app)
        
        logger.info("导入模型...")
        from wxcloudrun import model
        
        logger.info("创建数据库表...")
        with app.app_context():
            # 先检查表是否存在
            inspector = db.inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"已存在的表: {existing_tables}")
            
            # 创建所有表
            db.create_all()
            
            # 再次检查表是否创建成功
            inspector = db.inspect(db.engine)
            new_tables = inspector.get_table_names()
            logger.info(f"创建后的表: {new_tables}")
            
            if len(new_tables) > len(existing_tables):
                logger.info("数据库表创建成功")
            else:
                logger.warning("警告：没有创建新表")
        return True
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")
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
    
    # 3. 创建表
    if not create_tables():
        sys.exit(1)
    
    logger.info("数据库初始化完成")

if __name__ == '__main__':
    main()