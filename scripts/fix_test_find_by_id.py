#!/usr/bin/env python3
"""
修复测试文件中的get_by_id改为find_by_id
"""
import re
from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 替换 get_by_id 为 find_by_id
    new_content = content.replace('mock_repo.get_by_id', 'mock_repo.find_by_id')

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("修复测试文件中的get_by_id改为find_by_id")
    print("=" * 60)

    test_file = Path("tests/unit/test_community_checkin_use_cases.py")

    if not test_file.exists():
        print(f"❌ 文件不存在: {test_file}")
        return

    if fix_test_file(test_file):
        print(f"✅ 已修复: {test_file}")
    else:
        print(f"ℹ️  无需修改: {test_file}")

    print("=" * 60)
    print("修复完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()