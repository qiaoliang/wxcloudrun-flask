#!/usr/bin/env python3
"""
将 community_service.py 从 get_db() 模式迁移到 Flask-SQLAlchemy 的 db.session 模式
"""

def migrate_community_service():
    # 读取原始文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_session_block = False
    skip_next_lines = 0
    
    for i, line in enumerate(lines):
        # 跳过需要跳过的行
        if skip_next_lines > 0:
            skip_next_lines -= 1
            continue
        
        # 处理 get_db() 模式
        if 'db = get_db()' in line:
            # 注释掉这行
            new_lines.append('# db = get_db()  # Replaced with Flask-SQLAlchemy db.session\n')
            continue
        
        # 处理 with 语句
        if 'with db.get_session() as session:' in line:
            in_session_block = True
            # 注释掉这行
            new_lines.append('# with db.get_session() as session:  # Using Flask-SQLAlchemy db.session\n')
            continue
        
        # 处理 session 块结束
        if in_session_block and line.strip() == '':
            # 添加 db.session.commit() 如果需要
            if i + 1 < len(lines) and not lines[i+1].strip().startswith('#') and 'db.session.commit()' not in lines[i+1]:
                new_lines.append(line)  # 保留空行
            continue
        
        # 在会话块内，替换 session. 为 db.session.
        if in_session_block:
            if 'session.' in line:
                new_line = line.replace('session.', 'db.session.')
                new_lines.append(new_line)
                continue
            elif 'db.session.commit()' in line:
                # 保留 commit
                new_lines.append(line)
                continue
            elif 'db.session.flush()' in line:
                # 保留 flush
                new_lines.append(line)
                continue
            elif line.strip() == '' or line.strip().startswith('#'):
                # 结束会话块
                in_session_block = False
                new_lines.append(line)
                continue
            else:
                # 其他会话块内的代码
                new_lines.append(line)
                continue
        
        # 处理 session 参数相关的 else 块
        if 'else:' in line and i > 0 and 'session is None' in lines[i-1]:
            # 跳过整个 else 块
            skip_next_lines = 1
            # 查找块结束
            j = i + 1
            indent_level = len(line) - len(line.lstrip())
            while j < len(lines):
                if lines[j].strip() == '':
                    skip_next_lines += 1
                    j += 1
                elif len(lines[j]) - len(lines[j].lstrip()) <= indent_level and lines[j].strip() != '':
                    break
                else:
                    skip_next_lines += 1
                    j += 1
            new_lines.append('# else:  # Removed session parameter handling\n')
            continue
        
        # 默认情况，保留行
        new_lines.append(line)
    
    # 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("Community service migration completed!")

if __name__ == '__main__':
    migrate_community_service()
