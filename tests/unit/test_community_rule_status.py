"""
测试社区规则启用/停用功能
验证停用的规则对用户可见但不影响打卡
"""
import pytest
from datetime import datetime, date
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from database.flask_models import CommunityCheckinRule, UserCommunityRule, User, Community, CommunityStaff


def test_community_rule_disable_enable(test_session):
    """测试社区规则停用和启用功能"""
    # 创建测试社区
    community = Community(
        name="测试社区_状态测试",
        description="用于测试的社区",
        status=1
    )
    test_session.add(community)
    test_session.flush()
    
    # 创建测试用户（社区主管）
    user = User(
        wechat_openid="test_openid_status",
        nickname="测试用户",
        phone_number="13800138000",
        role=3,  # 社区主管
        community_id=community.community_id
    )
    test_session.add(user)
    test_session.flush()
    
    # 添加社区工作人员记录
    staff_record = CommunityStaff(
        community_id=community.community_id,
        user_id=user.user_id,
        role="manager",
        added_at=datetime.now()
    )
    test_session.add(staff_record)
    
    # 创建社区规则
    rule = CommunityCheckinRule(
        community_id=community.community_id,
        rule_name="测试规则",
        frequency_type=0,
        time_slot_type=4,
        week_days=127,
        status=1,  # 初始启用
        created_by=user.user_id
    )
    test_session.add(rule)
    test_session.flush()
    
    # 创建用户规则映射
    mapping = UserCommunityRule(
        user_id=user.user_id,
        community_rule_id=rule.community_rule_id,
        is_active=True
    )
    test_session.add(mapping)
    test_session.commit()
    
    user_id = user.user_id
    rule_id = rule.community_rule_id
    
    # 1. 验证初始状态：规则启用且对用户可见
    all_rules = UserCheckinRuleService.get_user_all_rules(user_id)
    community_rules = [r for r in all_rules if r['rule_source'] == 'community']
    assert len(community_rules) == 1
    assert community_rules[0]['is_active_for_user'] == True
    assert community_rules[0]['status_label'] == '启用'
    
    # 2. 停用规则
    CommunityCheckinRuleService.disable_community_rule(rule_id, user_id)
    
    # 3. 验证停用后状态：规则对用户仍可见但标记为停用
    all_rules = UserCheckinRuleService.get_user_all_rules(user_id)
    community_rules = [r for r in all_rules if r['rule_source'] == 'community']
    assert len(community_rules) == 1
    assert community_rules[0]['is_active_for_user'] == False
    assert community_rules[0]['status_label'] == '停用'
    
    # 4. 验证停用的规则不出现在今日打卡计划中
    today_plan_result = UserCheckinRuleService.get_today_checkin_plan(user_id)
    today_plan = today_plan_result.get('items', []) if isinstance(today_plan_result, dict) else []
    community_plan_items = [item for item in today_plan if item.get('rule_source') == 'community']
    assert len(community_plan_items) == 0
    
    # 5. 重新启用规则
    CommunityCheckinRuleService.enable_community_rule(rule_id, user_id)
    
    # 6. 验证启用后状态：规则重新激活
    all_rules = UserCheckinRuleService.get_user_all_rules(user_id)
    community_rules = [r for r in all_rules if r['rule_source'] == 'community']
    assert len(community_rules) == 1
    assert community_rules[0]['is_active_for_user'] == True
    assert community_rules[0]['status_label'] == '启用'
    
    # 7. 验证启用的规则重新出现在今日打卡计划中
    today_plan_result = UserCheckinRuleService.get_today_checkin_plan(user_id)
    today_plan = today_plan_result.get('items', []) if isinstance(today_plan_result, dict) else []
    community_plan_items = [item for item in today_plan if item.get('rule_source') == 'community']
    assert len(community_plan_items) == 1


