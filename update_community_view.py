#!/usr/bin/env python3
"""
更新 community.py 视图文件
"""

def update_community_view():
    # 读取文件
    with open('src/wxcloudrun/views/community.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. 更新导入语句
    content = content.replace(
        'from database.flask_models import CommunityStaff',
        'from database.flask_models import CommunityStaff'
    )
    content = content.replace(
        'from database import get_session',
        '# from database import get_session  # Using Flask-SQLAlchemy'
    )

    # 2. 移除 db = get_database()
    content = content.replace('db = get_database()\n', '')

    # 3. 替换数据库访问模式
    # 简单替换一些常见模式
    content = content.replace('with get_db().get_session() as session:', '# Using Flask-SQLAlchemy db.session')
    content = content.replace('with db.get_session() as session:', '# Using Flask-SQLAlchemy db.session')
    content = content.replace('with get_session() as session:', '# Using Flask-SQLAlchemy db.session')
    content = content.replace('session.query(', 'db.session.query(')
    content = content.replace('session.add(', 'db.session.add(')
    content = content.replace('session.merge(', 'db.session.merge(')
    content = content.replace('session.commit()', 'db.session.commit()')
    content = content.replace('session.flush()', 'db.session.flush()')
    content = content.replace('session.refresh(', 'db.session.refresh(')

    # 写回文件
    with open('src/wxcloudrun/views/community.py', 'w', encoding='utf-8') as f:
        f.write(content)

    print("Updated community view!")

if __name__ == '__main__':
    update_community_view()