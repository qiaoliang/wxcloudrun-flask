"""
删除打卡规则核心逻辑测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.models import CheckinRule, CheckinRecord, User


class TestDeleteRuleCoreLogic:
    """测试删除打卡规则的核心逻辑"""

    def test_delete_rule_sets_correct_timestamp(self, test_session, test_user):
        """测试删除规则时设置正确的时间戳"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="时间戳测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        
        # 记录删除前的时间
        before_delete = datetime.now()
        
        # 执行删除（软删除）
        rule.status = 2  # 已删除状态
        rule.deleted_at = datetime.now()
        test_session.commit()
        
        # 验证时间戳设置正确
        assert rule.deleted_at is not None
        assert before_delete <= rule.deleted_at <= datetime.now()
        
        # 验证时间戳精度（应该在秒级）
        time_diff = rule.deleted_at - before_delete
        assert time_diff.total_seconds() < 5  # 应该在5秒内

    def test_delete_rule_idempotency(self, test_session, test_user):
        """测试删除规则的幂等性"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="幂等性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        
        # 第一次删除
        rule.status = 2
        first_delete_time = datetime.now()
        rule.deleted_at = first_delete_time
        test_session.commit()
        
        assert rule.status == 2
        assert rule.deleted_at == first_delete_time
        
        # 等待一小段时间
        import time
        time.sleep(0.1)
        
        # 第二次删除（模拟再次调用删除操作）
        rule.status = 2
        rule.deleted_at = datetime.now()
        test_session.commit()
        
        # 验证状态保持不变
        assert rule.status == 2
        # 验证时间戳被更新了
        assert rule.deleted_at > first_delete_time

    def test_delete_rule_with_various_record_states(self, test_session, test_user):
        """测试删除包含各种状态记录的规则"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="多状态记录测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        
        # 创建不同状态的打卡记录
        base_time = datetime.now()
        records_data = [
            {"status": 1, "planned_time": base_time},  # 已打卡
            {"status": 0, "planned_time": base_time + timedelta(hours=1)},  # 未打卡
            {"status": 2, "planned_time": base_time + timedelta(hours=2)},  # 已撤销
        ]
        
        for record_data in records_data:
            record = CheckinRecord(
                rule_id=rule.rule_id,
                solo_user_id=test_user.user_id,
                status=record_data["status"],
                planned_time=record_data["planned_time"]
            )
            test_session.add(record)
        test_session.commit()
        
        # 验证记录已创建
        records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 3
        
        # 执行软删除
        rule.status = 2
        rule.deleted_at = datetime.now()
        test_session.commit()
        
        # 验证规则已删除
        assert rule.status == 2
        assert rule.deleted_at is not None
        
        # 验证打卡记录仍然存在
        remaining_records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(remaining_records) == 3
        
        # 验证记录状态未改变
        statuses = [r.status for r in remaining_records]
        assert 1 in statuses  # 已打卡
        assert 0 in statuses  # 未打卡
        assert 2 in statuses  # 已撤销

    def test_delete_rule_preserves_data_integrity(self, test_session, test_user):
        """测试删除规则保持数据完整性"""
        # 创建测试规则
        rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="数据完整性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        
        # 添加多条打卡记录
        for i in range(5):
            record = CheckinRecord(
                rule_id=rule.rule_id,
                solo_user_id=test_user.user_id,
                status=1 if i < 3 else 0,  # 前3条已打卡，后2条未打卡
                planned_time=datetime.now() + timedelta(hours=i)
            )
            test_session.add(record)
        test_session.commit()
        
        # 验证记录创建
        records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(records) == 5
        
        # 执行软删除
        rule.status = 2
        rule.deleted_at = datetime.now()
        test_session.commit()
        
        # 验证所有打卡记录仍然存在
        remaining_records = test_session.query(CheckinRecord).filter_by(rule_id=rule.rule_id).all()
        assert len(remaining_records) == 5
        
        # 验证记录状态保持不变
        checked_count = sum(1 for r in remaining_records if r.status == 1)
        missed_count = sum(1 for r in remaining_records if r.status == 0)
        assert checked_count == 3
        assert missed_count == 2
        
        # 验证记录的其他字段未改变
        for record in remaining_records:
            assert record.rule_id == rule.rule_id
            assert record.solo_user_id == test_user.user_id

    def test_query_deleted_rules(self, test_session, test_user):
        """测试查询已删除的规则"""
        # 创建多个规则
        active_rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="活跃规则",
            status=1
        )
        deleted_rule = CheckinRule(
            solo_user_id=test_user.user_id,
            rule_name="已删除规则",
            status=1
        )
        test_session.add_all([active_rule, deleted_rule])
        test_session.commit()
        
        # 软删除其中一个规则
        deleted_rule.status = 2
        deleted_rule.deleted_at = datetime.now()
        test_session.commit()
        
        # 查询所有规则
        all_rules = test_session.query(CheckinRule).filter_by(solo_user_id=test_user.user_id).all()
        assert len(all_rules) == 2
        
        # 查询活跃规则
        active_rules = test_session.query(CheckinRule).filter_by(
            solo_user_id=test_user.user_id,
            status=1
        ).all()
        assert len(active_rules) == 1
        assert active_rules[0].rule_name == "活跃规则"
        
        # 查询已删除规则
        deleted_rules = test_session.query(CheckinRule).filter_by(
            solo_user_id=test_user.user_id,
            status=2
        ).all()
        assert len(deleted_rules) == 1
        assert deleted_rules[0].rule_name == "已删除规则"
        assert deleted_rules[0].deleted_at is not None