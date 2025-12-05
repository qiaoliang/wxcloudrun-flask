# 创建应用实例
import sys
import os
import logging
from wxcloudrun import app, db

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


def run_auto_migration():
    """ENV_TYPE!= unit 时，自动执行数据库迁移。"""
    try:
        # 检查是否为 unit 环境（内存数据库）
        db_config = app.config.get('SQLALCHEMY_DATABASE_URI', '')

        migration_logger.info("开始检查数据库迁移...")

        # 检查并创建数据库文件（如果是SQLite）
        if 'sqlite://' in db_config:
            db_path = db_config.replace('sqlite:///', '')
            db_dir = os.path.dirname(db_path)

            # 确保数据库目录存在
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                migration_logger.info(f"创建数据库目录: {db_dir}")

            # 如果数据库文件不存在，创建空数据库文件
            if not os.path.exists(db_path):
                migration_logger.info(f"创建空数据库文件: {db_path}")
                # 创建空数据库文件
                open(db_path, 'a').close()

        # 导入 Flask-Migrate 相关模块
        from flask_migrate import upgrade, current

        # 检查当前数据库版本
        with app.app_context():
            try:
                current_revision = current()
                migration_logger.info(f"当前数据库版本: {current_revision}")
            except Exception as e:
                migration_logger.info(f"数据库未初始化或获取版本失败: {e}")
                current_revision = None

            # 执行迁移
            try:
                migration_logger.info("开始执行数据库迁移...")
                upgrade()
                migration_logger.info("数据库迁移执行成功！")

                # 显示迁移后的版本
                new_revision = current()
                migration_logger.info(f"迁移后数据库版本: {new_revision}")

                # 检查数据库文件是否创建
                if 'sqlite://' in db_config and os.path.exists(db_path):
                    migration_logger.info(f"数据库文件已创建: {db_path}")

            except Exception as e:
                migration_logger.error(f"数据库迁移执行失败: {e}")
                migration_logger.error("应用启动失败，请检查数据库配置和迁移文件。")
                sys.exit(1)

    except Exception as e:
        migration_logger.error(f"自动迁移过程中发生错误: {e}")
        migration_logger.error("应用启动失败，请检查迁移配置。")
        sys.exit(1)


# 根据环境变量决定是否启动Flask Web服务
if __name__ == '__main__':
    # 在启动应用之前执行自动迁移,unit 使用内存数据库，不用迁移
    if (os.getenv('ENV_TYPE') not in ['unit', '']):
        run_auto_migration()

    # 仅在非unit环境下启动Flask服务
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    app.run(host=host, port=port)
