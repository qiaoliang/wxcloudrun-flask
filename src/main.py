# 创建应用实例
import sys
import os
import logging

# 添加当前目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

# 在导入 wxcloudrun 之前检查 ENV_TYPE
env_type = os.getenv('ENV_TYPE')
migration_logger.info(f'启动时检查 ENV_TYPE: {env_type}')

if env_type is None or env_type == '':
    migration_logger.error("错误: ENV_TYPE 环境变量未设置！")
    migration_logger.error("请设置 ENV_TYPE 环境变量后重新启动应用:")
    migration_logger.error("  - 开发环境: ENV_TYPE=func")
    migration_logger.error("  - 单元测试: ENV_TYPE=unit")
    migration_logger.error("  - UAT环境: ENV_TYPE=uat")
    migration_logger.error("  - 生产环境: ENV_TYPE=prod")
    migration_logger.error("启动失败，请配置环境变量。")
    sys.exit(1)

# 现在可以安全地导入 wxcloudrun
from wxcloudrun import app, db


def create_app():
    """创建并配置 Flask 应用"""
    return app


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
    # 1. 首先执行数据库迁移（unit 环境使用内存数据库，跳过迁移）
    env_type = os.getenv('ENV_TYPE', 'unit')
    if env_type not in ['unit']:
        migration_success = run_migration()
        if not migration_success:
            migration_logger.error("数据库迁移失败，程序退出")
            sys.exit(1)
    else:
        migration_logger.info("检测到 unit 环境（内存数据库），跳过数据库迁移")
    
    # 2. 创建并启动 Flask 应用
    create_app()
    
    # 3. 在非 unit 环境下初始化默认社区（unit 环境已在 __init__.py 中处理）
    if env_type not in ['unit']:
        with app.app_context():
            try:
                from wxcloudrun.community_service import CommunityService
                default_community = CommunityService.get_or_create_default_community()
                migration_logger.info(f"默认社区初始化完成: {default_community.name} (ID: {default_community.community_id})")
            except Exception as e:
                migration_logger.error(f"初始化默认社区失败: {str(e)}", exc_info=True)
    
    # 4. 启动 Flask 应用
    host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
    app.run(host=host, port=port)


# 根据环境变量决定是否启动Flask Web服务
if __name__ == '__main__':
    main()
