#!/usr/bin/env python3
"""
正确处理 community_service.py 的迁移
"""

def fix_community_service():
    # 读取文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 处理 if session is None 块
        if 'if session is None:' in line:
            # 保留这行但修改内容
            new_lines.append('        # Flask-SQLAlchemy: Always use db.session\n')
            i += 1
            # 跳过空行
            while i < len(lines) and lines[i].strip() == '':
                i += 1
            # 处理实际代码，减少缩进
            while i < len(lines) and not lines[i].strip().startswith('else:'):
                if lines[i].strip() != '':
                    # 减少缩进
                    new_line = '    ' + lines[i].lstrip()
                    new_lines.append(new_line)
                i += 1
            continue
        
        # 跳过 else 块
        if 'else:' in line and i > 0 and 'session is None' in lines[i-1]:
            # 跳过 else 及其内容
            i += 1
            indent = len(line) - len(line.lstrip())
            while i < len(lines):
                if lines[i].strip() == '':
                    i += 1
                    continue
                current_indent = len(lines[i]) - len(lines[i].lstrip())
                if current_indent <= indent:
                    break
                i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("Fixed community service!")

if __name__ == '__main__':
    fix_community_service()