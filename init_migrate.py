"""
初始化 Flask-Migrate 的脚本
此脚本用于创建初始迁移文件，以反映当前的数据库结构
"""
import os
from wxcloudrun import app, db

# 设置环境变量以避免测试模式的干扰
os.environ['USE_SQLITE_FOR_TESTING'] = 'false'

if __name__ == '__main__':
    with app.app_context():
        # 创建数据库表（如果不存在）
        db.create_all()
        print("数据库初始化完成")