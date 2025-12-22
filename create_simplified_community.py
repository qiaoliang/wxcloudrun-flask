#!/usr/bin/env python3
"""
创建简化版的 community_service.py
"""

def create_simplified_version():
    # 读取原始文件
    with open('src/wxcloudrun/old_community_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换导入
    content = content.replace(
        'from .dao import get_db\nfrom database.models import User, Community, CommunityApplication, UserAuditLog',
        'from database.flask_models import db, User, Community, CommunityApplication, UserAuditLog'
    )
    
    # 简化方法 - 移除 session 参数逻辑
    lines = content.split('\n')
    new_lines = []
    i = 0
    in_method = False
    method_indent = 0
    
    while i < len(lines):
        line = lines[i]
        
        # 检测方法定义
        if 'def ' in line and '@staticmethod' in lines[i-1] if i > 0 else False:
            # 移除 session 参数
            line = line.replace(', session=None', '')
            line = line.replace(', session:', '')
            line = line.replace('session=None', '')
            new_lines.append(line)
            in_method = True
            method_indent = len(line) - len(line.lstrip())
            i += 1
            continue
        
        # 在方法内部
        if in_method:
            # 检测方法结束
            if line.strip() == '' or (len(line) - len(line.lstrip()) <= method_indent and line.strip() != '' and not line.strip().startswith('#')):
                in_method = False
                new_lines.append(line)
                i += 1
                continue
            
            # 跳过 session 相关代码
            if 'session is None' in line or 'session:' in line:
                i += 1
                # 跳过整个 if 块
                while i < len(lines):
                    if lines[i].strip() == 'else:':
                        i += 1
                        # 跳过 else 块
                        else_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                        while i < len(lines):
                            if lines[i].strip() == '':
                                i += 1
                                continue
                            current_indent = len(lines[i]) - len(lines[i].lstrip())
                            if current_indent <= else_indent:
                                break
                            i += 1
                        break
                    elif lines[i].strip() == '' or len(lines[i]) - len(lines[i].lstrip()) > method_indent:
                        i += 1
                    else:
                        break
                continue
            
            # 替换数据库操作
            if 'get_db()' in line:
                line = '# ' + line  # 注释掉
            if 'session.query' in line:
                line = line.replace('session.query', 'db.session.query')
            if 'session.add' in line:
                line = line.replace('session.add', 'db.session.add')
            if 'session.merge' in line:
                line = line.replace('session.merge', 'db.session.merge')
            if 'session.commit' in line:
                line = line.replace('session.commit', 'db.session.commit')
            if 'session.flush' in line:
                line = line.replace('session.flush', 'db.session.flush')
            if 'session.expunge' in line:
                line = line.replace('session.expunge', 'db.session.expunge')
            if 'session.delete' in line:
                line = line.replace('session.delete', 'db.session.delete')
            
            new_lines.append(line)
            i += 1
        else:
            new_lines.append(line)
            i += 1
    
    # 写入新文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("Created simplified version!")

if __name__ == '__main__':
    create_simplified_version()