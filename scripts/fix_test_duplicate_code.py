#!/usr/bin/env python3
"""
修复测试文件中的重复代码和旧Service mock
"""
import re
from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 删除重复的代码段
    # 删除 test_execute_success 中的重复代码
    pattern1 = r"(assert result\.status == UseCaseStatus\.SUCCESS\s+assert '获取统计信息成功' in result\.message\s+)(# Arrange\s+community_id = 1\s+user_id = 123\s+mock_stats = \{'date': '2026-01-15', 'total': 10, 'completed': 8\}\s+with patch\('app\.application\.use_cases\.community_checkin\.get_community_daily_stats_use_case\.CommunityService'\) as mock_service:.*?assert result\.data == mock_stats\s+)"
    new_content = re.sub(pattern1, r"\1", content, flags=re.DOTALL)

    # 替换 CommunityService mock 为 dashboard_repository mock
    pattern2 = "with patch('app.application.use_cases.community_checkin.get_community_daily_stats_use_case.CommunityService') as mock_service:\s+mock_service.has_community_permission.return_value = False"
    replacement2 = "with patch.object(use_case, 'dashboard_repository') as mock_repo:\n            mock_repo.has_permission.return_value = False"
    new_content = new_content.replace(pattern2, replacement2)

    if new_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("修复测试文件中的重复代码和旧Service mock")
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