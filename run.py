#!/usr/bin/env python3
"""
应用启动脚本
确保所有环境都使用init_database.py进行数据库初始化
"""
import sys
import subprocess
import logging
import os

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 首先执行数据库初始化脚本
logger.info("执行数据库初始化脚本...")
try:
    # 调用init_database.py脚本进行数据库初始化
    subprocess.run([sys.executable, "init_database.py"], check=True)
    logger.info("数据库初始化成功")
except subprocess.CalledProcessError as e:
    logger.error(f"数据库初始化失败: {e}")
    sys.exit(1)

# 然后启动Flask Web服务
logger.info("启动Flask Web服务...")
from wxcloudrun import app

if __name__ == '__main__':
    if len(sys.argv) < 3:
        logger.error("需要提供主机和端口参数")
        logger.error("使用示例: python3 run.py 0.0.0.0 8080")
        sys.exit(1)
    
    host = sys.argv[1]
    port = sys.argv[2]
    logger.info(f"启动服务: http://{host}:{port}")
    app.run(host=host, port=port)
