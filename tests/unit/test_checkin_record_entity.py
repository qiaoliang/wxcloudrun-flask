"""
测试 CheckinRecordEntity 领域实体
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_record_entity import CheckinRecordEntity

class TestCheckinRecordEntityCreation:
    """测试打卡记录实体创建"""

    def test_create_entity_with_required_fields(self):
        """测试使用必需字段创建实体"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        assert entity.record_id == 1
        assert entity.rule_id == 10
        assert entity.user_id == 100
        assert entity.checkin_status == 0  # 默认为未打卡

    def test_entity_without_orm_dependency(self):
        """测试实体不依赖 ORM 模型"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        # 不应该有 _record 属性
        assert not hasattr(entity, '_record')

class TestCheckinRecordEntityStateTransitions:
    """测试状态转换"""

    def test_complete_checkin(self):
        """测试完成打卡"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.complete()

        assert entity.is_completed is True
        assert entity.checkin_time is not None

    def test_mark_as_missed(self):
        """测试标记为错过"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.mark_missed()

        assert entity.is_missed is True
        assert entity.checkin_status == 2

    def test_cancel_checkin(self):
        """测试取消打卡(映射到 MISSED 状态)"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.cancel()

        assert entity.is_cancelled is True
        assert entity.checkin_status == 2  # CANCELLED 映射到 MISSED

class TestCheckinRecordEntityBusinessRules:
    """测试业务规则"""

    def test_is_overdue(self):
        """测试超时检查"""
        from datetime import timedelta

        planned_time = datetime.now() - timedelta(hours=5)
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=planned_time
        )

        # 超过4小时应该算超时
        assert entity.is_overdue() is True

    def test_get_checkin_delay(self):
        """测试获取打卡延迟"""
        from datetime import timedelta

        planned_time = datetime.now() - timedelta(hours=2)
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=planned_time
        )

        entity.complete(checkin_time=datetime.now())
        delay = entity.get_checkin_delay()

        assert delay is not None
        assert delay.total_seconds() > 0
