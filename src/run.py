#!/usr/bin/env python3
"""
SafeGuard 后端应用主入口
使用标准的 Flask 应用工厂模式启动应用
"""

import sys
import os
import logging

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 导入应用工厂
from app import create_app

# 配置迁移日志
import datetime
migration_logger = logging.getLogger('migration')
migration_logger.setLevel(logging.INFO)

# 确保日志目录存在
logs_dir = 'logs'
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir, exist_ok=True)

# 生成带时间戳的日志文件名
timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
log_filename = os.path.join(logs_dir, f'migration_{timestamp}.log')

# 创建文件处理器
file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.INFO)
# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
# 创建格式器
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)
# 添加处理器到日志器
migration_logger.addHandler(file_handler)
migration_logger.addHandler(console_handler)

# 关闭传播以避免与根日志器重复处理
migration_logger.propagate = False

# 在导入应用之前检查 ENV_TYPE
env_type = os.getenv('ENV_TYPE')
# 只在主进程中记录此日志，避免 Flask 重启时重复
if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
    migration_logger.info(f'启动时检查 ENV_TYPE: {env_type}')

if env_type is None or env_type == '':
    migration_logger.error("错误: ENV_TYPE 环境变量未设置！")
    migration_logger.error("请设置 ENV_TYPE 环境变量后重新启动应用:")
    migration_logger.error("  - 开发环境: ENV_TYPE=function")
    migration_logger.error("  - 单元测试: ENV_TYPE=unit")
    migration_logger.error("  - UAT环境: ENV_TYPE=uat")
    migration_logger.error("  - 生产环境: ENV_TYPE=prod")
    migration_logger.error("启动失败，请配置环境变量。")
    sys.exit(1)


def run_migration():
    """执行数据库迁移，返回是否成功"""
    try:
        from alembic_migration import migrate_database
        success = migrate_database()
        if not success:
            migration_logger.error("数据库迁移失败")
            return False
        migration_logger.info("数据库迁移成功")
        return True
    except Exception as e:
        migration_logger.error(f"迁移过程中发生异常: {str(e)}")
        return False


def main():
    """主程序入口"""
    # 1. 使用应用工厂创建 Flask 应用实例
    flask_app = create_app()

    # 获取环境类型
    env_type = os.getenv('ENV_TYPE', 'unit')

    # 检查是否为Flask调试器重启的子进程
    is_flask_restart = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
    is_debug_mode = flask_app.debug

    # 2. 数据库迁移和应用初始化
    with flask_app.app_context():
        # 3. 执行数据库迁移（unit 环境使用内存数据库，跳过迁移）
        if env_type in ['unit']:
            migration_logger.info("检测到 unit 环境（内存数据库），跳过数据库迁移")
            migration_success = True
            
            # 在 unit 环境下，需要手动创建 Flask-SQLAlchemy 的表
            migration_logger.info("在 unit 环境下创建 Flask-SQLAlchemy 表")
            from app.extensions import db
            db.create_all()
            migration_logger.info("Flask-SQLAlchemy 表创建完成")
        elif is_debug_mode and not is_flask_restart:
            # 调试模式下的第一次启动（主进程）
            migration_logger.info("调试模式主进程：执行数据库迁移")
            migration_success = run_migration()
            if not migration_success:
                migration_logger.error("数据库迁移失败，程序退出")
                sys.exit(1)
        elif is_debug_mode and is_flask_restart:
            # 调试模式下的重启（子进程），跳过迁移
            migration_logger.info("调试模式重启进程：跳过数据库迁移")
            migration_success = True
        else:
            # 生产模式，正常执行迁移
            migration_success = run_migration()
            if not migration_success:
                migration_logger.error("数据库迁移失败，程序退出")
                sys.exit(1)
        
        # 4. 初始化超级管理员和默认社区
        should_initialize = False
        
        if env_type == 'function':
            # function环境总是执行初始化
            should_initialize = True
            flask_app.logger.info("function环境：总是执行超级管理员和默认社区初始化")
        elif env_type not in ['unit'] and (not is_debug_mode or not is_flask_restart):
            # 其他非unit环境，在非调试模式或调试模式的主进程中执行
            should_initialize = True
            flask_app.logger.info("开始注入超级管理员和默认社区.....")
        
        if should_initialize:
            # 创建超级管理员和默认社区
            from database.initialization import create_super_admin_and_default_community
            create_super_admin_and_default_community()
            flask_app.logger.info("注入完成。请使用超级管理员和默认社区！！！")
        else:
            flask_app.logger.info("跳过超级管理员和默认社区注入")

    # 5. 启动 Flask 应用
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    flask_app.run(host=host, port=port)


if __name__ == '__main__':
    main()