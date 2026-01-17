#!/usr/bin/env python3
"""
批量修复UseCase中的Repository直接实例化问题

将所有直接实例化Repository的代码替换为使用RepositoryFactory
"""
import os
import re
from pathlib import Path

# 需要修复的文件列表
FILES_TO_FIX = [
    'src/app/application/use_cases/community/search_manageable_communities_use_case.py',
    'src/app/application/use_cases/community/get_managed_communities_use_case.py',
    'src/app/application/use_cases/community/search_community_use_case.py',
    'src/app/application/use_cases/community/get_all_communities_use_case.py',
    'src/app/application/use_cases/community/join_community_use_case.py',
    'src/app/application/use_cases/community/get_available_communities_use_case.py',
    'src/app/application/use_cases/community/get_admin_list_use_case.py',
    'src/app/application/use_cases/community/list_community_users_use_case.py',
    'src/app/application/use_cases/community/check_community_permission_use_case.py',
    'src/app/application/use_cases/community/get_community_members_use_case.py',
    'src/app/application/use_cases/community/search_users_use_case.py',
    'src/app/application/use_cases/community/update_community_use_case.py',
    'src/app/application/use_cases/user/update_profile_use_case.py',
    'src/app/application/use_cases/user/merge_accounts_use_case.py',
    'src/app/application/use_cases/community/verify_user_community_access_use_case.py',
    'src/app/application/use_cases/user/upload_avatar_use_case.py',
    'src/app/application/use_cases/user/change_password_use_case.py',
]

def fix_file(filepath):
    """修复单个文件"""
    print(f"处理文件: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # 1. 添加 RepositoryFactory 导入（如果还没有）
    if 'from app.infrastructure.persistence.repository_factory import RepositoryFactory' not in content:
        # 在其他导入之后添加
        import_pattern = r'(from app\.(application|domain)\..*?import.*?\n)'
        if re.search(import_pattern, content):
            content = re.sub(
                import_pattern,
                r'\1from app.infrastructure.persistence.repository_factory import RepositoryFactory\n',
                content,
                count=1
            )
            print(f"  ✓ 添加 RepositoryFactory 导入")

    # 2. 替换 self.user_repo = UserRepository() 为 self.user_repository = RepositoryFactory.get_user_repository()
    if 'self.user_repo = UserRepository()' in content:
        content = content.replace(
            'self.user_repo = UserRepository()',
            'self.user_repository = RepositoryFactory.get_user_repository()'
        )
        print(f"  ✓ 替换 UserRepository() 实例化")

    # 3. 替换 self.community_repo = CommunityRepository() 为 self.community_repository = RepositoryFactory.get_community_repository()
    if 'self.community_repo = CommunityRepository()' in content:
        content = content.replace(
            'self.community_repo = CommunityRepository()',
            'self.community_repository = RepositoryFactory.get_community_repository()'
        )
        print(f"  ✓ 替换 CommunityRepository() 实例化")

    # 4. 替换 self.checkin_rule_repo = CheckinRuleRepository() 为 self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
    if 'self.checkin_rule_repo = CheckinRuleRepository()' in content:
        content = content.replace(
            'self.checkin_rule_repo = CheckinRuleRepository()',
            'self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()'
        )
        print(f"  ✓ 替换 CheckinRuleRepository() 实例化")

    # 5. 替换 self.event_repo = CommunityEventRepository() 为 self.community_event_repository = RepositoryFactory.get_community_event_repository()
    if 'self.event_repo = CommunityEventRepository()' in content:
        content = content.replace(
            'self.event_repo = CommunityEventRepository()',
            'self.community_event_repository = RepositoryFactory.get_community_event_repository()'
        )
        print(f"  ✓ 替换 CommunityEventRepository() 实例化")

    # 6. 替换 self.staff_repo = CommunityStaffRepository() 为 self.community_staff_repository = RepositoryFactory.get_community_staff_repository()
    if 'self.staff_repo = CommunityStaffRepository()' in content:
        content = content.replace(
            'self.staff_repo = CommunityStaffRepository()',
            'self.community_staff_repository = RepositoryFactory.get_community_staff_repository()'
        )
        print(f"  ✓ 替换 CommunityStaffRepository() 实例化")

    # 如果内容有变化，写回文件
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ 文件已更新")
    else:
        print(f"  - 文件无需修改")

def main():
    """主函数"""
    print("开始批量修复UseCase中的Repository直接实例化问题...")
    print("=" * 60)

    for filepath in FILES_TO_FIX:
        full_path = Path(filepath)
        if full_path.exists():
            fix_file(full_path)
        else:
            print(f"✗ 文件不存在: {filepath}")

    print("=" * 60)
    print("批量修复完成！")

if __name__ == '__main__':
    main()