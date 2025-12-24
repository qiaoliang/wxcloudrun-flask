import os
import sys

# 添加父目录到路径，以便导入 app 模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 使用应用工厂创建应用实例
from app import create_app

# 创建应用实例
app = create_app()

# 导入后台任务
from .background_tasks import start_missing_check_service

# 在 unit 环境下不启动后台服务
import config_manager
if not config_manager.is_unit_environment():
    app.logger.info(f"app.debug={app.debug}")
    try:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
            app.logger.info(f"# 启动后台的打卡扫描检测服务")
            start_missing_check_service()
    except Exception as e:
        app.logger.error(f"启动后台missing服务失败: {str(e)}")
else:
    app.logger.info("unit 环境下不启动后台服务")
