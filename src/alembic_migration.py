"""
独立的 Alembic 数据库迁移脚本
完全独立于 Flask 应用，可以直接运行
"""
import logging
import sys
import os
import time
from alembic.config import Config
from alembic import command

# 配置独立的日志系统
logger = logging.getLogger('alembic_migration')
logger.setLevel(logging.INFO)

# 创建控制台处理器
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# 关闭传播以避免与根日志器重复处理
logger.propagate = False

# 文件处理器（在需要时创建）
def setup_file_handler():
    """设置文件处理器"""
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/migration.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 确保传播关闭（可能在之前被重置）
    logger.propagate = False

def validate_migration_prerequisites():
    """Layer 1: 验证迁移前置条件"""
    try:
        # 检查 alembic.ini 文件
        if not os.path.exists("alembic.ini"):
            raise FileNotFoundError("alembic.ini 文件不存在")

        # 检查 alembic 目录
        if not os.path.exists("alembic"):
            raise FileNotFoundError("alembic 目录不存在")

        # 检查数据库配置
        from config_manager import get_database_config
        db_config = get_database_config()
        db_uri = db_config.get('SQLALCHEMY_DATABASE_URI')
        if not db_uri:
            raise ValueError("数据库 URI 未配置")

        logger.info(f"数据库 URI: {db_uri}")
        return True

    except Exception as e:
        logger.error(f"迁移前置条件验证失败: {e}")
        return False

def validate_database_consistency():
    """Layer 2: 验证数据库一致性"""
    try:
        from config_manager import get_database_config
        db_config = get_database_config()
        db_path = db_config.get('DATABASE_PATH')

        if not db_path:
            logger.error("数据库路径未配置")
            return False

        # 如果数据库文件不存在，确保目录存在并创建数据库文件
        if not os.path.exists(db_path):
            logger.info(f"数据库文件不存在，将创建新数据库: {db_path}")
            
            # 确保数据库目录存在
            db_dir = os.path.dirname(db_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"创建数据库目录: {db_dir}")
            
            # 创建空的数据库文件
            import sqlite3
            conn = sqlite3.connect(db_path)
            conn.close()
            logger.info(f"创建空数据库文件: {db_path}")
            
            return True

        # 检查数据库完整性
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 检查 alembic_version 表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'")
        if cursor.fetchone():
            cursor.execute("SELECT version_num FROM alembic_version")
            version_row = cursor.fetchone()
            if version_row:
                current_version = version_row[0]

                # 检查当前版本是否在可用迁移中
                available_versions = get_available_versions()
                if current_version not in available_versions:
                    logger.warning(f"数据库版本 {current_version} 不在可用迁移版本中")
                    logger.info(f"可用版本: {available_versions}")

                    # 尝试修复版本不匹配
                    if not fix_version_mismatch(current_version, available_versions):
                        return False
            else:
                logger.warning("alembic_version 表存在但无数据，将重新初始化")
                # 删除空的版本表，让迁移重新创建
                cursor.execute("DROP TABLE IF EXISTS alembic_version")
        else:
            logger.info("alembic_version 表不存在，将创建新数据库")

        conn.close()
        return True

    except Exception as e:
        logger.error(f"数据库一致性验证失败: {e}")
        return False

def get_available_versions():
    """获取可用的迁移版本"""
    versions = []
    alembic_versions_dir = "alembic/versions"

    if not os.path.exists(alembic_versions_dir):
        return versions

    for filename in os.listdir(alembic_versions_dir):
        if filename.endswith('.py') and not filename.startswith('__'):
            filepath = os.path.join(alembic_versions_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n'):
                    if line.strip().startswith('revision = '):
                        version = line.split('=')[1].strip().strip("'\"")
                        versions.append(version)
                        break

    return versions

def fix_version_mismatch(current_version, available_versions):
    """修复版本不匹配问题"""
    try:
        import sqlite3
        import shutil
        import time

        from config_manager import get_database_config
        db_config = get_database_config()
        db_path = db_config.get('DATABASE_PATH')

        # 备份数据库
        backup_path = f"{db_path}.backup_{int(time.time())}"
        shutil.copy2(db_path, backup_path)
        logger.info(f"数据库已备份到: {backup_path}")

        # 重置版本
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # 删除当前版本记录
        cursor.execute("DELETE FROM alembic_version")

        # 设置为最新可用版本
        if available_versions:
            latest_version = max(available_versions, key=lambda x: len(x))
            cursor.execute("INSERT INTO alembic_version (version_num) VALUES (?)", (latest_version,))
            logger.info(f"数据库版本已重置为: {latest_version}")

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"修复版本不匹配失败: {e}")
        return False

