#!/usr/bin/env python3
"""
修复测试文件中剩余的CommunityService mock
"""
import re
from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 替换所有 CommunityService mock 为 dashboard_repository mock
    # GetCommunityCheckinStatsUseCase
    content = re.sub(
        r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_stats_use_case\.CommunityService'\) as mock_service:\s+mock_service\.has_community_permission\.return_value = True\s+mock_service\.get_community_checkin_stats\.return_value = mock_stats",
        "with patch.object(use_case, 'dashboard_repository') as mock_repo:\n            mock_repo.has_permission.return_value = True\n            mock_repo.get_community_checkin_stats.return_value = mock_stats",
        content
    )

    # GetCommunityCheckinStatsUseCase::test_execute_exception
    content = re.sub(
        r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_stats_use_case\.CommunityService'\) as mock_service:\s+mock_service\.has_community_permission\.return_value = True\s+mock_service\.get_community_checkin_stats\.side_effect = Exception\('数据库错误'\)",
        "with patch.object(use_case, 'dashboard_repository') as mock_repo:\n            mock_repo.has_permission.return_value = True\n            mock_repo.get_community_checkin_stats.side_effect = Exception('数据库错误')",
        content
    )

    # GetCommunityCheckinRulesUseCase::test_execute_exception
    content = re.sub(
        r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rules_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.get_community_rules\.side_effect = Exception\('数据库错误'\)",
        "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.find_by_community_id.side_effect = Exception('数据库错误')",
        content
    )

    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("修复测试文件中剩余的CommunityService mock")
    print("=" * 60)

    test_file = Path("tests/unit/test_community_checkin_use_cases.py")

    if not test_file.exists():
        print(f"❌ 文件不存在: {test_file}")
        return

    original_content = test_file.read_text(encoding='utf-8')

    if fix_test_file(test_file):
        print(f"✅ 已修复: {test_file}")
    else:
        print(f"ℹ️  无需修改: {test_file}")

    print("=" * 60)
    print("修复完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()