#!/usr/bin/env python3
"""
手机认证功能数据库迁移脚本
运行PhoneAuth表和相关索引的创建
"""

import os
import sys
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_migration():
    """运行数据库迁移"""
    try:
        # 导入必要的模块
        from wxcloudrun import app, db
        from wxcloudrun.model import User, PhoneAuth
        
        logger.info("开始执行手机认证功能数据库迁移...")
        
        with app.app_context():
            # 检查表是否已存在
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()
            
            logger.info(f"当前数据库中的表: {existing_tables}")
            
            # 创建PhoneAuth表
            if 'phone_auth' not in existing_tables:
                logger.info("创建PhoneAuth表...")
                PhoneAuth.__table__.create(db.engine, checkfirst=True)
                logger.info("PhoneAuth表创建成功")
            else:
                logger.info("PhoneAuth表已存在，跳过创建")
            
            # 检查并添加users表的新字段
            if 'users' in existing_tables:
                logger.info("检查users表结构...")
                columns = [column['name'] for column in inspector.get_columns('users')]
                logger.info(f"users表当前字段: {columns}")
                
                # 添加auth_type字段
                if 'auth_type' not in columns:
                    logger.info("添加auth_type字段到users表...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE users 
                            ADD COLUMN auth_type ENUM('wechat', 'phone', 'both') 
                            NOT NULL DEFAULT 'wechat' 
                            COMMENT '认证类型：wechat/phone/both'
                        """))
                        conn.commit()
                    logger.info("auth_type字段添加成功")
                else:
                    logger.info("auth_type字段已存在")
                
                # 添加linked_accounts字段
                if 'linked_accounts' not in columns:
                    logger.info("添加linked_accounts字段到users表...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            ALTER TABLE users 
                            ADD COLUMN linked_accounts TEXT 
                            DEFAULT NULL 
                            COMMENT '关联账户信息（JSON格式）'
                        """))
                        conn.commit()
                    logger.info("linked_accounts字段添加成功")
                else:
                    logger.info("linked_accounts字段已存在")
                
                # 添加索引
                logger.info("检查并添加索引...")
                indexes = inspector.get_indexes('users')
                index_names = [idx['name'] for idx in indexes]
                
                if 'idx_users_auth_type' not in index_names:
                    logger.info("添加auth_type索引...")
                    with db.engine.connect() as conn:
                        conn.execute(db.text("""
                            CREATE INDEX idx_users_auth_type ON users (auth_type)
                        """))
                        conn.commit()
                    logger.info("auth_type索引添加成功")
                else:
                    logger.info("auth_type索引已存在")
            
            # 创建用户认证信息视图
            logger.info("创建用户认证信息视图...")
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("""
                        CREATE OR REPLACE VIEW user_auth_view AS
                        SELECT 
                            u.user_id,
                            u.wechat_openid,
                            u.phone_number,
                            u.nickname,
                            u.auth_type,
                            u.is_solo_user,
                            u.is_supervisor,
                            u.is_community_worker,
                            u.status,
                            pa.phone_auth_id,
                            pa.auth_methods,
                            pa.is_verified as phone_verified,
                            pa.is_active as phone_active,
                            pa.last_login_at,
                            u.created_at,
                            u.updated_at
                        FROM users u
                        LEFT JOIN phone_auth pa ON u.user_id = pa.user_id
                    """))
                    conn.commit()
                logger.info("用户认证信息视图创建成功")
            except Exception as e:
                logger.warning(f"创建视图失败（可能已存在）: {str(e)}")
            
            # 验证表结构
            logger.info("验证表结构...")
            inspector = inspect(db.engine)
            updated_tables = inspector.get_table_names()
            
            if 'phone_auth' in updated_tables:
                phone_auth_columns = [col['name'] for col in inspector.get_columns('phone_auth')]
                logger.info(f"PhoneAuth表字段: {phone_auth_columns}")
                
                # 检查必要的字段
                required_columns = [
                    'phone_auth_id', 'user_id', 'phone_number', 'password_hash',
                    'auth_methods', 'is_verified', 'is_active', 'failed_attempts',
                    'locked_until', 'last_login_at', 'created_at', 'updated_at'
                ]
                
                missing_columns = [col for col in required_columns if col not in phone_auth_columns]
                if missing_columns:
                    logger.error(f"PhoneAuth表缺少字段: {missing_columns}")
                    return False
                else:
                    logger.info("PhoneAuth表结构验证通过")
            else:
                logger.error("PhoneAuth表创建失败")
                return False
            
            # 检查users表更新
            if 'users' in updated_tables:
                users_columns = [col['name'] for col in inspector.get_columns('users')]
                if 'auth_type' in users_columns and 'linked_accounts' in users_columns:
                    logger.info("users表更新验证通过")
                else:
                    logger.error("users表更新失败")
                    return False
            
            logger.info("手机认证功能数据库迁移完成！")
            return True
            
    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def rollback_migration():
    """回滚数据库迁移"""
    try:
        from wxcloudrun import app, db
        
        logger.info("开始回滚手机认证功能数据库迁移...")
        
        with app.app_context():
            # 删除视图
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("DROP VIEW IF EXISTS user_auth_view"))
                    conn.commit()
                logger.info("用户认证信息视图已删除")
            except Exception as e:
                logger.warning(f"删除视图失败: {str(e)}")
            
            # 删除PhoneAuth表
            try:
                with db.engine.connect() as conn:
                    conn.execute(db.text("DROP TABLE IF EXISTS phone_auth"))
                    conn.commit()
                logger.info("PhoneAuth表已删除")
            except Exception as e:
                logger.warning(f"删除PhoneAuth表失败: {str(e)}")
            
            # 删除users表的新字段（谨慎操作）
            try:
                with db.engine.connect() as conn:
                    # 删除索引
                    conn.execute(db.text("DROP INDEX IF EXISTS idx_users_auth_type ON users"))
                    
                    # 删除字段
                    conn.execute(db.text("ALTER TABLE users DROP COLUMN IF EXISTS auth_type"))
                    conn.execute(db.text("ALTER TABLE users DROP COLUMN IF EXISTS linked_accounts"))
                    conn.commit()
                logger.info("users表字段已删除")
            except Exception as e:
                logger.warning(f"删除users表字段失败: {str(e)}")
            
            logger.info("手机认证功能数据库迁移回滚完成！")
            return True
            
    except Exception as e:
        logger.error(f"数据库迁移回滚失败: {str(e)}")
        return False


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python run_phone_auth_migration.py [migrate|rollback]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == 'migrate':
        success = run_migration()
        sys.exit(0 if success else 1)
    elif command == 'rollback':
        success = rollback_migration()
        sys.exit(0 if success else 1)
    else:
        print(f"未知命令: {command}")
        print("用法: python run_phone_auth_migration.py [migrate|rollback]")
        sys.exit(1)


if __name__ == '__main__':
    main()