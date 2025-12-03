#!/usr/bin/env python3
"""
数据库初始化脚本
用于在Docker容器启动时初始化数据库和运行迁移
统一使用config.py中的配置，避免配置不一致问题
"""

import os
import time
import sys
import logging

# 因MySQLDB不支持Python3，使用pymysql扩展库代替MySQLDB库
import pymysql
pymysql.install_as_MySQLdb()

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

import config

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入统一配置
# 从配置中解析数据库连接信息
DB_CONNECTION_URI = config.DB_CONNECTION_URI
logger.info(f"📊 使用 DOT_ENV 配置中的数据库连接: {DB_CONNECTION_URI}")
MYSQL_USERNAME = config.username
MYSQL_PASSWORD = config.password
MYSQL_ADDRESS = config.db_address
DATABASE_NAME = config.db_name
logger.info(f"🔧 解析后的连接信息:")
logger.info(f"   - 用户名: {MYSQL_USERNAME}")
logger.info(f"   - 地址: {MYSQL_ADDRESS}")
logger.info(f"   - 数据库: {DATABASE_NAME}")


def wait_for_mysql():
    """等待MySQL服务启动"""
    try:
        import config
        max_retries = config.DB_RETRY_COUNT
        retry_delay = config.DB_RETRY_DELAY
        logger.info(f"🔄 使用config.py中的重试配置: 最大重试次数={max_retries}, 重试延迟={retry_delay}秒")
    except (ImportError, AttributeError) as e:
        logger.warning(f"⚠️  无法获取config.py中的重试配置，使用默认值: {e}")
        max_retries = 120
        retry_delay = 1.0

    retry_count = 0

    logger.info(f"🔄 等待MySQL服务启动...")
    logger.info(f"   连接信息: {MYSQL_USERNAME}@{MYSQL_ADDRESS}")

    while retry_count < max_retries:
        try:
            # 尝试连接到MySQL服务器（不指定数据库）
            connection_uri = DB_CONNECTION_URI
            engine = create_engine(connection_uri)
            with engine.connect() as connection:
                logger.info("✅ MySQL服务已启动")
                return True
        except OperationalError as e:
            retry_count += 1
            if retry_count % 10 == 0:  # 每10次才打印一次，避免日志过多
                logger.warning(f"⏳ 等待MySQL服务启动... ({retry_count}/{max_retries})")
            time.sleep(retry_delay)

    logger.error("❌ MySQL服务启动超时")
    return False

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    try:
        logger.info(f"🔍 检查数据库: {DATABASE_NAME}")

        # 连接到MySQL服务器（不指定数据库）
        connection_uri = DB_CONNECTION_URI
        engine = create_engine(connection_uri)
        with engine.connect() as connection:
            # 检查数据库是否存在
            result = connection.execute(text(f"SHOW DATABASES LIKE '{DATABASE_NAME}'"))
            if result.fetchone() is None:
                logger.info(f"➕ 创建数据库: {DATABASE_NAME}")
                connection.execute(text(f"CREATE DATABASE {DATABASE_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"))
                connection.commit()
                logger.info("✅ 数据库创建成功")
            else:
                logger.info(f"ℹ️  数据库 {DATABASE_NAME} 已存在")
        return True
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {str(e)}")
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
    """直接创建数据库表（使用统一配置）"""
    try:
        logger.info("使用统一配置创建Flask应用...")

        # 使用统一的配置导入Flask应用
        from wxcloudrun import app, db
        logger.info("✅ 成功导入Flask应用和数据库对象")

        logger.info("导入模型...")
        from wxcloudrun import model

        logger.info("在Flask应用上下文中创建数据库表...")
        with app.app_context():
            # 先检查表是否存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            logger.info(f"已存在的表: {existing_tables}")

            # 检查当前数据库配置
            try:
                import config
                current_db_uri = config.DB_CONNECTION_URI
                logger.info(f"从config.py获取当前数据库配置: {current_db_uri}")
            except (ImportError, AttributeError) as e:
                current_db_uri = app.config.get('DB_CONNECTION_URI', 'Not set')
                logger.info(f"从Flask应用配置获取当前数据库配置: {current_db_uri}")

            # 创建所有表
            db.create_all()

            # 再次检查表是否创建成功
            inspector = inspect(db.engine)
            new_tables = inspector.get_table_names()
            logger.info(f"创建后的表: {new_tables}")

            if len(new_tables) > len(existing_tables):
                logger.info("✅ 数据库表创建成功")
            else:
                logger.warning("⚠️  警告：没有创建新表（可能已经存在）")

        return True
    except Exception as e:
        logger.error(f"❌ 创建表失败: {str(e)}")
        import traceback
        logger.error(f"详细错误信息: {traceback.format_exc()}")
        return False


def main():
    """主函数"""
    logger.info("🚀 开始数据库初始化（使用统一配置）...")

    # 1. 等待MySQL服务启动
    if not wait_for_mysql():
        logger.error("❌ MySQL服务启动失败")
        sys.exit(1)

    # 2. 创建数据库
    if not create_database_if_not_exists():
        logger.error("❌ 数据库创建失败")
        sys.exit(1)

    # 3. 创建表（优先使用统一配置的方法）
    logger.info("🔧 使用统一配置创建数据库表...")
    if not create_tables_directly():
        logger.error("❌ 使用统一配置创建表失败")
        logger.info("🔄 尝试备用方法...")
        if not create_tables():
            logger.error("❌ 备用方法创建表也失败")
            sys.exit(1)

    logger.info("✅ 数据库初始化完成")

if __name__ == '__main__':
    main()