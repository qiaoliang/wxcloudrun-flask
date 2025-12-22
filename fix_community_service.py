#!/usr/bin/env python3
"""
修复 community_service.py 中的 session 引用问题
"""

def fix_community_service():
    # 读取文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复剩余的 session. 引用（在注释的块内）
    content = content.replace('session.merge(user)', 'db.session.merge(user)')
    content = content.replace('session.commit()', 'db.session.commit()')
    content = content.replace('session.query(', 'db.session.query(')
    content = content.replace('session.add(', 'db.session.add(')
    content = content.replace('session.delete(', 'db.session.delete(')
    content = content.replace('session.flush()', 'db.session.flush()')
    content = content.replace('session.refresh(', 'db.session.refresh(')
    
    # 2. 移除 session 参数相关的 else 块
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 如果是 else 块且前一行是 session is None
        if 'else:' in line and i > 0 and 'session is None' in lines[i-1]:
            # 跳过 else 块
            i += 1
            # 找到下一个同级或更高级的代码
            else_indent = len(line) - len(line.lstrip())
            while i < len(lines):
                if lines[i].strip() == '':
                    i += 1
                    continue
                current_indent = len(lines[i]) - len(lines[i].lstrip())
                if current_indent <= else_indent:
                    break
                i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # 3. 移除 session 参数（简化处理）
    final_lines = []
    for line in new_lines:
        # 简单移除 session=None 参数
        if 'session=None' in line:
            line = line.replace(', session=None', '')
            line = line.replace('session=None, ', '')
        # 移除整个 session 参数声明
        if 'session:' in line and 'def ' in line:
            # 保留方法定义，但移除 session 参数
            parts = line.split('(')
            if len(parts) > 1:
                rest = parts[1]
                if 'session:' in rest:
                    # 找到 session 参数的位置
                    session_pos = rest.find('session:')
                    # 找到参数结束位置
                    param_end = rest.find(',', session_pos)
                    if param_end == -1:
                        param_end = rest.find(')', session_pos)
                    # 移除这个参数
                    before = rest[:session_pos].rstrip(', ')
                    after = rest[param_end+1:].lstrip(', ')
                    line = parts[0] + '(' + before + after
        final_lines.append(line)
    
    # 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))
    
    print("Community service fix completed!")

if __name__ == '__main__':
    fix_community_service()