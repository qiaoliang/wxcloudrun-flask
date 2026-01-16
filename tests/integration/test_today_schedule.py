"""
今日待办集成测试
测试查看今日待办事项的完整流程，包括个人规则和社区规则的混合展示
"""

import pytest
import json
import sys
import os
from datetime import datetime, date, timedelta

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import User, Community, CheckinRule, CommunityCheckinRule, CheckinRecord
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestTodayScheduleIntegration(IntegrationTestBase):
    """今日待办集成测试类"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        cls._create_test_data()

    @classmethod
    def _create_test_data(cls):
        """创建测试数据"""
        with cls.app.app_context():
            # 创建测试用户
            cls.test_user = cls.create_standard_test_user(role=1)
            
            # 创建测试社区
            cls.test_community = cls.create_test_community(
                name='今日待办测试社区',
                creator=cls.test_user
            )
            
            # 建立用户-社区关系
            cls.test_user.community_id = cls.test_community.community_id
            cls.db.session.commit()

            print(f"✅ 创建测试用户: user_id={cls.test_user.user_id}")
            print(f"✅ phone_number: {cls.test_user.phone_number}")

    # ==================== 辅助方法 ====================

    def _create_test_user_with_token(self, test_context):
        """
        创建独立的测试用户并返回user_id和token
        
        Args:
            test_context: 测试上下文标识
            
        Returns:
            tuple: (user_id, phone_number, token)
        """
        user_id = None
        phone_number = None
        with self.app.app_context():
            test_user = self.create_standard_test_user(role=1, test_context=test_context)
            user_id = test_user.user_id
            phone_number = test_user.phone_number
            self.db.session.commit()
        
        token = self.get_jwt_token(phone_number)
        return user_id, phone_number, token

    def _create_personal_rule(self, user_id, rule_name, custom_time, week_days=127):
        """
        创建个人打卡规则

        Args:
            user_id: 用户ID
            rule_name: 规则名称
            custom_time: 自定义时间
            week_days: 周天数位掩码，默认127（每天）

        Returns:
            CheckinRule: 创建的规则对象
        """
        from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase

        create_rule_use_case = CreateCheckinRuleUseCase()
        result = create_rule_use_case.execute(
            user_id=user_id,
            rule_data={
                'rule_name': rule_name,
                'frequency_type': 0,  # 每天
                'time_slot_type': 4,  # 固定时间
                'custom_time': custom_time,
                'week_days': [1, 2, 3, 4, 5, 6, 7] if week_days == 127 else []
            }
        )
        # 确保规则被提交到数据库
        self.db.session.commit()
        return result.data['rule']

    def _create_checkin_record(self, user_id, rule_id, custom_time, checkin_time=None, status=1):
        """
        创建打卡记录
        
        Args:
            user_id: 用户ID
            rule_id: 规则ID
            custom_time: 计划时间
            checkin_time: 实际打卡时间，默认为当前时间
            status: 打卡状态，默认1（已打卡）
            
        Returns:
            CheckinRecord: 创建的打卡记录对象
        """
        today = date.today()
        record = CheckinRecord(
            user_id=user_id,
            rule_id=rule_id,
            planned_time=datetime.combine(today, datetime.strptime(custom_time, '%H:%M:%S').time()),
            checkin_time=checkin_time or datetime.now(),
            status=status
        )
        self.db.session.add(record)
        self.db.session.commit()
        return record

    def _create_community_rule_with_activation(self, user_id, community_id, rule_name, custom_time, week_days=127):
        """
        创建社区规则并激活

        Args:
            user_id: 用户ID
            community_id: 社区ID
            rule_name: 规则名称
            custom_time: 自定义时间
            week_days: 周天数位掩码，默认127（每天）

        Returns:
            CommunityCheckinRule: 创建的社区规则对象
        """
        from app.shared.utils.community_helpers import CommunityRuleQueryHelper
        from database.flask_models import UserCommunityRule

        # 创建社区打卡规则
        community_rule = CommunityCheckinRuleService.create_community_rule(
            {
                'rule_name': rule_name,
                'frequency_type': 0,  # 每天
                'time_slot_type': 4,  # 固定时间
                'custom_time': custom_time,
                'week_days': week_days
            },
            community_id,
            user_id
        )

        # 启用社区规则
        community_rule.status = 1

        # 创建 UserCommunityRule 关系，激活社区规则
        user_community_rule = UserCommunityRule(
            user_id=user_id,
            community_rule_id=community_rule.community_rule_id,
            is_active=True
        )
        self.db.session.add(user_community_rule)
        self.db.session.commit()

        return community_rule

    def _setup_community_with_staff(self, user_id, community_id):
        """
        设置用户为社区工作人员

        Args:
            user_id: 用户ID
            community_id: 社区ID
        """
        from app.shared.utils.community_helpers import CommunityRuleHelper
        from database.flask_models import User

        # 添加社区工作人员记录
        CommunityStaffService.add_staff_single(
            community_id=community_id,
            user_id=user_id,
            role='staff',
            operator_id=user_id
        )

        # 设置用户的 community_id（GetUserTodayPlanUseCase 需要此字段来查询社区规则）
        user = self.db.session.get(User, user_id)
        user.community_id = community_id
        self.db.session.commit()

    def test_get_today_checkin_items_empty(self):
        """测试获取今日打卡事项（无规则）"""
        client = self.get_test_client()

        # 获取JWT token
        token = self.get_jwt_token(self.test_user.phone_number)

        # 发送获取今日打卡事项请求
        response = client.get(
            '/api/checkin/today',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['checkin_items', 'date'])
        assert 'checkin_items' in data['data']
        assert 'date' in data['data']
        assert isinstance(data['data']['checkin_items'], list)

        print(f"✅ 获取今日打卡事项成功（无规则）")

    def test_get_today_checkin_items_with_personal_rules(self):
        """测试获取今日打卡事项（包含个人规则）"""
        client = self.get_test_client()

        with self.app.app_context():
            # 创建个人打卡规则
            rule1 = self._create_personal_rule(
                self.test_user.user_id, 
                '每日晨读', 
                '08:00:00'
            )

            rule2 = self._create_personal_rule(
                self.test_user.user_id, 
                '晚间运动', 
                '20:00:00'
            )

            # 为第一个规则创建今日打卡记录
            self._create_checkin_record(
                self.test_user.user_id, 
                rule1.rule_id, 
                '08:00:00'
            )

        # 获取JWT token
        token = self.get_jwt_token(self.test_user.phone_number)

        # 发送获取今日打卡事项请求
        response = client.get(
            '/api/checkin/today',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['checkin_items', 'date'])
        checkin_items = data['data']['checkin_items']
        
        assert len(checkin_items) == 2
        assert checkin_items[0]['rule_name'] == '每日晨读'
        assert checkin_items[0]['status'] == 'checked'
        assert checkin_items[1]['rule_name'] == '晚间运动'
        assert checkin_items[1]['status'] == 'pending'

        print(f"✅ 获取今日打卡事项成功（包含个人规则）")

    def test_get_user_today_plan_empty(self):
        """测试获取用户今日计划（无规则）"""
        client = self.get_test_client()

        # 创建独立的测试用户并获取token
        user_id, phone_number, token = self._create_test_user_with_token('empty_plan')

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date', 'total_items', 'completed_items', 'pending_items', 'items'])
        assert data['data']['total_items'] == 0
        assert data['data']['completed_items'] == 0
        assert data['data']['pending_items'] == 0
        assert isinstance(data['data']['items'], list)

        print(f"✅ 获取用户今日计划成功（无规则）")

    def test_get_user_today_plan_with_personal_rules(self):
        """测试获取用户今日计划（包含个人规则）"""
        client = self.get_test_client()

        # 创建独立的测试用户并获取token
        user_id, phone_number, token = self._create_test_user_with_token('personal_rules')

        with self.app.app_context():
            # 创建个人打卡规则
            self._create_personal_rule(
                user_id,
                '每日学习',
                '10:00:00'
            )

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date', 'total_items', 'completed_items', 'pending_items', 'items'])
        assert data['data']['total_items'] == 1
        assert len(data['data']['items']) == 1
        assert data['data']['items'][0]['rule_name'] == '每日学习'
        assert data['data']['items'][0]['rule_source'] == 'personal'
        assert data['data']['items'][0]['is_editable'] == True
        # 验证状态值是 pending（未打卡）
        assert data['data']['items'][0]['status'] == 'pending'

        print(f"✅ 获取用户今日计划成功（包含个人规则）")

    def test_get_user_today_plan_with_community_rules(self):
        """测试获取用户今日计划（包含社区规则）"""
        client = self.get_test_client()

        # 创建独立的测试用户并获取token
        user_id, phone_number, token = self._create_test_user_with_token('community_rules')

        with self.app.app_context():
            # 创建测试社区
            test_community = self.create_test_community(
                name='社区规则测试社区',
                creator=self.test_user  # 使用类级别的测试用户作为创建者
            )
            
            # 设置用户为社区工作人员
            self._setup_community_with_staff(user_id, test_community.community_id)
            
            # 创建社区规则并激活
            self._create_community_rule_with_activation(
                user_id,
                test_community.community_id,
                '社区健康打卡',
                '09:00:00',
                127  # 每天都打卡
            )

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date', 'total_items', 'completed_items', 'pending_items', 'items'])
        
        # 应该包含社区规则
        assert data['data']['total_items'] >= 1
        community_items = [item for item in data['data']['items'] if item.get('rule_source') == 'community']
        assert len(community_items) >= 1
        assert community_items[0]['rule_name'] == '社区健康打卡'
        assert community_items[0]['is_editable'] == False
        assert community_items[0]['community_name'] == '社区规则测试社区'
        # 验证状态值是 pending（未打卡）
        assert community_items[0]['status'] == 'pending'

        print(f"✅ 获取用户今日计划成功（包含社区规则）")

    def test_get_user_today_plan_mixed_rules(self):
        """测试获取用户今日计划（混合个人规则和社区规则）"""
        client = self.get_test_client()

        # 创建独立的测试用户并获取token
        user_id, phone_number, token = self._create_test_user_with_token('mixed_rules')

        with self.app.app_context():
            # 创建测试社区
            test_community = self.create_test_community(
                name='混合规则测试社区',
                creator=self.test_user  # 使用类级别的测试用户作为创建者
            )
            
            # 设置用户为社区工作人员
            self._setup_community_with_staff(user_id, test_community.community_id)
            
            # 创建个人打卡规则
            personal_rule = self._create_personal_rule(
                user_id, 
                '个人晨练', 
                '07:00:00'
            )

            # 创建社区规则并激活
            self._create_community_rule_with_activation(
                user_id,
                test_community.community_id,
                '社区会议',
                '14:00:00',
                31  # 仅工作日（位掩码：0b00011111 = 31，周一到周五）
            )

            # 为个人规则创建今日打卡记录
            self._create_checkin_record(
                user_id, 
                personal_rule.rule_id, 
                '07:00:00'
            )

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date', 'total_items', 'completed_items', 'pending_items', 'items'])
        
        # 检查个人规则
        personal_items = [item for item in data['data']['items'] if item.get('rule_source') == 'personal']
        assert len(personal_items) == 1
        assert personal_items[0]['rule_name'] == '个人晨练'
        assert personal_items[0]['status'] == 'checked'  # 已打卡
        assert personal_items[0]['is_editable'] == True
        
        # 检查社区规则
        community_items = [item for item in data['data']['items'] if item.get('rule_source') == 'community']
        assert len(community_items) == 1
        assert community_items[0]['rule_name'] == '社区会议'
        assert community_items[0]['is_editable'] == False
        assert community_items[0]['community_name'] == '混合规则测试社区'
        # 验证状态值是 pending（未打卡）
        assert community_items[0]['status'] == 'pending'

        print(f"✅ 获取用户今日计划成功（混合个人规则和社区规则）")

    def test_get_today_checkin_items_unauthorized(self):
        """测试未授权访问今日打卡事项"""
        client = self.get_test_client()

        # 不提供token
        response = client.get('/api/checkin/today')

        # 验证错误响应
        data = self.assert_api_error(response, expected_msg_pattern='缺少token参数')

        print(f"✅ 未授权访问验证通过")

    def test_get_user_today_plan_unauthorized(self):
        """测试未授权访问用户今日计划"""
        client = self.get_test_client()

        # 不提供token
        response = client.get('/api/user-checkin/today-plan')

        # 验证错误响应
        data = self.assert_api_error(response, expected_msg_pattern='缺少token参数')

        print(f"✅ 未授权访问验证通过")

    def test_get_user_today_plan_date_format(self):
        """测试今日计划的日期格式"""
        client = self.get_test_client()

        # 获取JWT token
        token = self.get_jwt_token(self.test_user.phone_number)

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date'])
        
        # 验证日期格式为 YYYY-MM-DD
        date_str = data['data']['date']
        assert len(date_str) == 10  # YYYY-MM-DD
        assert date_str.count('-') == 2
        
        # 验证日期是今天
        today_str = date.today().strftime('%Y-%m-%d')
        assert date_str == today_str

        print(f"✅ 日期格式验证通过: {date_str}")

    def test_get_user_today_plan_with_completed_items(self):
        """测试获取用户今日计划（包含已完成的事项）"""
        client = self.get_test_client()

        # 创建独立的测试用户并获取token
        user_id, phone_number, token = self._create_test_user_with_token('completed_items')

        with self.app.app_context():
            # 创建个人打卡规则
            rule1 = self._create_personal_rule(
                user_id, 
                '早起打卡', 
                '06:00:00'
            )

            rule2 = self._create_personal_rule(
                user_id, 
                '睡前阅读', 
                '22:00:00'
            )

            # 为两个规则创建今日打卡记录
            self._create_checkin_record(
                user_id, 
                rule1.rule_id, 
                '06:00:00',
                checkin_time=datetime.now() - timedelta(hours=2)
            )
            
            self._create_checkin_record(
                user_id, 
                rule2.rule_id, 
                '22:00:00'
            )

        # 发送获取用户今日计划请求
        response = client.get(
            '/api/user-checkin/today-plan',
            headers={'Authorization': f'Bearer {token}'}
        )

        # 验证响应
        data = self.assert_api_success(response, ['date', 'total_items', 'completed_items', 'pending_items', 'items'])
        
        assert data['data']['total_items'] == 2
        
        # 验证所有事项都已完成
        for item in data['data']['items']:
            assert item['status'] == 'checked'  # 已打卡
            assert item['checkin_time'] is not None

        print(f"✅ 获取用户今日计划成功（包含已完成的事项）")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])