"""
打卡规则管理集成测试
Happy path: 成功创建、查询、更新、删除打卡规则
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.integration.conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestCheckinRules(IntegrationTestBase):
    """打卡规则管理集成测试"""

    def test_create_checkin_rule_success(self):
        """测试成功创建打卡规则"""
        with self.app.app_context():
        # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='create_rule')
            client = self.get_test_client()

        # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

        # 发送创建打卡规则请求
            response = client.post(
                '/api/checkin/rules',
                data=json.dumps({
                    'rule_name': '每日晨读',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '07:00:00',
                    'week_days': [1, 2, 3, 4, 5, 6, 7],
                    'icon_url': 'https://example.com/icon.png'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['rule'])
            assert data['data']['rule']['rule_name'] == '每日晨读'
            assert data['data']['rule']['frequency_type'] == 0

    def test_get_checkin_rules_success(self):
        """测试成功获取打卡规则列表"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='get_rules')
            client = self.get_test_client()

            # 创建几个打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '规则1',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '08:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '规则2',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

        # 发送获取打卡规则列表请求
            response = client.get(
                '/api/checkin/rules',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['rules'])
            assert len(data['data']['rules']) >= 2

        def test_get_single_checkin_rule_success(self):
            """测试成功获取单个打卡规则"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='get_single_rule')
            client = self.get_test_client()

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '测试规则',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

            # 发送获取单个打卡规则请求
            response = client.get(
                f'/api/checkin/rules?rule_id={rule_id}',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['rule_id', 'rule_name'])
            assert data['data']['rule_id'] == rule_id
            assert data['data']['rule_name'] == '测试规则'

    def test_update_checkin_rule_success(self):
        """测试成功更新打卡规则"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='update_rule')
            client = self.get_test_client()

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '原始规则',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '10:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

            # 发送更新打卡规则请求
            response = client.put(
                '/api/checkin/rules',
                data=json.dumps({
                    'rule_id': rule_id,
                    'rule_name': '更新后的规则',
                    'custom_time': '11:00:00'
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['rule'])
            assert data['data']['rule']['rule_name'] == '更新后的规则'

    def test_delete_checkin_rule_success(self):
        """测试成功删除打卡规则"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='delete_rule')
            client = self.get_test_client()

            # 创建打卡规则
            from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
            create_rule_use_case = CreateCheckinRuleUseCase()
            result = create_rule_use_case.execute(
                user_id=user.user_id,
                rule_data={
                    'rule_name': '待删除规则',
                    'frequency_type': 0,  # 每天
                    'time_slot_type': 4,  # 自定义时间
                    'custom_time': '12:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                }
            )
            rule_id = result.data['rule'].rule_id

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

            # 发送删除打卡规则请求
            response = client.delete(
                f'/api/checkin/rules?rule_id={rule_id}',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response, ['message'])
            assert data['data']['message'] == '规则删除成功'


if __name__ == '__main__':
        pytest.main([__file__, '-v'])