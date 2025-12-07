#!/usr/bin/env python3
"""
数据库迁移工具脚本
提供 Flask-Migrate 的命令行接口
"""

import os
import sys
from flask.cli import FlaskGroup
from wxcloudrun import app, db

# 创建 Flask CLI 组
cli = FlaskGroup(app)

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python migrate_tool.py <flask命令>")
        print("示例:")
        print("  python migrate_tool.py db init")
        print("  python migrate_tool.py db migrate -m '初始迁移'")
        print("  python migrate_tool.py db upgrade")
        print("  python migrate_tool.py db downgrade")
        return 1
    
    # 设置 FLASK_APP 环境变量
    os.environ['FLASK_APP'] = 'wxcloudrun'
    
    # 执行 Flask 命令
    try:
        from flask.cli import main as flask_main
        sys.argv = ['flask'] + sys.argv[1:]
        flask_main()
        return 0
    except Exception as e:
        print(f"执行命令失败: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())