#!/usr/bin/env python3
"""
批量迁移测试文件的import语句
将旧Service导入替换为Helper或UseCase
"""
import re
import os
from pathlib import Path

# 定义import替换映射
IMPORT_REPLACEMENTS = {
    # CommunityService.has_community_permission() -> CommunityPermissionHelper
    'from wxcloudrun.community_service import CommunityService': (
        'from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper'
    ),
    'CommunityService.has_community_permission': 'CommunityPermissionHelper.has_community_permission',
    
    # CommunityStaffService._activate_new_community_rules() -> CommunityRuleHelper
    'from wxcloudrun.community_staff_service import CommunityStaffService': (
        'from app.shared.utils.community_helpers import CommunityRuleHelper'
    ),
    'CommunityStaffService._activate_new_community_rules': 'CommunityRuleHelper.activate_new_community_rules',
    
    # CommunityCheckinRuleService.get_rule_detail() -> CommunityRuleQueryHelper
    'from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService': (
        'from app.shared.utils.community_helpers import CommunityRuleQueryHelper'
    ),
    'CommunityCheckinRuleService.get_rule_detail': 'CommunityRuleQueryHelper.get_rule_detail',
    'CommunityCheckinRuleService.get_user_community_rules': 'CommunityRuleQueryHelper.get_user_community_rules',
    
    # UserCheckinRuleService -> CommunityRuleQueryHelper
    'from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService': (
        'from app.shared.utils.community_helpers import CommunityRuleQueryHelper'
    ),
    'UserCheckinRuleService.get_rule_detail': 'CommunityRuleQueryHelper.get_rule_detail',
    'UserCheckinRuleService.get_user_community_rules': 'CommunityRuleQueryHelper.get_user_community_rules',
    
    # CommunityEventService保持不变（暂时）
    # UserService保持不变（暂时）
    # random_str保持不变
    # CommunityDashboardService -> 删除（已删除）
    'from wxcloudrun.community_dashboard_service import CommunityDashboardService': (
        '# CommunityDashboardService已删除，请使用Repository'
    ),
}

# 需要迁移的测试文件列表
UNIT_TEST_FILES = [
    'tests/unit/test_community_service_get_manageable_communities.py',
    'tests/unit/test_user_service.py',
    'tests/unit/test_community_staff_service_refactor.py',
    'tests/unit/test_community_checkin_rule_service.py',
    'tests/unit/test_checkin_record_calculate_planned_time_fix.py',
    'tests/unit/test_community_management_permissions.py',
    'tests/unit/test_community_dashboard_service.py',
    'tests/unit/test_community_rule_sync.py',
    'tests/unit/test_user_service_search_ankafamily.py',
    'tests/unit/test_community_rule_enable_bug_fix.py',
    'tests/unit/test_community_event_service.py',
    'tests/unit/test_manager_access_community.py',
    'tests/unit/test_user_update_parametrized.py',
    'tests/unit/test_community_staff_service.py',
    'tests/unit/test_community_location.py',
    'tests/unit/test_community_rule_status.py',
    'tests/unit/test_user_community_rule_switching.py',
]

INTEGRATION_TEST_FILES = [
    'tests/integration/conftest.py',
    'tests/integration/test_close_event.py',
    'tests/integration/test_community_applications.py',
    'tests/integration/test_community_create.py',
    'tests/integration/test_community_remove_user.py',
    'tests/integration/test_events_operations.py',
    'tests/integration/test_today_schedule.py',
]

TEST_FILES = UNIT_TEST_FILES + INTEGRATION_TEST_FILES

def migrate_test_file(file_path: str):
    """
    迁移单个测试文件的import语句
    
    Args:
        file_path: 测试文件路径
    """
    print(f"处理文件: {file_path}")
    
    if not os.path.exists(file_path):
        print(f"  ⚠️  文件不存在，跳过")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # 执行替换
    for old_import, new_import in IMPORT_REPLACEMENTS.items():
        if old_import in content:
            content = content.replace(old_import, new_import)
            print(f"  ✓ 替换: {old_import} -> {new_import}")
    
    # 如果内容有变化，写回文件
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 已更新文件")
    else:
        print(f"  ℹ️  无需修改")

def main():
    """主函数"""
    print("=" * 60)
    print("批量迁移测试文件import语句")
    print("=" * 60)
    
    # 切换到backend目录
    backend_dir = Path(__file__).parent.parent
    os.chdir(backend_dir)
    
    print(f"工作目录: {os.getcwd()}")
    print()
    
    # 迁移所有测试文件
    for test_file in TEST_FILES:
        migrate_test_file(test_file)
        print()
    
    print("=" * 60)
    print("迁移完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()