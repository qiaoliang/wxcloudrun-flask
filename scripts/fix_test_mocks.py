#!/usr/bin/env python3
"""
修复测试文件中的Service mock，改为Repository mock
"""
import re
from pathlib import Path

def fix_test_file(file_path):
    """修复单个测试文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 定义替换规则
    replacements = [
        # CreateCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.create_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.create_community_rule\.return_value = mock_rule",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.save.return_value = mock_rule"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.create_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.create_community_rule\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.save.side_effect = Exception('数据库错误')"
        ),
        # DeleteCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.delete_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.delete_community_rule\.return_value = True",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.delete.return_value = True"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.delete_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.delete_community_rule\.return_value = False",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.delete.return_value = False"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.delete_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.delete_community_rule\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.delete.side_effect = Exception('数据库错误')"
        ),
        # DisableCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.disable_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.disable_community_rule\.return_value = \{'status': 0\}",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_rule = Mock()\n            mock_rule.status = 0\n            mock_repo.get_by_id.return_value = mock_rule\n            mock_repo.update.return_value = mock_rule"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.disable_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.disable_community_rule\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_id.side_effect = Exception('数据库错误')"
        ),
        # EnableCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.enable_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.enable_community_rule\.return_value = \{'status': 1\}",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_rule = Mock()\n            mock_rule.status = 1\n            mock_repo.get_by_id.return_value = mock_rule\n            mock_repo.update.return_value = mock_rule"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.enable_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.enable_community_rule\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_id.side_effect = Exception('数据库错误')"
        ),
        # GetCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_rule = Mock\(\)\s+mock_rule\.community_rule_id = 1\s+mock_rule\.rule_name = '测试规则'\s+mock_service\.get_rule_detail\.return_value = mock_rule",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_rule = Mock()\n            mock_rule.community_rule_id = 1\n            mock_rule.rule_name = '测试规则'\n            mock_repo.get_by_id.return_value = mock_rule"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.get_rule_detail\.return_value = None",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_id.return_value = None"
        ),
        # GetCommunityCheckinRulesUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rules_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_rule1 = Mock\(\)\s+mock_rule1\.community_rule_id = 1\s+mock_rule2 = Mock\(\)\s+mock_rule2\.community_rule_id = 2\s+mock_service\.get_community_rules\.return_value = \[mock_rule1, mock_rule2\]",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_rule1 = Mock()\n            mock_rule1.community_rule_id = 1\n            mock_rule2 = Mock()\n            mock_rule2.community_rule_id = 2\n            mock_repo.get_by_community_id.return_value = [mock_rule1, mock_rule2]"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rules_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.get_community_rules\.return_value = \[\]",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_community_id.return_value = []"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.get_community_checkin_rules_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.get_community_rules\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_community_id.side_effect = Exception('数据库错误')"
        ),
        # UpdateCommunityCheckinRuleUseCase
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.update_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_rule = Mock\(\)\s+mock_rule\.community_rule_id = 1\s+mock_rule\.rule_name = '更新后的规则'\s+mock_service\.update_community_rule\.return_value = mock_rule",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_rule = Mock()\n            mock_rule.community_rule_id = 1\n            mock_rule.rule_name = '更新后的规则'\n            mock_repo.get_by_id.return_value = mock_rule\n            mock_repo.update.return_value = mock_rule"
        ),
        (
            r"with patch\('app\.application\.use_cases\.community_checkin\.update_community_checkin_rule_use_case\.CommunityCheckinRuleService'\) as mock_service:\s+mock_service\.update_community_rule\.side_effect = Exception\('数据库错误'\)",
            "with patch.object(use_case, 'checkin_rule_repository') as mock_repo:\n            mock_repo.get_by_id.side_effect = Exception('数据库错误')"
        ),
    ]

    modified = False
    for pattern, replacement in replacements:
        new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
        if new_content != content:
            modified = True
            content = new_content

    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    """主函数"""
    print("=" * 60)
    print("修复测试文件中的Service mock")
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