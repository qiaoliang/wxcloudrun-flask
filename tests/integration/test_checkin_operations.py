"""
打卡操作集成测试
Happy path: 成功执行打卡、上报漏打卡、取消打卡
"""

import pytest
import json
import os
import sys
from datetime import datetime, date

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestCheckinOperations(IntegrationTestBase):
    """打卡操作集成测试"""

    def test_get_today_checkin_items_success(self):
        """测试成功获取今日打卡事项"""
        # 创建测试用户
        with self.app.app_context():
            user = self.create_standard_test_user(role=1, test_context='today_checkin')
            phone_number = user.phone_number
        client = self.get_test_client()

        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送获取今日打卡事项请求
        response = client.get(
            '/api/checkin/today',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['checkin_items', 'date'])
        assert 'checkin_items' in data['data']
        assert 'date' in data['data']

    def test_perform_checkin_success(self):
        """测试成功执行打卡"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='perform_checkin')
            phone_number = user.phone_number

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日阅读',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                },
                user.user_id
            )

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送打卡请求
        response = client.post(
            '/api/checkin',
            data=json.dumps({
                'rule_id': rule.rule_id,
                'checkin_time': '09:00:00',
                'note': '今天完成了阅读任务'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['record_id', 'status'])
        assert data['data']['status'] == 'completed'

    def test_report_miss_checkin_success(self):
        """测试成功上报漏打卡"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='miss_checkin')
            phone_number = user.phone_number

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                },
                user.user_id
            )

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送上报漏打卡请求
        response = client.post(
            '/api/checkin/miss',
            data=json.dumps({
                'rule_id': rule.rule_id,
                'miss_date': '2024-12-25',
                'reason': '生病了，无法运动'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['record_id', 'status'])
        assert data['data']['status'] == 'missed'

    def test_cancel_checkin_success(self):
        """测试成功取消打卡"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='cancel_checkin')
            phone_number = user.phone_number

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '20:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                },
                user.user_id
            )

            # 先执行打卡
            from wxcloudrun.checkin_record_service import CheckinRecordService
            record = CheckinRecordService.perform_checkin(
                rule.rule_id,
                user.user_id
            )

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送取消打卡请求
        response = client.post(
            '/api/checkin/cancel',
            data=json.dumps({
                'record_id': record['record_id'],
                'reason': '误操作，取消打卡'
            }),
            content_type='application/json',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['record_id', 'status'])
        assert data['data']['status'] == 'cancelled'

    def test_get_checkin_history_success(self):
        """测试成功获取打卡历史记录"""
        from datetime import timedelta
        from database.flask_models import db, CheckinRecord
        
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='checkin_history')
            phone_number = user.phone_number

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日打卡',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '08:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                },
                user.user_id
            )

            # 创建不同日期的打卡记录
            today = datetime.now()
            yesterday = today - timedelta(days=1)
            
            # 创建昨天的打卡记录
            record1 = CheckinRecord(
                user_id=user.user_id,
                rule_id=rule.rule_id,
                planned_time=yesterday,
                checkin_time=yesterday,
                status=1
            )
            db.session.add(record1)
            
            # 创建今天的打卡记录
            record2 = CheckinRecord(
                user_id=user.user_id,
                rule_id=rule.rule_id,
                planned_time=today,
                checkin_time=today,
                status=1
            )
            db.session.add(record2)
            db.session.commit()

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送获取打卡历史请求
        response = client.get(
            '/api/checkin/history',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['history', 'total'])
        assert data['data']['total'] >= 2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])