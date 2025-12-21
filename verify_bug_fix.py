#!/usr/bin/env python
"""
验证社区规则启用bug修复的脚本
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


def test_bug_fix():
    """测试bug修复"""
    print("开始验证社区规则启用bug修复...")
    
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
        
        # 创建普通用户
        regular_user = User(
            phone_number="13800000002",
            nickname="普通用户",
            role=2,  # 独居者
            community_id=community.community_id,
            community_joined_at=datetime.now(),
            created_at=datetime.now()
        )
        session.add(regular_user)
        session.flush()
        
        # 创建一个停用的社区规则
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="测试规则",
            status=0,  # 停用状态
            created_by=staff_user.user_id,
            created_at=datetime.now()
        )
        session.add(rule)
        session.commit()
        rule_id = rule.community_rule_id
        
        print(f"1. 创建了停用的规则，ID: {rule_id}")
        
        # 验证初始状态：用户看到的规则是停用状态
        user_rules = UserCheckinRuleService.get_user_all_rules(regular_user.user_id)
        user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
        
        if user_rule:
            print(f"2. 初始状态 - 规则状态: {user_rule['status']}, 标签: {user_rule['status_label']}, 激活: {user_rule['is_active_for_user']}")
            assert user_rule['status'] == 0, "规则初始应该是停用状态"
            assert user_rule['status_label'] == '停用', "规则应该显示为停用"
            assert user_rule['is_active_for_user'] == False, "规则对用户应该是未激活状态"
        else:
            print("2. 错误：用户看不到规则")
            return False
        
        # 启用规则
        print("3. 启用规则...")
        CommunityCheckinRuleService.enable_community_rule(rule_id, staff_user.user_id)
        
        # 验证规则状态已更新
        session.refresh(rule)
        assert rule.status == 1, "规则应该是启用状态"
        
        # 验证用户映射记录已创建
        mapping = session.query(UserCommunityRule).filter_by(
            user_id=regular_user.user_id,
            community_rule_id=rule_id
        ).first()
        assert mapping is not None, "应该存在用户规则映射记录"
        assert mapping.is_active == True, "映射记录应该是激活状态"
        
        # 验证用户看到的规则已更新为启用状态
        user_rules = UserCheckinRuleService.get_user_all_rules(regular_user.user_id)
        user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
        
        if user_rule:
            print(f"4. 启用后状态 - 规则状态: {user_rule['status']}, 标签: {user_rule['status_label']}, 激活: {user_rule['is_active_for_user']}")
            if user_rule['status'] == 1 and user_rule['status_label'] == '启用' and user_rule['is_active_for_user'] == True:
                print("✅ Bug修复成功！规则启用后用户视图正确更新")
                return True
            else:
                print("❌ Bug修复失败！规则启用后用户视图未正确更新")
                return False
        else:
            print("❌ 错误：启用后用户看不到规则")
            return False


if __name__ == "__main__":
    try:
        success = test_bug_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)