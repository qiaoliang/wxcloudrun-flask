#!/usr/bin/env python3
"""
最终修复 community_service.py
"""

def final_fix():
    # 读取文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 修复 db.db.session 错误
    content = content.replace('db.db.session', 'db.session')
    
    # 2. 移除 session 参数相关的判断
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 如果是 session is None 的判断
        if 'if session is None:' in line:
            # 跳过这个判断块
            i += 1
            # 找到对应的 else 或块结束
            while i < len(lines):
                if lines[i].strip().startswith('else:'):
                    # 跳过 else 块
                    i += 1
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
                elif lines[i].strip() == '' or lines[i].startswith('#'):
                    i += 1
                    continue
                else:
                    # 这是实际的代码块，保留但减少缩进
                    if '        ' in line:  # 8 spaces or more
                        new_line = '    ' + line.lstrip()  # 减少到4 spaces
                        new_lines.append(new_line)
                    i += 1
            continue
        
        # 跳过 else 块
        if 'else:' in line and i > 0 and 'session is None' in lines[i-1]:
            i += 1
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
        
        # 移除注释掉的行
        if line.strip().startswith('# db = get_db()') or line.strip().startswith('# with db.get_session()'):
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # 3. 移除方法签名中的 session 参数
    final_lines = []
    for line in new_lines:
        # 处理方法定义行
        if 'def ' in line and '(' in line and ')' in line:
            # 简单移除 session 参数
            if 'session=' in line or 'session:' in line:
                # 保留方法名和其他参数
                import re
                # 匹配方法定义
                match = re.match(r'(\s*def\s+\w+\s*\([^)]*))(session[^)]*)?([^)]*\))', line)
                if match:
                    line = match.group(1) + match.group(3)
        final_lines.append(line)
    
    # 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))
    
    print("Final fix completed!")

if __name__ == '__main__':
    final_fix()