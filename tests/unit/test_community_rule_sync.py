"""
测试用户加入社区时的规则同步功能
"""
import pytest
from datetime import datetime
from database.flask_models import db, User, Community, CommunityApplication, CommunityCheckinRule, UserCommunityRule
from wxcloudrun.community_service import CommunityService
from wxcloudrun.community_staff_service import CommunityStaffService


class TestCommunityRuleSync:
    """测试社区规则同步功能"""

    def test_process_application_syncs_rules(self, test_session):
        """测试批准社区申请时同步规则"""
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="测试社区描述",
            location="测试地点",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建社区打卡规则
        rule1 = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="早起打卡",
            custom_time=datetime.strptime("07:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=1,
            created_by=1
        )
        rule2 = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="晚餐打卡",
            custom_time=datetime.strptime("18:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=1,
            created_by=1
        )
        test_session.add_all([rule1, rule2])
        test_session.commit()

        # 创建测试用户
        user = User(
            phone_number="13800138000",
            nickname="测试用户",
            role=0
        )
        test_session.add(user)
        test_session.commit()

        # 创建社区申请
        application = CommunityApplication(
            user_id=user.user_id,
            target_community_id=community.community_id,
            status=1,
            reason="想加入这个社区"
        )
        test_session.add(application)
        test_session.commit()

        # 批准申请
        result = CommunityService.process_application(
            application.application_id,
            approve=True,
            processor_id=1
        )

        # 验证规则同步
        user_mappings = test_session.query(UserCommunityRule).filter_by(
            user_id=user.user_id,
            is_active=True
        ).all()

        assert len(user_mappings) == 2, f"应该有2个激活的规则，实际有{len(user_mappings)}个"

        rule_ids = {mapping.community_rule_id for mapping in user_mappings}
        assert rule1.community_rule_id in rule_ids, "规则1应该被同步"
        assert rule2.community_rule_id in rule_ids, "规则2应该被同步"

    def test_add_users_to_community_syncs_rules(self, test_session):
        """测试批量添加用户到社区时同步规则"""
        # 创建测试社区
        community = Community(
            name="测试社区2",
            description="测试社区描述2",
            location="测试地点2",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建社区打卡规则
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="午餐打卡",
            custom_time=datetime.strptime("12:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=1,
            created_by=1
        )
        test_session.add(rule)
        test_session.commit()

        # 创建测试用户
        user1 = User(
            phone_number="13800138001",
            nickname="测试用户1",
            role=0
        )
        user2 = User(
            phone_number="13800138002",
            nickname="测试用户2",
            role=0
        )
        test_session.add_all([user1, user2])
        test_session.commit()

        # 批量添加用户到社区
        result = CommunityService.add_users_to_community(
            community.community_id,
            [user1.user_id, user2.user_id],
            operator_id=1
        )

        # 验证规则同步
        for user in [user1, user2]:
            user_mappings = test_session.query(UserCommunityRule).filter_by(
                user_id=user.user_id,
                is_active=True
            ).all()

            assert len(user_mappings) == 1, f"用户{user.user_id}应该有1个激活的规则，实际有{len(user_mappings)}个"
            assert user_mappings[0].community_rule_id == rule.community_rule_id, "应该同步正确的规则"

    def test_rule_sync_with_existing_mappings(self, test_session):
        """测试规则同步时处理已存在的映射"""
        # 创建测试社区
        community = Community(
            name="测试社区3",
            description="测试社区描述3",
            location="测试地点3",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建社区打卡规则
        rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="睡前打卡",
            custom_time=datetime.strptime("22:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=1,
            created_by=1
        )
        test_session.add(rule)
        test_session.commit()

        # 创建测试用户
        user = User(
            phone_number="13800138003",
            nickname="测试用户3",
            role=0
        )
        test_session.add(user)
        test_session.commit()

        # 创建已存在的停用映射
        existing_mapping = UserCommunityRule(
            user_id=user.user_id,
            community_rule_id=rule.community_rule_id,
            is_active=False
        )
        test_session.add(existing_mapping)
        test_session.commit()

        # 批量添加用户到社区
        result = CommunityService.add_users_to_community(
            community.community_id,
            [user.user_id],
            operator_id=1
        )

        # 验证规则同步应该重新激活已存在的映射
        user_mappings = test_session.query(UserCommunityRule).filter_by(
            user_id=user.user_id,
            community_rule_id=rule.community_rule_id,
            is_active=True
        ).all()

        assert len(user_mappings) == 1, "应该重新激活已存在的映射"
        assert user_mappings[0].mapping_id == existing_mapping.mapping_id, "应该使用已存在的映射记录"

    def test_rule_sync_with_inactive_rules(self, test_session):
        """测试只同步启用的规则"""
        # 创建测试社区
        community = Community(
            name="测试社区4",
            description="测试社区描述4",
            location="测试地点4",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建启用的规则
        active_rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="启用规则",
            custom_time=datetime.strptime("10:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=1,
            created_by=1
        )

        # 创建停用的规则
        inactive_rule = CommunityCheckinRule(
            community_id=community.community_id,
            rule_name="停用规则",
            custom_time=datetime.strptime("15:00:00", "%H:%M:%S").time(),
            frequency_type=0,
            status=2,  # 停用状态
            created_by=1
        )
        test_session.add_all([active_rule, inactive_rule])
        test_session.commit()

        # 创建测试用户
        user = User(
            phone_number="13800138004",
            nickname="测试用户4",
            role=0
        )
        test_session.add(user)
        test_session.commit()

        # 批量添加用户到社区
        result = CommunityService.add_users_to_community(
            community.community_id,
            [user.user_id],
            operator_id=1
        )

        # 验证只同步启用的规则
        user_mappings = test_session.query(UserCommunityRule).filter_by(
            user_id=user.user_id,
            is_active=True
        ).all()

        assert len(user_mappings) == 1, "应该只同步1个启用的规则"
        assert user_mappings[0].community_rule_id == active_rule.community_rule_id, "应该同步启用的规则"

        # 验证停用的规则没有被同步
        inactive_mapping = test_session.query(UserCommunityRule).filter_by(
            user_id=user.user_id,
            community_rule_id=inactive_rule.community_rule_id
        ).first()
        assert inactive_mapping is None, "停用的规则不应该被同步"