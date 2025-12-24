import pytest
import sys
import os
import re

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import User, Community, CommunityCheckinRule
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_COMMUNITY_ID
from wxcloudrun.community_checkin_rule_service import CommunityCheckinRuleService
from wxcloudrun.community_service import CommunityService
from wxcloudrun.user_service import UserService
from wxcloudrun.user_service import random_str
import uuid as uuid_str


class TestCommunityCheckinRulesService:

    def _create_community_with_manager(self, test_session, manager_id):
        comm_name, description = f"comm_name_{uuid_str.uuid4().hex[:8]}", f"comm_desc_{uuid_str.uuid4().hex[:12]}"
        comm = CommunityService.create_community(comm_name, description, manager_id, None, None, manager_id, None, None)
        test_session.commit()
        return comm

    def _create_a_user(self, test_session):
        # Arrange - 创建一个用户（直接使用数据库，绕过UserService的默认设置）
        new_user = User(
            wechat_openid=f"test_openid{uuid_str.uuid4().hex[:8]}",
            nickname=f"微信新用户_{uuid_str.uuid4().hex[:8]}",
            avatar_url=f"https://{uuid_str.uuid4().hex[:8]}.example.com/1.jpg",
            role=4,  # 超级管理员
            status=1
        )
        test_session.add(new_user)
        test_session.commit()
        test_session.refresh(new_user)
        return new_user

    def _create_a_community_rule(self, comm_id, user_id, test_session):
        result = CommunityCheckinRuleService.create_community_rule(
            rule_data={
                'rule_name': f'默认签到规则_{uuid_str.uuid4().hex[:8]}',
                'community_id': comm_id,
                'start_time': '08:00:00',
                'end_time': '18:00:00',
                'checkin_days': [1, 2, 3, 4, 5],
                'checkin_times': [
                    {'start_time': '08:00:00',}
                ]
            },
            community_id=comm_id,
            created_by=user_id
        )
        return result

    def test_get_community_rules_with_disabled(self, test_session, test_app):
        """测试获取社区签到规则"""
        with test_app.app_context():
            # 先创建用户（超级管理员）
            a_user = self._create_a_user(test_session)
            test_session.commit()
            
            # 创建社区
            comm1 = self._create_community_with_manager(test_session, a_user.user_id)
            test_session.commit()
            
            # 创建规则
            rule1 = self._create_a_community_rule(comm1.community_id, a_user.user_id, test_session)
            rule2 = self._create_a_community_rule(comm1.community_id, a_user.user_id, test_session)
            
            # enable 两个规则
            result = CommunityCheckinRuleService.enable_community_rule(rule1.community_rule_id, a_user.user_id)
            assert result['status'] == 1
            result = CommunityCheckinRuleService.enable_community_rule(rule2.community_rule_id, a_user.user_id)
            assert result['status'] == 1

            rules = CommunityCheckinRuleService.get_community_rules(comm1.community_id, False)
            assert len(rules) == 2
            
            # 禁用其中一个规则
            result = CommunityCheckinRuleService.disable_community_rule(rule2.community_rule_id, a_user.user_id)
            assert result['status'] == 0
            
            rules = CommunityCheckinRuleService.get_community_rules(comm1.community_id, False)
            assert len(rules) == 1
            
            rules = CommunityCheckinRuleService.get_community_rules(comm1.community_id, True)
            assert len(rules) == 2

    def test_create_community_rule(self, test_session, test_app):
        """测试创建社区签到规则"""
        with test_app.app_context():
            a_user = self._create_a_user(test_session)
            # Arrange - 创建一个社区
            comm1 = self._create_community_with_manager(test_session, a_user.user_id)
            test_session.commit()

            # Act - 创建一个社区签到规则
            result = CommunityCheckinRuleService.create_community_rule(
                rule_data={
                    'rule_name': '默认社区签到规则',
                    'community_id': comm1.community_id,
                    'start_time': '08:00:00',
                    'end_time': '18:00:00',
                    'checkin_days': [1, 2, 3, 4, 5],
                    'checkin_times': [
                        {'start_time': '08:00:00',}
                    ]
                },
                community_id=comm1.community_id,
                created_by=a_user.user_id
            )
            assert result.community_rule_id == 1