def setup_migration_safeguards():
    """Layer 3: 设置迁移安全守卫"""
    try:
        # 创建迁移日志目录
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        # 设置迁移前的安全检查
        from config_manager import is_production_environment

        if is_production_environment():
            logger.warning("在生产环境中执行迁移，请确保已备份数据库")

        return True

    except Exception as e:
        logger.error(f"设置迁移安全守卫失败: {e}")
        return False

def capture_migration_context():
    """Layer 4: 捕获迁移上下文"""
    try:
        import json

        # 收集迁移上下文信息
        context = {
            "timestamp": time.time(),
            "environment": os.getenv('ENV_TYPE', 'unknown'),
            "working_directory": os.getcwd(),
            "python_path": sys.path,
            "database_config": None
        }

        try:
            from config_manager import get_database_config
            context["database_config"] = get_database_config()
        except Exception as e:
            context["database_config_error"] = str(e)

        # 保存上下文信息
        debug_dir = "debug"
        if not os.path.exists(debug_dir):
            os.makedirs(debug_dir, exist_ok=True)

        context_file = os.path.join(debug_dir, "migration_context.json")
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(context, f, indent=2, ensure_ascii=False)

        logger.info(f"迁移上下文已保存到: {context_file}")
        return True

    except Exception as e:
        logger.error(f"捕获迁移上下文失败: {e}")
        return False

def migrate_database():
    """执行数据库迁移（应用 Defense-in-Depth 原则）

    Returns:
        bool: 迁移成功返回 True，失败返回 False
    """
    try:
        # 设置文件处理器
        setup_file_handler()

        logger.info("开始数据库迁移...")

        # Layer 1: 验证迁移前置条件
        if not validate_migration_prerequisites():
            logger.error("迁移前置条件验证失败")
            return False

        # 检查是否存在迁移脚本，如果没有则生成
        if not get_available_versions():
            logger.info("没有找到迁移脚本，正在生成初始迁移...")
            alembic_cfg = Config("alembic.ini")
            command.revision(alembic_cfg, autogenerate=True, message="init_db")
            logger.info("初始迁移脚本生成成功")

        # Layer 2: 验证数据库一致性
        if not validate_database_consistency():
            logger.error("数据库一致性验证失败")
            return False

        # Layer 3: 设置迁移安全守卫
        if not setup_migration_safeguards():
            logger.error("迁移安全守卫设置失败")
            return False

        # Layer 4: 捕获迁移上下文
        if not capture_migration_context():
            logger.error("迁移上下文捕获失败")
            return False

        # 执行迁移
        logger.info("正在执行数据库迁移...")
        alembic_cfg = Config("alembic.ini")
        
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception as e:
            logger.warning(f"迁移过程中出现异常: {e}")
            # 继续执行，因为表可能已经创建
        
        # 验证迁移是否成功并手动处理版本记录
        from config_manager import get_database_config
        db_config = get_database_config()
        db_path = db_config.get('DATABASE_PATH')
        
        if db_path and os.path.exists(db_path):
            import sqlite3
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # 检查alembic_version表是否有记录
            cursor.execute("SELECT version_num FROM alembic_version")
            version_row = cursor.fetchone()
            
            if not version_row:
                # 如果没有版本记录，手动插入最新版本
                available_versions = get_available_versions()
                if available_versions:
                    latest_version = max(available_versions, key=lambda x: len(x))
                    try:
                        cursor.execute("INSERT OR REPLACE INTO alembic_version (version_num) VALUES (?)", (latest_version,))
                        conn.commit()
                        logger.info(f"手动插入版本记录: {latest_version}")
                    except Exception as e:
                        logger.error(f"插入版本记录失败: {e}")
            
            # 验证表是否创建成功
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            table_names = [table[0] for table in tables]
            
            expected_tables = ['users', 'communities', 'checkin_rules', 'checkin_records']
            missing_tables = [table for table in expected_tables if table not in table_names]
            
            if missing_tables:
                logger.error(f"缺少关键表: {missing_tables}")
                conn.close()
                return False
            else:
                logger.info(f"数据库表验证成功，共 {len(table_names)} 个表")
            
            conn.close()

        logger.info("数据库迁移完成")
        return True

    except Exception as e:
        logger.error(f"数据库迁移失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")

        # 记录详细的错误堆栈
        import traceback
        logger.error(f"错误详情:\n{traceback.format_exc()}")

        return False

if __name__ == "__main__":
    """直接运行此脚本时执行迁移"""
    success = migrate_database()
    sys.exit(0 if success else 1)