def test_user_cannot_edit_disabled_rules(test_session):
    """测试用户不能编辑停用的社区规则"""
    # 创建测试社区
    community = Community(
        name="测试社区_编辑测试",
        description="用于测试的社区",
        status=1
    )
    test_session.add(community)
    test_session.flush()
    
    # 创建测试用户（社区主管）
    user = User(
        wechat_openid="test_openid_edit",
        nickname="测试用户",
        phone_number="13800138001",
        role=3,  # 社区主管
        community_id=community.community_id
    )
    test_session.add(user)
    test_session.flush()
    
    # 添加社区工作人员记录
    staff_record = CommunityStaff(
        community_id=community.community_id,
        user_id=user.user_id,
        role="manager",
        added_at=datetime.now()
    )
    test_session.add(staff_record)
    
    # 创建社区规则
    rule = CommunityCheckinRule(
        community_id=community.community_id,
        rule_name="测试规则",
        frequency_type=0,
        time_slot_type=4,
        week_days=127,
        status=1,  # 初始启用
        created_by=user.user_id
    )
    test_session.add(rule)
    test_session.flush()
    
    # 创建用户规则映射
    mapping = UserCommunityRule(
        user_id=user.user_id,
        community_rule_id=rule.community_rule_id,
        is_active=True
    )
    test_session.add(mapping)
    test_session.commit()
    
    user_id = user.user_id
    rule_id = rule.community_rule_id
    
    # 停用规则
    CommunityCheckinRuleService.disable_community_rule(rule_id, user_id)
    
    # 验证用户不能编辑停用的规则
    all_rules = UserCheckinRuleService.get_user_all_rules(user_id)
    community_rules = [r for r in all_rules if r['rule_source'] == 'community']
    assert len(community_rules) == 1
    assert community_rules[0]['is_editable'] == False


def test_multiple_users_see_same_rule_status(test_session):
    """测试多个用户看到相同的规则状态"""
    # 创建测试社区
    community = Community(
        name="测试社区_多用户测试",
        description="用于测试的社区",
        status=1
    )
    test_session.add(community)
    test_session.flush()
    
    # 创建第一个测试用户（社区主管）
    user = User(
        wechat_openid="test_openid_multi1",
        nickname="测试用户1",
        phone_number="13800138002",
        role=3,  # 社区主管
        community_id=community.community_id
    )
    test_session.add(user)
    test_session.flush()
    
    # 添加社区工作人员记录
    staff_record = CommunityStaff(
        community_id=community.community_id,
        user_id=user.user_id,
        role="manager",
        added_at=datetime.now()
    )
    test_session.add(staff_record)
    
    # 创建社区规则
    rule = CommunityCheckinRule(
        community_id=community.community_id,
        rule_name="测试规则",
        frequency_type=0,
        time_slot_type=4,
        week_days=127,
        status=1,  # 初始启用
        created_by=user.user_id
    )
    test_session.add(rule)
    test_session.flush()
    
    # 为第一个用户创建规则映射
    mapping1 = UserCommunityRule(
        user_id=user.user_id,
        community_rule_id=rule.community_rule_id,
        is_active=True
    )
    test_session.add(mapping1)
    
    # 创建第二个用户
    user2 = User(
        wechat_openid="test_openid_multi2",
        nickname="测试用户2",
        phone_number="13800138003",
        role=1,
        community_id=community.community_id
    )
    test_session.add(user2)
    test_session.flush()
    
    # 为第二个用户创建规则映射
    mapping2 = UserCommunityRule(
        user_id=user2.user_id,
        community_rule_id=rule.community_rule_id,
        is_active=True
    )
    test_session.add(mapping2)
    test_session.commit()
    
    user_id = user.user_id
    user2_id = user2.user_id
    rule_id = rule.community_rule_id
    
    # 停用规则
    CommunityCheckinRuleService.disable_community_rule(rule_id, user_id)
    
    # 验证两个用户都看到规则为停用状态
    for uid in [user_id, user2_id]:
        all_rules = UserCheckinRuleService.get_user_all_rules(uid)
        community_rules = [r for r in all_rules if r['rule_source'] == 'community']
        assert len(community_rules) == 1
        assert community_rules[0]['is_active_for_user'] == False
        assert community_rules[0]['status_label'] == '停用'

