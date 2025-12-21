"""
测试 today-plan 接口的集成测试
验证 combine() argument 2 must be datetime.time, not str 错误已修复
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time
from wxcloudrun.user_checkin_rule_service import UserCheckinRuleService
from wxcloudrun.checkin_rule_service import CheckinRuleService
from wxcloudrun.checkin_record_service import CheckinRecordService


class TestTodayPlanIntegration(unittest.TestCase):
    def setUp(self):
        self.user_id = 1
        self.today = date(2025, 12, 19)

    def test_today_plan_with_string_time_fix(self):
        """测试 today-plan 接口处理字符串时间的情况"""
        
        # 直接测试 CheckinRecordService._calculate_planned_time 处理字符串时间的能力
        # 这模拟了社区规则传递字符串时间的情况
        
        # 测试字典格式规则（社区规则）
        rule_dict = {
            'community_rule_id': 2,
            'rule_name': '社区健康打卡',
            'time_slot_type': 4,
            'custom_time': '09:30:00'  # 字符串格式时间
        }
        
        # 这应该不会抛出 combine() argument 2 must be datetime.time, not str 错误
        result = CheckinRecordService._calculate_planned_time(rule_dict, self.today)
        expected = datetime(2025, 12, 19, 9, 30)
        self.assertEqual(result, expected)
        
        # 测试对象格式规则（个人规则）
        class MockRule:
            def __init__(self):
                self.community_rule_id = 2
                self.rule_name = '社区健康打卡'
                self.time_slot_type = 4
                self.custom_time = '09:30:00'  # 字符串格式时间

        rule_obj = MockRule()
        result2 = CheckinRecordService._calculate_planned_time(rule_obj, self.today)
        expected2 = datetime(2025, 12, 19, 9, 30)
        self.assertEqual(result2, expected2)

    def test_checkin_record_service_calculate_planned_time_with_string(self):
        """测试 CheckinRecordService._calculate_planned_time 处理字符串时间"""
        
        # 测试字典格式规则（社区规则）
        rule_dict = {
            'time_slot_type': 4,
            'custom_time': '14:30:00'
        }
        
        result = CheckinRecordService._calculate_planned_time(rule_dict, self.today)
        expected = datetime(2025, 12, 19, 14, 30)
        self.assertEqual(result, expected)

        # 测试对象格式规则（个人规则）
        class MockRule:
            def __init__(self):
                self.time_slot_type = 4
                self.custom_time = '16:45:00'  # 字符串格式时间

        rule_obj = MockRule()
        result2 = CheckinRecordService._calculate_planned_time(rule_obj, self.today)
        expected2 = datetime(2025, 12, 19, 16, 45)
        self.assertEqual(result2, expected2)

    def test_checkin_record_service_calculate_planned_time_error_handling(self):
        """测试 CheckinRecordService._calculate_planned_time 错误处理"""
        
        # 测试无效时间格式
        rule_dict = {
            'time_slot_type': 4,
            'custom_time': 'invalid_time'
        }
        
        result = CheckinRecordService._calculate_planned_time(rule_dict, self.today)
        expected = datetime(2025, 12, 19, 20, 0)  # 应该回退到默认时间
        self.assertEqual(result, expected)

        # 测试非时间类型
        rule_dict2 = {
            'time_slot_type': 4,
            'custom_time': 12345
        }
        
        result2 = CheckinRecordService._calculate_planned_time(rule_dict2, self.today)
        expected2 = datetime(2025, 12, 19, 20, 0)  # 应该回退到默认时间
        self.assertEqual(result2, expected2)


if __name__ == '__main__':
    unittest.main()