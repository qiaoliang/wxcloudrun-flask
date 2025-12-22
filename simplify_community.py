#!/usr/bin/env python3
"""
简化 community_service.py，移除所有 session 参数逻辑
"""

def simplify_community_service():
    # 读取文件
    with open('src/wxcloudrun/community_service.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. 移除方法签名中的 session 参数
    import re
    def remove_session_param(match):
        method = match.group(1)
        params = match.group(2)
        # 移除 session 参数
        params = re.sub(r',\s*session\s*=\s*None', '', params)
        params = re.sub(r',\s*session:\s*[^,)]*', '', params)
        # 清理多余的逗号
        params = re.sub(r',\s*\)', ')', params)
        return method + params
    
    content = re.sub(r'(def\s+\w+\s*\([^)]*)(session[^)]*)(\))', remove_session_param, content)
    
    # 2. 移除所有 session 相关的 if/else 块
    lines = content.split('\n')
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # 跳过 session 相关行
        if 'session is None' in line or 'session:' in line:
            i += 1
            continue
        
        # 跳过注释
        if '# 如果session为None' in line or '# 使用传入的session' in line:
            i += 1
            continue
        
        # 跳过独立的 else 块
        if line.strip() == 'else:' and i > 0:
            # 检查前几行是否有 session 相关
            has_session = False
            for j in range(max(0, i-5), i):
                if 'session' in lines[j]:
                    has_session = True
                    break
            if has_session:
                # 跳过 else 块
                i += 1
                continue
        
        new_lines.append(line)
        i += 1
    
    # 3. 写回文件
    with open('src/wxcloudrun/community_service.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(new_lines))
    
    print("Simplified community service!")

if __name__ == '__main__':
    simplify_community_service()