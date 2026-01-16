#!/usr/bin/env python3
"""
修复集成测试文件中的缩进问题
"""
import re

def fix_indentation(file_path):
    """修复文件中的缩进问题"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    fixed_lines = []
    for i, line in enumerate(lines):
        # 修复use_case = CreateEventUseCase()的缩进
        if 'use_case = CreateEventUseCase()' in line:
            # 查找前一个非空行
            j = i - 1
            while j >= 0 and not lines[j].strip():
                j -= 1
            if j >= 0:
                # 使用前一个非空行的缩进
                indent = re.match(r'^\s*', lines[j]).group(0)
                fixed_lines.append(indent + 'use_case = CreateEventUseCase()\n')
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    return True

def main():
    print("============================================================")
    print("修复集成测试文件中的缩进问题")
    print("============================================================")
    
    files = [
        "/Users/qiaoliang/working/code/safeGuard/backend/tests/integration/test_events_operations.py",
        "/Users/qiaoliang/working/code/safeGuard/backend/tests/integration/test_close_event.py"
    ]
    
    for file_path in files:
        if fix_indentation(file_path):
            print(f"✅ 已修复: {file_path}")
        else:
            print(f"❌ 修复失败: {file_path}")
    
    print("============================================================")
    print("修复完成！")
    print("============================================================")

if __name__ == "__main__":
    main()