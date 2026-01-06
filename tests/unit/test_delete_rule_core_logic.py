"""
删除打卡规则核心逻辑测试
遵循测试反模式原则：测试真实业务行为，而非 mock 行为或实现细节
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import CheckinRule, CheckinRecord, User, Community
from wxcloudrun.checkin_rule_service import CheckinRuleService
from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
from test_constants import TEST_CONSTANTS
from hashlib import sha256


class TestDeleteRuleCoreLogic:
    """测试删除打卡规则的核心逻辑"""

    def test_delete_rule_sets_correct_timestamp(self, test_session):
        """测试删除规则时设置正确的时间戳"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_delete_rule_timestamp")
        openid = generate_unique_openid(phone_number, "test_delete_rule_timestamp")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        user = User(
            nickname=generate_unique_nickname("test_delete_rule_timestamp"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建测试社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("timestamp"),
            description=TEST_CONSTANTS.generate_community_description("timestamp"),
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建测试规则
        rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="时间戳测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # 记录删除前的时间
        before_delete = datetime.now()

        # 执行删除（通过业务逻辑层）
        result = CheckinRuleService.delete_rule(rule.rule_id, user.user_id)

        # 验证删除成功
        assert result is True

        # 重新查询验证状态
        deleted_rule = test_session.get(CheckinRule, rule.rule_id)
        assert deleted_rule.status == 2

        # 验证 updated_at 时间戳被更新
        assert deleted_rule.updated_at is not None
        time_diff = deleted_rule.updated_at - before_delete
        assert time_diff.total_seconds() < 5  # 应该在5秒内

    def test_delete_rule_idempotency(self, test_session):
        """测试删除规则的可重复性 - 验证业务逻辑允许重复调用删除操作"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_delete_rule_idempotency")
        openid = generate_unique_openid(phone_number, "test_delete_rule_idempotency")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        user = User(
            nickname=generate_unique_nickname("test_delete_rule_idempotency"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建测试社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("idempotency"),
            description=TEST_CONSTANTS.generate_community_description("idempotency"),
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建测试规则
        rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="幂等性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # 第一次删除
        result1 = CheckinRuleService.delete_rule(rule.rule_id, user.user_id)
        assert result1 is True

        # 重新查询验证状态
        rule_after_first_delete = test_session.get(CheckinRule, rule.rule_id)
        assert rule_after_first_delete.status == 2

        # 等待一小段时间
        import time
        time.sleep(0.1)

        # 第二次删除（模拟再次调用删除操作）
        # 业务逻辑允许重复删除，状态保持不变
        result2 = CheckinRuleService.delete_rule(rule.rule_id, user.user_id)
        assert result2 is True

        # 验证状态保持不变
        rule_after_second_delete = test_session.get(CheckinRule, rule.rule_id)
        assert rule_after_second_delete.status == 2
        
        # 验证 updated_at 时间戳被更新（业务逻辑的真实行为）
        assert rule_after_second_delete.updated_at is not None
        assert rule_after_second_delete.updated_at >= rule_after_first_delete.updated_at

    def test_delete_rule_with_various_record_states(self, test_session):
        """测试删除包含各种状态记录的规则 - 验证业务逻辑不影响关联记录"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_delete_rule_various_states")
        openid = generate_unique_openid(phone_number, "test_delete_rule_various_states")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        user = User(
            nickname=generate_unique_nickname("test_delete_rule_various_states"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建测试社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("various_states"),
            description=TEST_CONSTANTS.generate_community_description("various_states"),
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建测试规则
        rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="多状态记录测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # 创建不同状态的打卡记录
        base_time = datetime.now()
        records_data = [
            {"checkin_type": "已打卡", "checkin_time": base_time},  # 已打卡
            {"checkin_type": "未打卡", "checkin_time": base_time + timedelta(hours=1)},  # 未打卡
            {"checkin_type": "已撤销", "checkin_time": base_time + timedelta(hours=2)},  # 已撤销
        ]

        for record_data in records_data:
            record = CheckinRecord(
                rule_id=rule.rule_id,
                user_id=user.user_id,
                planned_time=record_data["checkin_time"],
                checkin_type=record_data["checkin_type"],
                checkin_time=record_data["checkin_time"]
            )
            test_session.add(record)
        test_session.flush()

        # 验证记录已创建
        records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 3

        # 执行软删除（通过业务逻辑层）
        result = CheckinRuleService.delete_rule(rule.rule_id, user.user_id)
        assert result is True

        # 验证规则已删除
        deleted_rule = test_session.get(CheckinRule, rule.rule_id)
        assert deleted_rule.status == 2

        # 验证打卡记录仍然存在（软删除不影响历史记录）
        remaining_records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(remaining_records) == 3

        # 验证记录状态未改变
        checkin_types = [r.checkin_type for r in remaining_records]
        assert "已打卡" in checkin_types
        assert "未打卡" in checkin_types
        assert "已撤销" in checkin_types

    def test_delete_rule_preserves_data_integrity(self, test_session):
        """测试删除规则保持数据完整性 - 验证业务逻辑不破坏关联数据"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_delete_rule_data_integrity")
        openid = generate_unique_openid(phone_number, "test_delete_rule_data_integrity")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        user = User(
            nickname=generate_unique_nickname("test_delete_rule_data_integrity"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建测试社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("data_integrity"),
            description=TEST_CONSTANTS.generate_community_description("data_integrity"),
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建测试规则
        rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="数据完整性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()

        # 添加多条打卡记录
        for i in range(5):
            record = CheckinRecord(
                rule_id=rule.rule_id,
                user_id=user.user_id,
                planned_time=datetime.now() + timedelta(hours=i),
                checkin_type=f"打卡{i+1}",
                checkin_time=datetime.now() + timedelta(hours=i)
            )
            test_session.add(record)
        test_session.flush()

        # 验证记录创建
        records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 5

        # 执行软删除（通过业务逻辑层）
        result = CheckinRuleService.delete_rule(rule.rule_id, user.user_id)
        assert result is True

        # 验证所有打卡记录仍然存在
        remaining_records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(remaining_records) == 5

        # 验证规则已被软删除
        deleted_rule = test_session.get(CheckinRule, rule.rule_id)
        assert deleted_rule.status == 2

        # 验证记录的其他字段未改变
        for record in remaining_records:
            assert record.rule_id == rule.rule_id
            assert record.user_id == user.user_id

    def test_query_deleted_rules(self, test_session):
        """测试查询已删除的规则 - 验证业务逻辑的查询能力"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_query_deleted_rules")
        openid = generate_unique_openid(phone_number, "test_query_deleted_rules")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
        
        user = User(
            nickname=generate_unique_nickname("test_query_deleted_rules"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建测试社区
        community = Community(
            name=TEST_CONSTANTS.generate_community_name("query_deleted"),
            description=TEST_CONSTANTS.generate_community_description("query_deleted"),
            status=1
        )
        test_session.add(community)
        test_session.flush()

        # 创建多个规则
        active_rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="活跃规则",
            status=1
        )
        deleted_rule = CheckinRule(
            user_id=user.user_id,
            community_id=community.community_id,
            rule_type="personal",
            rule_name="已删除规则",
            status=2  # 已删除状态
        )
        test_session.add_all([active_rule, deleted_rule])
        test_session.flush()

        # 通过业务逻辑层删除其中一个规则
        result = CheckinRuleService.delete_rule(deleted_rule.rule_id, user.user_id)
        assert result is True

        # 查询所有规则
        all_rules = test_session.query(CheckinRule).filter_by(user_id=user.user_id).all()
        assert len(all_rules) == 2

        # 查询活跃规则
        active_rules = test_session.query(CheckinRule).filter_by(
            user_id=user.user_id,
            status=1
        ).all()
        assert len(active_rules) == 1
        assert active_rules[0].status == 1

        # 查询已删除规则
        deleted_rules = test_session.query(CheckinRule).filter_by(
            user_id=user.user_id,
            status=2
        ).all()
        assert len(deleted_rules) == 1
        assert deleted_rules[0].status == 2