"""
用于运行 Flask-Migrate 命令的脚本
"""
import os
import sys
from flask_migrate import upgrade, stamp, Migrate
from flask import Flask
from wxcloudrun import app, db

def init_db_with_migrate():
    """初始化数据库并创建初始迁移"""
    with app.app_context():
        # 导入所有模型以确保它们被 Alembic 识别
        from wxcloudrun import model
        
        # 尝试创建所有表
        db.create_all()
        print("数据库表创建完成")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python run_migrations.py [init|stamp|upgrade|migrate]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == 'init':
        # 初始化数据库表
        init_db_with_migrate()
    elif command == 'stamp':
        # 为当前数据库打上初始版本标签
        from flask_migrate import stamp
        with app.app_context():
            stamp()  # 为当前数据库结构创建初始版本
            print("数据库已标记为初始版本")
    elif command == 'upgrade':
        # 应用所有迁移
        with app.app_context():
            upgrade()
            print("数据库升级完成")
    else:
        print(f"未知命令: {command}")
        print("用法: python run_migrations.py [init|stamp|upgrade|migrate]")
        sys.exit(1)