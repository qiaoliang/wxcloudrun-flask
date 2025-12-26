"""
测试社区列表中主管昵称的显示
验证返回的 manager_name 字段使用的是 nickname 而不是 name
"""
import pytest
import sys
import os

# 添加上级目录到路径以导入测试工具
tests_path = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, tests_path)

from database.flask_models import User, Community
from .conftest import IntegrationTestBase


class TestManagerNicknameDisplay(IntegrationTestBase):
    """测试主管昵称显示"""

    @classmethod
    def setup_class(cls):
        """类级别的设置"""
        super().setup_class()
        # 获取超级管理员用户
        with cls.app.app_context():
            cls.super_admin = cls.get_super_admin()
            cls.super_admin_id = cls.super_admin['user_id']
            cls.super_admin_phone = cls.super_admin['phone_number']

    def setup_method(self, method):
        """每个测试方法前的设置"""
        super().setup_method(method)

    def test_manager_name_should_be_nickname_not_real_name(self):
        """测试返回的 manager_name 应该是 nickname 而不是真实姓名"""
        with self.app.app_context():
            # 创建测试用户，nickname 和 name 不同
            test_user = User(
                wechat_openid='test_manager_user',
                phone_number='13800008888',
                nickname='测试主管昵称',
                name='测试主管真实姓名',  # 真实姓名
                role=3  # 社区主管
            )
            self.db.session.add(test_user)
            self.db.session.commit()

            # 创建社区并设置主管
            community = Community(
                name='测试社区',
                description='测试描述',
                creator_id=self.super_admin_id,
                manager_id=test_user.user_id
            )
            self.db.session.add(community)
            self.db.session.commit()

            # 调用获取社区列表 API
            response = self.make_authenticated_request(
                'GET',
                '/api/communities',
                phone_number=self.super_admin_phone
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['code'] == 1

            communities = data['data']['communities']
            test_community = next((c for c in communities if c['community_id'] == community.community_id), None)
            assert test_community is not None

            # 验证 manager_name 是 nickname 而不是真实姓名
            assert test_community['manager_name'] == '测试主管昵称', \
                f"manager_name 应该是 nickname '测试主管昵称'，但实际是 '{test_community['manager_name']}'"

            # 验证 manager 对象中的 nickname
            assert test_community['manager']['nickname'] == '测试主管昵称', \
                f"manager.nickname 应该是 '测试主管昵称'，但实际是 '{test_community['manager']['nickname']}'"

            # 验证不是真实姓名
            assert test_community['manager_name'] != '测试主管真实姓名', \
                "manager_name 不应该是真实姓名"

    def test_manager_name_with_none_nickname(self):
        """测试当 nickname 为 None 时的处理"""
        with self.app.app_context():
            # 创建测试用户（nickname 为 None）
            test_user = User(
                wechat_openid='test_manager_no_nickname',
                phone_number='13800009999',
                nickname=None,
                name='测试主管真实姓名',
                role=3
            )
            self.db.session.add(test_user)
            self.db.session.commit()

            # 创建社区并设置主管
            community = Community(
                name='测试社区2',
                description='测试描述',
                creator_id=self.super_admin_id,
                manager_id=test_user.user_id
            )
            self.db.session.add(community)
            self.db.session.commit()

            # 调用获取社区列表 API
            response = self.make_authenticated_request(
                'GET',
                '/api/communities',
                phone_number=self.super_admin_phone
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['code'] == 1

            communities = data['data']['communities']
            test_community = next((c for c in communities if c['community_id'] == community.community_id), None)
            assert test_community is not None

            # 当 nickname 为 None 时，manager_name 也应该是 None
            assert test_community['manager_name'] is None

    def test_manager_name_with_empty_nickname(self):
        """测试当 nickname 为空字符串时的处理"""
        with self.app.app_context():
            # 创建测试用户（nickname 为空字符串）
            test_user = User(
                wechat_openid='test_manager_empty_nickname',
                phone_number='13800007777',
                nickname='',  # 空字符串
                name='测试主管真实姓名',
                role=3
            )
            self.db.session.add(test_user)
            self.db.session.commit()

            # 创建社区并设置主管
            community = Community(
                name='测试社区3',
                description='测试描述',
                creator_id=self.super_admin_id,
                manager_id=test_user.user_id
            )
            self.db.session.add(community)
            self.db.session.commit()

            # 调用获取社区列表 API
            response = self.make_authenticated_request(
                'GET',
                '/api/communities',
                phone_number=self.super_admin_phone
            )

            assert response.status_code == 200
            data = response.get_json()
            assert data['code'] == 1

            communities = data['data']['communities']
            test_community = next((c for c in communities if c['community_id'] == community.community_id), None)
            assert test_community is not None

            # 当 nickname 为空字符串时，manager_name 也应该是空字符串
            assert test_community['manager_name'] == ''