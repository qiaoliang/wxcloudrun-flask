"""
分享操作集成测试
Happy path: 成功创建分享链接、解析分享链接
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


class TestShareOperations(IntegrationTestBase):
    """分享操作集成测试"""

    def test_create_share_checkin_link_success(self):
        """测试成功创建打卡分享链接"""
        with self.app.app_context():
        # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='create_share_link')
            client = self.get_test_client()

        # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日晨读',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '07:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                user.user_id
            )

        # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

        # 发送创建分享链接请求
            response = client.post(
                '/api/checkin/create',
                data=json.dumps({
                    'rule_id': rule.rule_id,
                    'expire_hours': 168  # 7天
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

        # 验证响应
            data = self.assert_api_success(response, ['token', 'url', 'mini_path', 'expire_at'])
            assert data['data']['token'] is not None
            assert data['data']['url'] is not None
            assert data['data']['mini_path'] is not None
            assert data['data']['expire_at'] is not None

        # 保存token用于后续测试
            self.share_token = data['data']['token']

    def test_resolve_share_checkin_link_success(self):
        """测试成功解析打卡分享链接"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='resolve_share_link')
            client = self.get_test_client()

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日学习',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '09:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                user.user_id
            )

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

            # 创建分享链接
            response = client.post(
                '/api/checkin/create',
                data=json.dumps({
                    'rule_id': rule.rule_id,
                    'expire_hours': 168
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            data = json.loads(response.data)
            share_token = data['data']['token']

            # 发送解析分享链接请求（无需登录）
            resolve_response = client.get(
                f'/api/checkin/resolve?token={share_token}'
            )

            # 验证响应
            resolve_data = self.assert_api_success(resolve_response, ['rule_info', 'inviter_info'])
            assert resolve_data['data']['rule_info']['rule_id'] == rule.rule_id
            assert resolve_data['data']['inviter_info']['user_id'] == user.user_id

    def test_share_checkin_page_success(self):
        """测试成功渲染分享打卡页面"""
        with self.app.app_context():
            # 创建测试用户
            user = self.create_standard_test_user(role=1, test_context='share_page')
            client = self.get_test_client()

            # 创建打卡规则
            from wxcloudrun.checkin_rule_service import CheckinRuleService
            rule = CheckinRuleService.create_rule(
                {
                    'rule_name': '每日运动',
                    'frequency_type': 0,
                    'time_slot_type': 'fixed_time',
                    'custom_time': '18:00:00',
                    'week_days': [1, 2, 3, 4, 5]
                },
                user.user_id
            )

            # 获取JWT token
            token = self.get_jwt_token(user.phone_number)

            # 创建分享链接
            response = client.post(
                '/api/checkin/create',
                data=json.dumps({
                    'rule_id': rule.rule_id,
                    'expire_hours': 168
                }),
                content_type='application/json',
                headers={'Authorization': f'Bearer {token}'}
            )

            data = json.loads(response.data)
            share_token = data['data']['token']

            # 访问分享页面（无需登录）
            page_response = client.get(f'/api/check-in?token={share_token}')

            # 验证响应
            assert page_response.status_code == 200
            assert b'<!DOCTYPE html>' in page_response.data
            assert rule.rule_name.encode('utf-8') in page_response.data
            assert user.nickname.encode('utf-8') in page_response.data


if __name__ == '__main__':
        pytest.main([__file__, '-v'])