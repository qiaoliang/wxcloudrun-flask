"""
用户社区切换规则管理测试用例
测试用户在不同社区间切换时，规则的正确停用和激活逻辑
"""

import pytest
import logging
import random
import string
from datetime import datetime
from wxcloudrun.community_staff_service import CommunityStaffService
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from database.flask_models import User, Community, CommunityCheckinRule, UserCommunityRule, CheckinRule
from wxcloudrun.dao import get_db

logger = logging.getLogger(__name__)


def generate_random_community_name():
    """生成随机的社区名称"""
    return f"测试社区_{''.join(random.choices(string.ascii_letters, k=8))}"


class TestUserCommunityRuleSwitching:
    """用户社区规则切换测试类"""

    @pytest.fixture
    def setup_test_data(self):
        """设置测试数据"""
        import time
        import uuid

        db = get_db()
        with db.get_session() as session:
            # 生成唯一的标识符
            unique_id = str(int(time.time()))[-6:]

            # 创建测试用户
            test_user = User(
                nickname=f"测试用户_{unique_id}",
                phone_number=f"1380013{unique_id}",
                role=1,
                status=1,
                community_id=None
            )
            session.add(test_user)
            session.flush()  # 获取用户ID

            # 创建测试社区A
            community_a = Community(
                name=generate_random_community_name(),
                description=f"测试社区A描述_{unique_id}",
                status=1
            )
            session.add(community_a)
            session.flush()

            # 创建测试社区B
            community_b = Community(
                name=generate_random_community_name(),
                description=f"测试社区B描述_{unique_id}",
                status=1
            )
            session.add(community_b)
            session.flush()

            # 为社区A创建规则
            community_a_rule1 = CommunityCheckinRule(
                community_id=community_a.community_id,
                rule_name="社区A规则1",
                frequency_type=1,
                time_slot_type=1,
                status=1,
                created_by=test_user.user_id
            )
            community_a_rule2 = CommunityCheckinRule(
                community_id=community_a.community_id,
                rule_name="社区A规则2",
                frequency_type=2,
                time_slot_type=2,
                status=1,
                created_by=test_user.user_id
            )
            session.add_all([community_a_rule1, community_a_rule2])

            # 为社区B创建规则
            community_b_rule1 = CommunityCheckinRule(
                community_id=community_b.community_id,
                rule_name="社区B规则1",
                frequency_type=1,
                time_slot_type=1,
                status=1,
                created_by=test_user.user_id
            )
            community_b_rule2 = CommunityCheckinRule(
                community_id=community_b.community_id,
                rule_name="社区B规则2",
                frequency_type=2,
                time_slot_type=2,
                status=0,  # 停用状态
                created_by=test_user.user_id
            )
            session.add_all([community_b_rule1, community_b_rule2])

            # 为用户创建个人规则
            personal_rule = CheckinRule(
                user_id=test_user.user_id,  # 更新字段名
                community_id=community_a.community_id,  # 添加必需的community_id
                rule_name="个人规则1",
                frequency_type=1,
                time_slot_type=1,
                status=1
            )
            session.add(personal_rule)

            session.commit()

            # 返回测试数据
            return {
                'user_id': test_user.user_id,
                'community_a_id': community_a.community_id,
                'community_b_id': community_b.community_id,
                'community_a_rule1_id': community_a_rule1.community_rule_id,
                'community_a_rule2_id': community_a_rule2.community_rule_id,
                'community_b_rule1_id': community_b_rule1.community_rule_id,
                'community_b_rule2_id': community_b_rule2.community_rule_id,
                'personal_rule_id': personal_rule.rule_id
            }

    def test_initial_community_assignment(self, setup_test_data, test_app):
        """测试初始社区分配时的规则激活"""
        user_id = setup_test_data['user_id']
        community_a_id = setup_test_data['community_a_id']

        # 在Flask应用上下文中执行
        with test_app.app_context():
            # 用户初始分配到社区A
            result = CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=None,
                new_community_id=community_a_id
            )

        # 验证结果
        assert result['success'] is True
        assert result['deactivated_count'] == 0  # 没有旧规则需要停用
        assert result['activated_count'] == 2    # 社区A有2个启用规则

        # 验证数据库状态
        db = get_db()
        with db.get_session() as session:
            active_mappings = session.query(UserCommunityRule).filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            assert len(active_mappings) == 2
            # 确认是社区A的规则
            for mapping in active_mappings:
                rule = session.query(CommunityCheckinRule).get(mapping.community_rule_id)
                assert rule.community_id == community_a_id

    def test_community_switching(self, setup_test_data, test_app):
        """测试从社区A切换到社区B的规则管理"""
        user_id = setup_test_data['user_id']
        community_a_id = setup_test_data['community_a_id']
        community_b_id = setup_test_data['community_b_id']

        # 在Flask应用上下文中执行
        with test_app.app_context():
            # 步骤1: 用户先加入社区A
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=None,
                new_community_id=community_a_id
            )

            # 步骤2: 切换到社区B
            result = CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=community_a_id,
                new_community_id=community_b_id
            )

        # 验证切换结果
        assert result['success'] is True
        assert result['deactivated_count'] == 2    # 停用社区A的2个规则
        assert result['activated_count'] == 1      # 激活社区B的1个启用规则（社区B规则2是停用状态）

        # 验证数据库状态
        db = get_db()
        with db.get_session() as session:
            # 检查社区A规则是否已停用
            a_mappings = session.query(UserCommunityRule).join(CommunityCheckinRule).filter(
                UserCommunityRule.user_id == user_id,
                CommunityCheckinRule.community_id == community_a_id
            ).all()

            for mapping in a_mappings:
                assert mapping.is_active is False

            # 检查社区B规则状态
            b_mappings = session.query(UserCommunityRule).join(CommunityCheckinRule).filter(
                UserCommunityRule.user_id == user_id,
                CommunityCheckinRule.community_id == community_b_id
            ).all()

            # 应该只有社区B规则1是激活的（因为规则2本身是停用状态）
            active_b_rules = [m for m in b_mappings if m.is_active]
            assert len(active_b_rules) == 1

            # 验证是社区B规则1
            active_rule = session.query(CommunityCheckinRule).get(active_b_rules[0].community_rule_id)
            assert active_rule.community_id == community_b_id
            assert active_rule.rule_name == "社区B规则1"

    def test_personal_rules_unchanged(self, setup_test_data, test_app):
        """测试个人规则在社区切换时不受影响"""
        user_id = setup_test_data['user_id']
        community_a_id = setup_test_data['community_a_id']
        community_b_id = setup_test_data['community_b_id']
        personal_rule_id = setup_test_data['personal_rule_id']

        # 在Flask应用上下文中执行
        with test_app.app_context():
            # 用户加入社区A
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=None,
                new_community_id=community_a_id
            )

            # 切换到社区B
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=community_a_id,
                new_community_id=community_b_id
            )

        # 验证个人规则状态
        db = get_db()
        with db.get_session() as session:
            personal_rule = session.query(CheckinRule).get(personal_rule_id)
            assert personal_rule is not None
            assert personal_rule.status == 1  # 个人规则状态未改变
            assert personal_rule.user_id == user_id  # 更新字段名

    def test_get_user_rules_after_switching(self, setup_test_data, test_app):
        """测试社区切换后获取用户规则列表的正确性"""
        user_id = setup_test_data['user_id']
        community_a_id = setup_test_data['community_a_id']
        community_b_id = setup_test_data['community_b_id']
    
        # 在Flask应用上下文中执行
        with test_app.app_context():
            # 用户加入社区A
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=None,
                new_community_id=community_a_id
            )
    
            # 获取用户规则列表
            rules_after_a = UserCheckinRuleService.get_user_all_rules(user_id)
    
            # 验证规则列表
            community_rules = [r for r in rules_after_a if r['rule_source'] == 'community']
            personal_rules = [r for r in rules_after_a if r['rule_source'] == 'personal']
    
            assert len(community_rules) == 2  # 社区A的2个规则
            assert len(personal_rules) == 1  # 1个个人规则
    
            # 验证社区规则都来自社区A
            db = get_db()
            with db.get_session() as session:
                community_a = session.query(Community).get(community_a_id)
                community_a_name = community_a.name
    
            for rule in community_rules:
                assert community_a_name in rule['source_label']
                assert rule['is_active_for_user'] is True
    
            # 切换到社区B
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=community_a_id,
                new_community_id=community_b_id
            )
    
            # 再次获取用户规则列表
            rules_after_b = UserCheckinRuleService.get_user_all_rules(user_id)
    
            community_rules_b = [r for r in rules_after_b if r['rule_source'] == 'community']
            personal_rules_b = [r for r in rules_after_b if r['rule_source'] == 'personal']
    
            # 验证规则列表更新
            active_community_rules_b = [r for r in community_rules_b if r['is_active_for_user']]
            assert len(active_community_rules_b) == 1  # 只有社区B的1个启用规则对用户激活
            assert len(personal_rules_b) == 1  # 个人规则数量不变
    
            # 验证社区规则来自社区B
            with db.get_session() as session:
                community_b = session.query(Community).get(community_b_id)
                community_b_name = community_b.name
    
            for rule in active_community_rules_b:
                assert community_b_name in rule['source_label']
                assert rule['is_active_for_user'] is True
    def test_switch_back_to_previous_community(self, setup_test_data, test_app):
        """测试切换回原社区时规则的重新激活"""
        user_id = setup_test_data['user_id']
        community_a_id = setup_test_data['community_a_id']
        community_b_id = setup_test_data['community_b_id']

        # 在Flask应用上下文中执行
        with test_app.app_context():
            # 用户加入社区A
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=None,
                new_community_id=community_a_id
            )

            # 切换到社区B
            CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=community_a_id,
                new_community_id=community_b_id
            )

            # 再切换回社区A
            result = CommunityStaffService.handle_user_community_change(
                user_id=user_id,
                old_community_id=community_b_id,
                new_community_id=community_a_id
            )

        # 验证切换结果
        assert result['success'] is True
        assert result['deactivated_count'] == 1    # 停用社区B的1个规则
        assert result['activated_count'] == 2      # 重新激活社区A的2个规则

        # 验证最终状态
        db = get_db()
        with db.get_session() as session:
            active_mappings = session.query(UserCommunityRule).filter_by(
                user_id=user_id,
                is_active=True
            ).all()

            assert len(active_mappings) == 2
            # 确认都是社区A的规则
            for mapping in active_mappings:
                rule = session.query(CommunityCheckinRule).get(mapping.community_rule_id)
                assert rule.community_id == community_a_id


if __name__ == '__main__':
    pytest.main([__file__])