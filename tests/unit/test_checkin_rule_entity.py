"""
测试 CheckinRuleEntity 领域实体
"""
import pytest
from datetime import datetime, time
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity

class TestCheckinRuleEntityCreation:
    """测试领域实体创建"""

    def test_create_entity_with_required_fields(self):
        """测试使用必需字段创建实体"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=1,  # 每天一次
            time_slot_type=0,  # 早晨
            status=1  # 启用
        )

        assert entity.rule_id == 1
        assert entity.user_id == 100
        assert entity.rule_name == "晨间打卡"
        assert entity.frequency_type == 1
        assert entity.time_slot_type == 0
        assert entity.status == 1

    def test_entity_without_orm_dependency(self):
        """测试实体不依赖 ORM 模型"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        # 不应该有 _rule 属性
        assert not hasattr(entity, '_rule')
        # 应该有直接的属性
        assert hasattr(entity, 'rule_id')
        assert hasattr(entity, 'user_id')

class TestCheckinRuleEntityBusinessLogic:
    """测试实体业务逻辑"""

    def test_enable_rule(self):
        """测试启用规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=0  # 禁用
        )

        entity.enable()

        assert entity.status == 1
        assert entity.updated_at is not None

    def test_disable_rule(self):
        """测试禁用规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1  # 启用
        )

        entity.disable()

        assert entity.status == 0

    def test_soft_delete_rule(self):
        """测试软删除规则"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        entity.soft_delete()

        assert entity.status == 2  # 删除状态
        assert entity.is_deleted is True

class TestCheckinRuleEntityValidation:
    """测试实体验证逻辑"""

    def test_update_with_invalid_frequency_type(self):
        """测试使用无效的频率类型更新"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=0,
            status=1
        )

        # 无效的频率类型不应该更新
        original_frequency = entity.frequency_type
        entity.update(frequency_type=999)

        assert entity.frequency_type == original_frequency

    def test_update_with_invalid_time_format(self):
        """测试使用无效的时间格式更新"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="测试",
            frequency_type=1,
            time_slot_type=4,  # 自定义时间
            status=1
        )

        # 无效的时间格式不应该更新
        original_time = entity.custom_time
        entity.update(custom_time="invalid-time")

        assert entity.custom_time == original_time

class TestCheckinRuleEntityCalculations:
    """测试实体计算逻辑"""

    def test_calculate_planned_checkin_time_for_morning(self):
        """测试计算早晨打卡时间"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="晨间打卡",
            frequency_type=1,
            time_slot_type=0,  # 早晨
            status=1
        )

        planned_time = entity.calculate_planned_checkin_time()

        assert planned_time is not None
        assert planned_time.hour == 8
        assert planned_time.minute == 0

    def test_calculate_planned_checkin_time_for_custom_time(self):
        """测试计算自定义打卡时间"""
        entity = CheckinRuleEntity.create(
            rule_id=1,
            user_id=100,
            rule_name="自定义打卡",
            frequency_type=1,
            time_slot_type=4,  # 自定义时间
            custom_time="09:30:00",
            status=1
        )

        planned_time = entity.calculate_planned_checkin_time()

        assert planned_time is not None
        assert planned_time.hour == 9
        assert planned_time.minute == 30
