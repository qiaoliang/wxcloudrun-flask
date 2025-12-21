#!/usr/bin/env python
"""
验证社区规则停用bug的边界情况
"""
import sys
import os
from datetime import datetime

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入必要的模块
from database import get_database, reset_all
from wxcloudrun.dao import get_db
from database.models import Community, User, CommunityCheckinRule, UserCommunityRule, CommunityStaff
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService


def test_disable_edge_cases():
    """测试规则停用的边界情况"""
    print("开始验证社区规则停用边界情况...")
    
    # 重置数据库
    reset_all()
    db = get_db()
    db.create_tables()
    
    with db.get_session() as session:
        # 创建社区
        community = Community(
            name="测试社区",
            status=1,
            created_at=datetime.now()
        )
        session.add(community)
        session.flush()
        
        # 创建工作人员用户
        staff_user = User(
            phone_number="13800000001",
            nickname="工作人员",
            role=3,  # 社区工作人员
            community_id=community.community_id,
            community_joined_at=datetime.now(),
            created_at=datetime.now()
        )
        session.add(staff_user)
        session.flush()
        
        # 添加工作人员记录
        staff_record = CommunityStaff(
            community_id=community.community_id,
            user_id=staff_user.user_id,
            role="manager",
            added_at=datetime.now()
        )
        session.add(staff_record)
        
        # 创建多个普通用户
        users = []
        for i in range(3):
            user = User(
                phone_number=f"1380000000{2+i}",
                nickname=f"用户{i+1}",
                role=2,  # 独居者
                community_id=community.community_id,
                community_joined_at=datetime.now(),
                created_at=datetime.now()
            )
            session.add(user)
            session.flush()
            users.append(user)
        
        # 创建一个已启用的社区规则
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="测试规则",
            status=1,  # 启用状态
            created_by=staff_user.user_id,
            created_at=datetime.now()
        )
        session.add(rule)
        session.commit()
        rule_id = rule.community_rule_id
        
        print(f"1. 创建了启用的规则，ID: {rule_id}")
        
        # 测试场景1：部分用户有映射记录，部分没有
        # 只为第一个用户创建映射记录
        mapping1 = UserCommunityRule(
            user_id=users[0].user_id,
            community_rule_id=rule_id,
            is_active=True,
            created_at=datetime.now()
        )
        session.add(mapping1)
        session.commit()
        
        # 验证初始状态
        print("\n2. 验证初始状态：")
        for i, user in enumerate(users):
            user_rules = UserCheckinRuleService.get_user_all_rules(user.user_id)
            user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
            if user_rule:
                print(f"   用户{i+1} - 状态: {user_rule['status']}, 标签: {user_rule['status_label']}, 激活: {user_rule['is_active_for_user']}")
        
        # 停用规则
        print("\n3. 停用规则...")
        CommunityCheckinRuleService.disable_community_rule(rule_id, staff_user.user_id)
        
        # 验证停用后的状态
        print("\n4. 验证停用后状态：")
        all_correct = True
        for i, user in enumerate(users):
            user_rules = UserCheckinRuleService.get_user_all_rules(user.user_id)
            user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
            if user_rule:
                print(f"   用户{i+1} - 状态: {user_rule['status']}, 标签: {user_rule['status_label']}, 激活: {user_rule['is_active_for_user']}")
                if not (user_rule['status'] == 0 and user_rule['status_label'] == '停用' and user_rule['is_active_for_user'] == False):
                    all_correct = False
                    print(f"     ❌ 用户{i+1}的状态不正确！")
            else:
                all_correct = False
                print(f"   ❌ 用户{i+1}看不到规则！")
        
        # 验证数据库中的映射记录
        print("\n5. 验证数据库映射记录：")
        mappings = session.query(UserCommunityRule).filter_by(community_rule_id=rule_id).all()
        for mapping in mappings:
            user = next((u for u in users if u.user_id == mapping.user_id), None)
            if user:
                print(f"   {user.nickname} - is_active: {mapping.is_active}")
                if mapping.is_active != False:
                    all_correct = False
                    print(f"     ❌ {user.nickname}的映射记录不正确！")
        
        if all_correct:
            print("\n✅ 所有测试通过！规则停用功能正常")
            return True
        else:
            print("\n❌ 存在问题！规则停用功能有bug")
            return False


if __name__ == "__main__":
    try:
        success = test_disable_edge_cases()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)