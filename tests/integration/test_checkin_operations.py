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

from tests.integration.conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestCheckinOperations(IntegrationTestBase):
    """打卡操作集成测试"""

    def test_get_today_checkin_items_success(self):
        """测试成功获取今日打卡事项"""
        # 创建测试用户
        with self.app.app_context():
            user = self.create_standard_test_user(role=1, test_context='today_checkin')
            phone_number = user.phone_number
            self.db.session.commit()
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
            self.db.session.commit()

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '每日阅读',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                }
            )
            rule_id = result.data['rule'].rule_id
            self.db.session.commit()

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送打卡请求
        response = client.post(
            '/api/checkin',
            data=json.dumps({
                'rule_id': rule_id,
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
            self.db.session.commit()

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                }
            )

            # 在 app context 内提取 rule_id，避免访问 detached 对象
            rule_id = result.data['rule'].rule_id
            self.db.session.commit()

        client = self.get_test_client()
        # 获取JWT token
        token = self.get_jwt_token(phone_number)

        # 发送上报漏打卡请求
        response = client.post(
            '/api/checkin/miss',
            data=json.dumps({
                'rule_id': rule_id,
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
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '20:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                }
            )

            rule_id = result.data['rule'].rule_id
            self.db.session.commit()

            # 创建一个未完成的打卡记录（状态=0，待打卡）
            from database.flask_models import CheckinRecord
            from datetime import datetime
            record = CheckinRecord(
                user_id=user.user_id,
                rule_id=rule_id,
                planned_time=datetime.now(),
                status=0  # 待打卡状态
            )
            self.db.session.add(record)
            self.db.session.commit()
            record_id = record.record_id

            # 取消未完成的打卡记录
            from app.application.use_cases.checkin.cancel_checkin_use_case import CancelCheckinUseCase
            cancel_use_case = CancelCheckinUseCase()
            cancel_result = cancel_use_case.execute(
                user_id=user.user_id,
                record_id=record_id
            )

            # 验证取消成功
            assert cancel_result.is_success
            assert cancel_result.data['record_id'] == record_id

    def test_get_checkin_history_success(self):
        """测试成功获取打卡历史记录"""
        from datetime import timedelta
        from database.flask_models import db, CheckinRecord
        
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='checkin_history')
            phone_number = user.phone_number

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '每日打卡',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '08:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7]
                }
            )
            rule_id = result.data['rule'].rule_id
            self.db.session.commit()

            # 创建不同日期的打卡记录
            today = datetime.now()
            yesterday = today - timedelta(days=1)

            # 创建昨天的打卡记录
            record1 = CheckinRecord(
                user_id=user.user_id,
                rule_id=rule_id,
                planned_time=yesterday,
                checkin_time=yesterday,
                status=1
            )
            db.session.add(record1)
            
            # 创建今天的打卡记录
            record2 = CheckinRecord(
                user_id=user.user_id,
                rule_id=rule_id,
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