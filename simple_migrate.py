#!/usr/bin/env python3
"""
简化的数据库迁移脚本，用于处理已有表的情况
"""
import os
import sys
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, stamp, upgrade
import pymysql

# 安装MySQL驱动
pymysql.install_as_MySQLdb()

# 创建Flask应用
app = Flask(__name__)

# 配置数据库连接
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:rootpassword@127.0.0.1:3306/flask_demo?charset=utf8mb4'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 初始化数据库
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 导入模型
sys.path.append('/Users/qiaoliang/working/code/safeGuard/backend')
from wxcloudrun.model import Counters, User, CheckinRule, CheckinRecord

def main():
    command = sys.argv[1] if len(sys.argv) > 1 else 'help'
    
    with app.app_context():
        if command == 'init':
            try:
                init()
                print("Flask-Migrate环境初始化完成")
            except Exception as e:
                print(f"初始化失败（可能已经存在）: {e}")
        
        elif command == 'migrate':
            try:
                migrate(message="Initial migration")
                print("迁移文件生成完成")
            except Exception as e:
                print(f"生成迁移文件失败: {e}")
        
        elif command == 'stamp':
            try:
                stamp()
                print("数据库状态标记完成")
            except Exception as e:
                print(f"标记数据库状态失败: {e}")
        
        elif command == 'upgrade':
            try:
                upgrade()
                print("数据库升级完成")
            except Exception as e:
                print(f"数据库升级失败: {e}")
        
        elif command == 'current':
            try:
                from flask_migrate import current
                print(f"当前版本: {current()}")
            except Exception as e:
                print(f"获取当前版本失败: {e}")
        
        else:
            print("用法: python simple_migrate.py [init|migrate|stamp|upgrade|current]")

if __name__ == '__main__':
    main()