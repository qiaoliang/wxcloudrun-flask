"""
测试 _calculate_planned_time 方法的边界情况
验证 datetime.combine() 类型错误的修复
"""
import pytest
from datetime import datetime, date, time
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from wxcloudrun.checkin_rule_service import CheckinRuleService


class MockRule:
    """模拟规则对象，用于测试"""
    def __init__(self, time_slot_type, custom_time):
        self.time_slot_type = time_slot_type
        self.custom_time = custom_time


class TestCalculatePlannedTime:
    """测试计划时间计算方法"""
    
    def setup_method(self):
        """测试前的设置"""
        self.today = date.today()
    
    def test_normal_time_object(self):
        """测试正常的time对象"""
        rule = MockRule(4, time(9, 30))
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(9, 30))
        assert result == expected
    
    def test_string_time_hhmmss(self):
        """测试字符串时间格式 HH:MM:SS"""
        rule = MockRule(4, "09:30:00")
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(9, 30))
        assert result == expected
    
    def test_string_time_hhmm(self):
        """测试字符串时间格式 HH:MM"""
        rule = MockRule(4, "09:30")
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(9, 30))
        assert result == expected
    
    def test_invalid_string_fallback(self):
        """测试无效字符串时间，应该回退到默认时间"""
        rule = MockRule(4, "invalid_time")
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(20, 0))  # 默认晚上时间
        assert result == expected
    
    def test_non_time_type_fallback(self):
        """测试非时间类型（如数字），应该回退到默认时间"""
        rule = MockRule(4, 12345)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(20, 0))  # 默认晚上时间
        assert result == expected
    
    def test_morning_time_slot(self):
        """测试上午时间段"""
        rule = MockRule(1, None)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(9, 0))
        assert result == expected
    
    def test_afternoon_time_slot(self):
        """测试下午时间段"""
        rule = MockRule(2, None)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(14, 0))
        assert result == expected
    
    def test_evening_time_slot(self):
        """测试晚上时间段"""
        rule = MockRule(3, None)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(20, 0))
        assert result == expected
    
    def test_default_time_slot(self):
        """测试默认时间段（其他值）"""
        rule = MockRule(99, None)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(20, 0))
        assert result == expected
    
    def test_custom_time_with_none(self):
        """测试自定义时间为None的情况"""
        rule = MockRule(4, None)
        result = CheckinRuleService._calculate_planned_time(rule, self.today)
        expected = datetime.combine(self.today, time(20, 0))
        assert result == expected