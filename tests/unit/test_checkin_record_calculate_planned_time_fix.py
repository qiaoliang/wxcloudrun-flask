"""
测试 CheckinRecordService._calculate_planned_time 方法的边界情况
"""
import unittest
from datetime import datetime, date, time
from wxcloudrun.checkin_record_service import CheckinRecordService


class TestCalculatePlannedTimeFix(unittest.TestCase):
    def setUp(self):
        self.today = date(2025, 12, 19)

    def test_normal_time_object(self):
        """测试正常的time对象"""
        rule = {
            'time_slot_type': 4,
            'custom_time': time(9, 30)
        }
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 9, 30)
        self.assertEqual(result, expected)

    def test_string_time_hhmmss(self):
        """测试HH:MM:SS格式字符串"""
        rule = {
            'time_slot_type': 4,
            'custom_time': '09:30:00'
        }
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 9, 30)
        self.assertEqual(result, expected)

    def test_string_time_hhmm(self):
        """测试HH:MM格式字符串"""
        rule = {
            'time_slot_type': 4,
            'custom_time': '09:30'
        }
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 9, 30)
        self.assertEqual(result, expected)

    def test_invalid_string_fallback(self):
        """测试无效字符串格式回退到默认时间"""
        rule = {
            'time_slot_type': 4,
            'custom_time': 'invalid_time'
        }
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 20, 0)  # 默认晚上8点
        self.assertEqual(result, expected)

    def test_non_time_type_fallback(self):
        """测试非时间类型回退到默认时间"""
        rule = {
            'time_slot_type': 4,
            'custom_time': 12345  # 数字类型
        }
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 20, 0)  # 默认晚上8点
        self.assertEqual(result, expected)

    def test_morning_time_slot(self):
        """测试上午时间段"""
        rule = {'time_slot_type': 1}
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 9, 0)
        self.assertEqual(result, expected)

    def test_afternoon_time_slot(self):
        """测试下午时间段"""
        rule = {'time_slot_type': 2}
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 14, 0)
        self.assertEqual(result, expected)

    def test_evening_time_slot(self):
        """测试晚上时间段"""
        rule = {'time_slot_type': 3}
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 20, 0)
        self.assertEqual(result, expected)

    def test_default_time_slot(self):
        """测试默认时间段（其他值）"""
        rule = {'time_slot_type': 99}
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 20, 0)
        self.assertEqual(result, expected)

    def test_custom_time_with_none(self):
        """测试自定义时间为None"""
        rule = {'time_slot_type': 4, 'custom_time': None}
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 20, 0)
        self.assertEqual(result, expected)

    def test_object_rule_with_string_time(self):
        """测试对象格式规则且时间为字符串"""
        class MockRule:
            def __init__(self):
                self.time_slot_type = 4
                self.custom_time = '15:45:00'
        
        rule = MockRule()
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 15, 45)
        self.assertEqual(result, expected)

    def test_object_rule_with_time_object(self):
        """测试对象格式规则且时间为time对象"""
        class MockRule:
            def __init__(self):
                self.time_slot_type = 4
                self.custom_time = time(15, 45)
        
        rule = MockRule()
        result = CheckinRecordService._calculate_planned_time(rule, self.today)
        expected = datetime(2025, 12, 19, 15, 45)
        self.assertEqual(result, expected)


if __name__ == '__main__':
    unittest.main()