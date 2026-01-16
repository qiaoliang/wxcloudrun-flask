import pytest
import sys
import os
from datetime import datetime, date, time, timedelta

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from database.flask_models import (
    User, Community, CommunityCheckinRule, CheckinRecord,
    UserDailyAbnormality, UserCommunityRule
)
from wxcloudrun.community_dashboard_service import CommunityDashboardService
from app.shared.utils.community_helpers import CommunityPermissionHelper, CommunityRuleHelper
from app.shared.utils.community_helpers import CommunityRuleQueryHelper
from app.shared.constants.roles import Role
import uuid as uuid_str


class TestCommunityDashboardService:
    """社区数字看板服务单元测试"""

    def _create_community_with_manager(self, test_session, manager_id):
        """创建测试社区"""
        comm_name = f"comm_name_{uuid_str.uuid4().hex[:8]}"
        description = f"comm_desc_{uuid_str.uuid4().hex[:12]}"
        comm = CommunityService.create_community(
            comm_name, description, manager_id, None, None, manager_id
        )
        test_session.commit()
        return comm

    def _create_user(self, test_session, role=Role.SOLO, community_id=None):
        """创建测试用户"""
        new_user = User(
            wechat_openid=f"test_openid{uuid_str.uuid4().hex[:8]}",
            nickname=f"测试用户_{uuid_str.uuid4().hex[:8]}",
            avatar_url=f"https://{uuid_str.uuid4().hex[:8]}.example.com/avatar.jpg",
            role=role,
            status=1,
            community_id=community_id
        )
        test_session.add(new_user)
        test_session.commit()
        test_session.refresh(new_user)
        return new_user

    def _create_community_rule(self, comm_id, user_id, test_session, rule_name=None):
        """创建社区打卡规则"""
        if not rule_name:
            rule_name = f'测试规则_{uuid_str.uuid4().hex[:8]}'

        result = CommunityCheckinRuleService.create_community_rule(
            rule_data={
                'rule_name': rule_name,
                'community_id': comm_id,
                'start_time': '08:00:00',
                'end_time': '18:00:00',
                'checkin_days': [1, 2, 3, 4, 5, 6, 7],
                'checkin_times': [{'start_time': '08:00:00'}]
            },
            community_id=comm_id,
            created_by=user_id
        )
        return result

    def test_has_permission_super_admin(self, test_session, test_app):
        """测试超级管理员权限检查"""
        with test_app.app_context():
            # 创建超级管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 超级管理员应该有权限访问任何社区
            has_permission = CommunityDashboardService.has_permission(admin.user_id, comm.community_id)
            assert has_permission is True

    def test_has_permission_manager(self, test_session, test_app):
        """测试社区主管权限检查"""
        with test_app.app_context():
            # 创建社区主管
            manager = self._create_user(test_session, role=Role.MANAGER)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, manager.user_id)
            test_session.commit()

            # 将主管分配到该社区
            manager.community_id = comm.community_id
            test_session.commit()

            # 主管应该有权限访问自己管理的社区
            has_permission = CommunityDashboardService.has_permission(manager.user_id, comm.community_id)
            assert has_permission is True

    def test_has_permission_staff(self, test_session, test_app):
        """测试社区专员权限检查"""
        with test_app.app_context():
            # 创建社区主管
            manager = self._create_user(test_session, role=Role.MANAGER)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, manager.user_id)
            test_session.commit()

            # 创建社区专员
            staff = self._create_user(test_session, role=Role.STAFF, community_id=comm.community_id)
            test_session.commit()

            # 专员应该有权限访问所属社区
            has_permission = CommunityDashboardService.has_permission(staff.user_id, comm.community_id)
            assert has_permission is True

    def test_has_permission_solo_user(self, test_session, test_app):
        """测试普通用户无权限"""
        with test_app.app_context():
            # 创建社区主管
            manager = self._create_user(test_session, role=Role.MANAGER)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, manager.user_id)
            test_session.commit()

            # 创建普通用户
            solo_user = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            test_session.commit()

            # 普通用户不应该有权限访问数据看板
            has_permission = CommunityDashboardService.has_permission(solo_user.user_id, comm.community_id)
            assert has_permission is False

    def test_get_community_stats(self, test_session, test_app):
        """测试获取社区统计数据"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 创建3个用户
            user1 = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            user2 = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            user3 = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            test_session.commit()

            # 创建2个启用的规则
            rule1 = self._create_community_rule(comm.community_id, admin.user_id, test_session, '晨间问候')
            rule2 = self._create_community_rule(comm.community_id, admin.user_id, test_session, '晚间报平安')
            CommunityCheckinRuleService.enable_community_rule(rule1.community_rule_id, admin.user_id)
            CommunityCheckinRuleService.enable_community_rule(rule2.community_rule_id, admin.user_id)
            test_session.commit()

            # 为用户创建规则关联
            for user in [user1, user2, user3]:
                for rule_obj in [rule1, rule2]:
                    # 检查是否已存在关联
                    existing = test_session.query(UserCommunityRule).filter_by(
                        user_id=user.user_id,
                        community_rule_id=rule_obj.community_rule_id
                    ).first()
                    if not existing:
                        mapping = UserCommunityRule(
                            user_id=user.user_id,
                            community_rule_id=rule_obj.community_rule_id,
                            is_active=True
                        )
                        test_session.add(mapping)
            test_session.commit()

            # 获取统计数据
            stats = CommunityDashboardService.get_community_stats(comm.community_id)

            assert stats['total_users'] == 3
            assert stats['total_rules'] == 2
            assert 'today_checkin_rate' in stats
            assert 'unchecked_count' in stats

    def test_get_abnormal_users_empty(self, test_session, test_app):
        """测试获取异常用户列表（无异常用户）"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 获取异常用户列表
            result = CommunityDashboardService.get_abnormal_users(comm.community_id)

            assert result['users'] == []
            assert result['total'] == 0
            assert result['has_next'] is False

    def test_get_trend_data(self, test_session, test_app):
        """测试获取历史趋势数据"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 创建用户和规则
            user1 = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            test_session.commit()

            rule = self._create_community_rule(comm.community_id, admin.user_id, test_session)
            CommunityCheckinRuleService.enable_community_rule(rule.community_rule_id, admin.user_id)
            test_session.commit()

            # 创建用户规则关联（检查是否已存在）
            existing = test_session.query(UserCommunityRule).filter_by(
                user_id=user1.user_id,
                community_rule_id=rule.community_rule_id
            ).first()
            if not existing:
                mapping = UserCommunityRule(
                    user_id=user1.user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                test_session.add(mapping)
                test_session.commit()

            # 获取7天趋势数据
            trends = CommunityDashboardService.get_trend_data(comm.community_id, days=7)

            assert 'date_range' in trends
            assert 'checkin_rates' in trends
            assert 'rule_missed_stats' in trends
            assert len(trends['date_range']) == 7
            assert len(trends['checkin_rates']) == 7

    def test_get_trend_data_invalid_days(self, test_session, test_app):
        """测试获取趋势数据（无效天数参数）"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 使用无效的天数参数，应该默认使用7天
            trends = CommunityDashboardService.get_trend_data(comm.community_id, days=15)

            assert len(trends['date_range']) == 7

    def test_get_pending_events_empty(self, test_session, test_app):
        """测试获取未处理事件（无事件）"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 获取未处理事件
            events = CommunityDashboardService.get_pending_events(comm.community_id)

            assert events['events'] == []
            assert events['total'] == 0

    def test_get_user_abnormality_detail(self, test_session, test_app):
        """测试获取用户异常值详情"""
        with test_app.app_context():
            # 创建管理员
            admin = self._create_user(test_session, role=Role.SUPER_ADMIN)
            test_session.commit()

            # 创建社区
            comm = self._create_community_with_manager(test_session, admin.user_id)
            test_session.commit()

            # 创建用户
            user = self._create_user(test_session, role=Role.SOLO, community_id=comm.community_id)
            test_session.commit()

            # 创建规则
            rule = self._create_community_rule(comm.community_id, admin.user_id, test_session)
            CommunityCheckinRuleService.enable_community_rule(rule.community_rule_id, admin.user_id)
            test_session.commit()

            # 创建用户规则关联（检查是否已存在）
            existing = test_session.query(UserCommunityRule).filter_by(
                user_id=user.user_id,
                community_rule_id=rule.community_rule_id
            ).first()
            if not existing:
                mapping = UserCommunityRule(
                    user_id=user.user_id,
                    community_rule_id=rule.community_rule_id,
                    is_active=True
                )
                test_session.add(mapping)
                test_session.commit()

            # 创建异常值记录
            today = date.today()
            abnormality = UserDailyAbnormality(
                user_id=user.user_id,
                rule_id=rule.community_rule_id,
                date=today,
                total_abnormality=5,
                is_completed=False
            )
            test_session.add(abnormality)
            test_session.commit()

            # 获取用户异常值详情
            detail = CommunityDashboardService.get_user_abnormality_detail(comm.community_id, user.user_id)

            assert detail['user_id'] == user.user_id
            assert detail['total_abnormality'] == 5
            assert len(detail['rule_details']) == 1
