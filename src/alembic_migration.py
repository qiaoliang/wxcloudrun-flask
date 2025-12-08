"""
独立的 Alembic 数据库迁移脚本
完全独立于 Flask 应用，可以直接运行
"""
import logging
import sys
import os
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

# 文件处理器（在需要时创建）
def setup_file_handler():
    """设置文件处理器"""
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/migration.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

def migrate_database():
    """执行数据库迁移
    
    Returns:
        bool: 迁移成功返回 True，失败返回 False
    """
    try:
        # 设置文件处理器
        setup_file_handler()
        
        logger.info("开始数据库迁移...")
        
        # 加载 Alembic 配置
        alembic_cfg = Config("alembic.ini")
        
        # 执行迁移
        command.upgrade(alembic_cfg, "head")
        
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
