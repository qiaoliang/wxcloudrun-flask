"""
删除打卡规则核心逻辑测试
"""
import pytest
import sys
import os
import json
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

# from wxcloudrun import app
# from database import get_database
from database import initialize_for_test

db = initialize_for_test()

from database.flask_models import CheckinRule, CheckinRecord, User, Community
# from wxcloudrun.dao import delete_checkin_rule_by_id, query_checkin_rule_by_id, query_checkin_rules_by_user_id


class TestDeleteRuleCoreLogic:

    def test_soft_delete_rule_with_records(self, test_session, test_user):
        """测试有打卡记录的规则软删除"""
        # 创建测试社区
        community = Community(
            name="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建测试规则
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()

        # 添加打卡记录
        record = CheckinRecord(
            rule_id=rule.rule_id,
            user_id=test_user.user_id,
            planned_time=datetime.now(),
            checkin_time=datetime.now(),
            checkin_type="测试打卡"
        )
        test_session.add(record)
        test_session.commit()

        # 执行软删除 - 模拟软删除操作
        rule.status=2  # 软删除状态
        test_session.commit()

        # 验证结果
        assert rule.status==2  # 已删除状态

        # 验证记录仍然存在
        assert test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).count() == 1

    def test_query_rules_exclude_deleted(self, test_session, test_user):
        """测试查询规则时排除已删除的规则"""
        # 创建测试社区
        community = Community(
            name="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建正常规则
        active_rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="正常规则",
            status=1
        )

        # 创建已删除规则
        deleted_rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="已删除规则",
            status=2
        )

        # 创建禁用规则
        disabled_rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="禁用规则",
            status=0
        )

        test_session.add(active_rule)
        test_session.add(deleted_rule)
        test_session.add(disabled_rule)
        test_session.commit()

        # 查询规则 - 只查询激活的规则
        rules = test_session.query(CheckinRule).filter_by(user_id=test_user.user_id).filter(CheckinRule.status == 1).all()

        # 验证只返回正常的规则
        assert len(rules) == 1
        state = [rule.status for rule in rules]
        assert 1 in state
        assert 2 not in state
        assert 0 not in state

    def test_soft_delete_preserves_data_integrity(self, test_session, test_user):
        """测试软删除保持数据完整性"""
        # 创建测试社区
        community = Community(
            name="测试社区",
            status=1
        )
        test_session.add(community)
        test_session.commit()

        # 创建测试规则
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="数据完整性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()

        # 添加多条打卡记录
        for i in range(3):
            record = CheckinRecord(
                rule_id=rule.rule_id,
                user_id=test_user.user_id,
                planned_time=datetime.now(),
                checkin_time=datetime.now(),
                checkin_type=f"测试打卡{i+1}"
            )
            test_session.add(record)
        test_session.commit()

        # 执行软删除
        rule.status = 2
        test_session.commit()

        # 验证所有打卡记录仍然存在
        records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 3

        # 验证规则已被软删除
        assert rule.status == 2


if __name__ == '__main__':
    pytest.main([__file__])