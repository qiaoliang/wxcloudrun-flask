"""
社区数字看板 API 集成测试
Happy path: 成功获取统计数据、异常用户列表、趋势数据、未处理事件
"""

import pytest
import json
import os
import sys

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from tests.integration.conftest import IntegrationTestBase
from app.shared.constants.roles import Role


class TestCommunityDashboardRoutes(IntegrationTestBase):
    """社区数字看板 API 集成测试"""

    def _get_user_by_admin_info(self, admin_info):
        """根据admin信息获取用户对象"""
        from database.flask_models import User
        return self.db.session.query(User).filter_by(user_id=admin_info['user_id']).first()

    def test_get_community_stats_success(self):
        """测试成功获取社区统计数据"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('get_stats')
            test_client = self.get_test_client()

            # 创建社区（使用user_id而不是phone_number查询）
            from database.flask_models import User
            admin_user = self.db.session.query(User).filter_by(user_id=admin['user_id']).first()
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 创建用户
            user1 = self.create_standard_test_user(role=Role.SOLO, test_context='stats_user1')
            user2 = self.create_standard_test_user(role=Role.SOLO, test_context='stats_user2')
            user1.community_id = comm.community_id
            user2.community_id = comm.community_id
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送获取统计数据请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/stats',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'total_users' in data['data']
            assert 'today_checkin_rate' in data['data']
            assert 'unchecked_count' in data['data']
            assert 'total_rules' in data['data']

    def test_get_community_stats_permission_denied(self):
        """测试普通用户无权限获取统计数据"""
        with self.app.app_context():
            # 创建普通用户
            solo_user = self.create_standard_test_user(role=Role.SOLO, test_context='no_perm_user')
            test_client = self.get_test_client()

            # 创建社区
            manager = self.create_standard_test_user(role=Role.MANAGER, test_context='no_perm_manager')
            comm = self.create_test_community(creator=manager)
            self.db.session.commit()

            solo_user.community_id = comm.community_id
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(solo_user.phone_number)

            # 发送请求（应该失败）
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/stats',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应为权限错误 (decorator或route都可能返回权限错误)
            data = self.assert_api_error(response, expected_code=0)
            # Error message could be from decorator or from route-level check
            # Both should result in code=0
            assert data['code'] == 0

    def test_get_abnormal_users_success(self):
        """测试成功获取异常用户列表"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('abnormal_users')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 创建用户
            user1 = self.create_standard_test_user(role=Role.SOLO, test_context='abnormal_user1')
            user1.community_id = comm.community_id
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送获取异常用户列表请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/abnormal-users',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'users' in data['data']
            assert 'total' in data['data']
            assert 'page' in data['data']

    def test_get_abnormal_users_with_pagination(self):
        """测试异常用户列表分页"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('pagination')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送带分页参数的请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/abnormal-users?page=1&page_size=10',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert data['data']['page'] == 1
            assert 'has_next' in data['data']

    def test_get_trend_data_success(self):
        """测试成功获取历史趋势数据"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('trend_data')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送获取7天趋势数据请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/trends?days=7',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'date_range' in data['data']
            assert 'checkin_rates' in data['data']
            assert 'rule_missed_stats' in data['data']
            assert len(data['data']['date_range']) == 7

    def test_get_trend_data_invalid_days(self):
        """测试获取趋势数据（无效天数参数）"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('invalid_days')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送带无效天数参数的请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/trends?days=15',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 应该返回错误
            data = self.assert_api_error(response, expected_code=0)
            assert '天数' in data['msg'] or '7' in data['msg']

    def test_get_pending_events_success(self):
        """测试成功获取未处理事件"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('pending_events')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送获取未处理事件请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/pending-events',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'events' in data['data']
            assert 'total' in data['data']

    def test_get_pending_events_with_limit(self):
        """测试获取未处理事件（带数量限制）"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('events_limit')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送带limit参数的请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/pending-events?limit=5',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'events' in data['data']
            assert 'total' in data['data']

    def test_get_user_abnormality_detail_success(self):
        """测试成功获取用户异常值详情"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('user_detail')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建社区
            comm = self.create_test_community(creator=admin_user)
            self.db.session.commit()

            # 创建用户
            user = self.create_standard_test_user(role=Role.SOLO, test_context='detail_user')
            user.community_id = comm.community_id
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 发送获取用户异常值详情请求
            response = test_client.get(
                f'/api/community-dashboard/{comm.community_id}/user-abnormality/{user.user_id}',
                headers={'Authorization': f'Bearer {token}'}
            )

            # 验证响应
            data = self.assert_api_success(response)
            assert 'user_id' in data['data']
            assert 'total_abnormality' in data['data']
            assert 'rule_details' in data['data']

    def test_community_isolation(self):
        """测试社区数据隔离（不同社区的数据不混）"""
        with self.app.app_context():
            # 创建超级管理员
            admin = self.get_super_admin('isolation')
            admin_user = self._get_user_by_admin_info(admin)
            test_client = self.get_test_client()

            # 创建两个社区
            comm1 = self.create_test_community(creator=admin_user, name='社区1')
            comm2 = self.create_test_community(creator=admin_user, name='社区2')
            self.db.session.commit()

            # 为社区1创建用户
            user1 = self.create_standard_test_user(role=Role.SOLO, test_context='isolation_user1')
            user1.community_id = comm1.community_id
            self.db.session.commit()

            # 获取JWT token
            token = self.get_jwt_token(admin['phone_number'])

            # 获取社区1的统计数据
            response1 = test_client.get(
                f'/api/community-dashboard/{comm1.community_id}/stats',
                headers={'Authorization': f'Bearer {token}'}
            )
            data1 = self.assert_api_success(response1)

            # 获取社区2的统计数据
            response2 = test_client.get(
                f'/api/community-dashboard/{comm2.community_id}/stats',
                headers={'Authorization': f'Bearer {token}'}
            )
            data2 = self.assert_api_success(response2)

            # 验证两个社区的数据不同
            assert data1['data']['total_users'] != data2['data']['total_users'] or \
                   data1['data']['total_rules'] != data2['data']['total_rules']

    def test_manager_can_only_access_own_community(self):
        """测试社区主管只能访问自己管理的社区"""
        with self.app.app_context():
            # 创建两个社区主管
            manager1 = self.create_standard_test_user(role=Role.MANAGER, test_context='manager1')
            manager2 = self.create_standard_test_user(role=Role.MANAGER, test_context='manager2')

            # 创建两个社区 (使用唯一名称避免UNIQUE约束错误)
            comm1 = self.create_test_community(creator=manager1, name='社区1_isolation')
            comm2 = self.create_test_community(creator=manager2, name='社区2_isolation')
            self.db.session.commit()

            # manager1 属于 comm1
            manager1.community_id = comm1.community_id
            self.db.session.commit()

            test_client = self.get_test_client()

            # manager1 获取自己的社区数据 - 应该成功
            token1 = self.get_jwt_token(manager1.phone_number)
            response1 = test_client.get(
                f'/api/community-dashboard/{comm1.community_id}/stats',
                headers={'Authorization': f'Bearer {token1}'}
            )
            self.assert_api_success(response1)

            # manager1 尝试获取 comm2 的数据 - 应该失败
            response2 = test_client.get(
                f'/api/community-dashboard/{comm2.community_id}/stats',
                headers={'Authorization': f'Bearer {token1}'}
            )
            self.assert_api_error(response2, expected_code=0)
