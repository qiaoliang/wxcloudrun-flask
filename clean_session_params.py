#!/usr/bin/env python3
"""
清理 community_service.py 中的 session 参数
"""

import re

def clean_session_params():
    # 读取文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除方法签名中的 session 参数
    def fix_method_signature(match):
        method_def = match.group(1)
        params = match.group(2)
        # 移除 session 参数
        params = re.sub(r',?\s*session\s*=\s*None', '', params)
        params = re.sub(r',?\s*session:\s*.*?(?=,|\))', '', params)
        # 清理多余的逗号
        params = re.sub(r',\s*\)', ')', params)
        return method_def + params
    
    # 匹配方法定义
    pattern = r'(\s*def\s+\w+\s*\()([^)]*)(\))'
    content = re.sub(pattern, fix_method_signature, content)
    
    # 2. 移除 session is None 的判断块
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过 session 相关的判断
        if 'if session is None:' in line:
            # 找到对应的 else
            i += 1
            while i < len(lines) and not 'else:' in lines[i]:
                i += 1
            if i < len(lines) and 'else:' in lines[i]:
                # 跳过 else 块
                i += 1
                indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                while i < len(lines):
                    if lines[i].strip() == '':
                        i += 1
                        continue
                    current_indent = len(lines[i]) - len(lines[i].lstrip())
                    if current_indent <= indent:
                        break
                    i += 1
            continue
        
        # 跳过独立的 else 块
        if 'else:' in line and i > 0 and 'session is None' in lines[i-1]:
            i += 1
            continue
        
        new_lines.append(line)
        i += 1
    
    # 3. 清理注释
    final_lines = []
    for line in new_lines:
        if line.strip().startswith('# Using Flask-SQLAlchemy'):
            continue
        final_lines.append(line)
    
    # 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(final_lines))
    
    print("Session params cleaned!")

if __name__ == '__main__':
    clean_session_params()