# 创建应用实例
import sys
from config_manager import should_start_flask_service
from wxcloudrun import app

# 根据环境变量决定是否启动Flask Web服务
if __name__ == '__main__':
    if should_start_flask_service():
        # 仅在非unit环境下启动Flask服务
        host = sys.argv[1] if len(sys.argv) > 1 else '0.0.0.0'
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 8080
        app.run(host=host, port=port)
    else:
        # unit环境下不启动Web服务，仅用于运行测试
        print("ENV_TYPE=unit, 跳过启动Flask Web服务。此环境仅用于运行单元测试。")
