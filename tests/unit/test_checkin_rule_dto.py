"""
测试 CheckinRuleDTO
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.application.dtos.checkin_rule_dto import CheckinRuleDTO


class TestCheckinRuleDTO:
    """测试CheckinRuleDTO"""

    def test_from_entity_basic_fields(self):
        """测试基本字段转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=0,  # 每天
            time_slot_type=0,  # 早晨
            status=1  # 启用
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['rule_id'] == 1
        assert result['user_id'] == 100
        assert result['rule_name'] == "晨间打卡"
        assert result['frequency_type'] == 0
        assert result['time_slot_type'] == 0
        assert result['status'] == 1

    def test_from_entity_with_custom_time(self):
        """测试带自定义时间的转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="自定义打卡",
            frequency_type=0,
            time_slot_type=4,  # 自定义
            custom_time="09:30:00",
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['custom_time'] == "09:30:00"

    def test_from_entity_with_week_days_bitmask(self):
        """测试week_days位掩码转换"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="工作日打卡",
            frequency_type=1,  # 每周
            time_slot_type=4,
            week_days=31,  # 周一至周五
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert result['week_days'] == 31

    def test_from_entity_with_datetime_fields(self):
        """测试日期时间字段转换"""
        now = datetime.now()
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="日期范围打卡",
            frequency_type=3,  # 自定义日期
            time_slot_type=4,
            custom_start_date=now,
            custom_end_date=now,
            status=1
        )

        result = CheckinRuleDTO.from_entity(entity)

        assert 'custom_start_date' in result
        assert 'custom_end_date' in result
        assert result['custom_start_date'] is not None
        assert result['custom_end_date'] is not None

    def test_from_entity_list(self):
        """测试列表转换"""
        entities = [
            CheckinRuleEntity.create(
                rule_id=i,
                user_id=100,
                rule_name=f"打卡规则{i}",
                frequency_type=0,
                time_slot_type=0,
                status=1
            ) for i in range(1, 4)
        ]

        result = CheckinRuleDTO.from_entity_list(entities)

        assert len(result) == 3
        assert result[0]['rule_id'] == 1
        assert result[1]['rule_id'] == 2
        assert result[2]['rule_id'] == 3
