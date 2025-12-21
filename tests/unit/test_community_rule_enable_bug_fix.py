"""
测试社区规则启用后用户视图的正确性
验证bug修复：当社区规则从'停用'改为'启用'后，用户应该能看到规则为'启用'状态
"""
import pytest
from datetime import datetime
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from wxcloudrun.dao import get_db
from database.models import Community, User, CommunityCheckinRule, UserCommunityRule, CommunityStaff


class TestCommunityRuleEnableBugFix:
    """测试社区规则启用bug修复"""
    
    def test_rule_enable_user_view_sync(self, test_data):
        """测试规则启用后用户视图同步更新"""
        # 准备测试数据
        community = test_data['community']
        staff_user = test_data['staff_user']
        regular_user = test_data['regular_user']
        
        # 创建一个停用的社区规则
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="测试规则",
            rule_content="测试内容",
            status=0,  # 停用状态
            created_by=staff_user.user_id,
            created_at=datetime.now()
        )
        
        db = get_db()
        with db.get_session() as session:
            session.add(rule)
            session.commit()
            rule_id = rule.community_rule_id
            
            # 验证初始状态：用户看到的规则是停用状态
            user_rules = UserCheckinRuleService.get_user_all_rules(regular_user.user_id)
            user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
            
            assert user_rule is not None, "用户应该能看到社区规则"
            assert user_rule['status'] == 0, "规则初始应该是停用状态"
            assert user_rule['status_label'] == '停用', "规则应该显示为停用"
            assert user_rule['is_active_for_user'] == False, "规则对用户应该是未激活状态"
            
            # 启用规则
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
            
            assert user_rule is not None, "用户应该仍能看到社区规则"
            assert user_rule['status'] == 1, "规则应该是启用状态"
            assert user_rule['status_label'] == '启用', "规则应该显示为启用"
            assert user_rule['is_active_for_user'] == True, "规则对用户应该是激活状态"
    
    def test_missing_mapping_auto_creation(self, test_data):
        """测试缺失映射记录的自动创建"""
        # 准备测试数据
        community = test_data['community']
        staff_user = test_data['staff_user']
        regular_user = test_data['regular_user']
        
        # 创建一个已启用的社区规则（但不创建用户映射）
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="测试规则2",
            rule_content="测试内容2",
            status=1,  # 启用状态
            enabled_by=staff_user.user_id,
            enabled_at=datetime.now(),
            created_by=staff_user.user_id,
            created_at=datetime.now()
        )
        
        db = get_db()
        with db.get_session() as session:
            session.add(rule)
            session.commit()
            rule_id = rule.community_rule_id
            
            # 确保没有用户映射记录
            mapping = session.query(UserCommunityRule).filter_by(
                user_id=regular_user.user_id,
                community_rule_id=rule_id
            ).first()
            assert mapping is None, "初始不应该有用户映射记录"
            
            # 用户查询规则时，应该自动创建缺失的映射记录
            user_rules = UserCheckinRuleService.get_user_all_rules(regular_user.user_id)
            user_rule = next((r for r in user_rules if r.get('community_rule_id') == rule_id), None)
            
            assert user_rule is not None, "用户应该能看到社区规则"
            assert user_rule['status'] == 1, "规则应该是启用状态"
            assert user_rule['status_label'] == '启用', "规则应该显示为启用"
            assert user_rule['is_active_for_user'] == True, "规则对用户应该是激活状态"
            
            # 验证映射记录已被自动创建
            mapping = session.query(UserCommunityRule).filter_by(
                user_id=regular_user.user_id,
                community_rule_id=rule_id
            ).first()
            assert mapping is not None, "应该自动创建用户映射记录"
            assert mapping.is_active == True, "映射记录应该是激活状态"


@pytest.fixture
def test_data():
    """准备测试数据"""
    db = get_db()
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
            phone="13800000001",
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
            created_at=datetime.now()
        )
        session.add(staff_record)
        
        # 创建普通用户
        regular_user = User(
            phone="13800000002",
            nickname="普通用户",
            role=2,  # 独居者
            community_id=community.community_id,
            community_joined_at=datetime.now(),
            created_at=datetime.now()
        )
        session.add(regular_user)
        
        session.commit()
        
        return {
            'community': community,
            'staff_user': staff_user,
            'regular_user': regular_user
        }