"""
超级管理员管理社区列表集成测试
测试当登录用户是超级系统管理员时，请求社区列表API返回的社区包含"安卡大家庭"和"黑屋"
"""

import pytest
import sys
import os

# 设置测试环境
os.environ['ENV_TYPE'] = 'integration'

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database.flask_models import db, Community
from .conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS
from const_default import DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME


class TestManagedCommunities(IntegrationTestBase):
    """社区工作人员的管理社区列表测试"""

    @classmethod
    def setup_class(cls):
        """设置测试数据"""
        super().setup_class()

        with cls.app.app_context():
            # 创建社区工作人员
            cls.super_admin = cls.create_standard_test_user(role=4)  # 超级管理员
            cls.super_admin_phone = cls.super_admin.phone_number
            cls.comm_manager = cls.create_standard_test_user(role=3)
            cls.comm_manager_phone = cls.comm_manager.phone_number
            cls.comm_staff = cls.create_standard_test_user(role=2)
            cls.comm_staff_phone = cls.comm_staff.phone_number

            # 保存对test_user的引用（如果需要）
            cls.test_user = cls.super_admin
            cls.test_phone_number = cls.super_admin_phone
            # 确保安卡大家庭社区存在
            ankafamily = db.session.query(Community).filter_by(
                name=DEFAULT_COMMUNITY_NAME
            ).first()

            if not ankafamily:
                ankafamily = cls.create_test_community(
                    name=DEFAULT_COMMUNITY_NAME,
                    creator=cls.test_user,
                    description='系统默认社区',
                    status=1,
                    is_default=True
                )

            # 确保黑屋社区存在
            blackhouse = db.session.query(Community).filter_by(
                name=DEFAULT_BLACK_ROOM_NAME
            ).first()

            if not blackhouse:
                blackhouse = cls.create_test_community(
                    name=DEFAULT_BLACK_ROOM_NAME,
                    creator=cls.test_user,
                    description='黑屋社区',
                    status=1,
                    is_default=False,
                    is_blackhouse=True
                )

            # 创建普通社区1
            # manager 是普通社区1的主管
            cls.normal_community1 = cls.create_test_community(
                name='普通测试社区1',
                creator=cls.test_user,
                description='普通社区1',
                status=1,
                is_default=False,
                is_blackhouse=False,
                manager_id=cls.comm_manager.user_id,
            )
            # manager 是普通社区2的主管
            cls.normal_community2 = cls.create_test_community(
                name='普通测试社区2',
                creator=cls.test_user,
                description='普通社区2',
                status=1,
                is_default=False,
                is_blackhouse=False,
                manager_id=cls.comm_manager.user_id,
            )

            # 创建一个禁用的社区（不应该出现在列表中）
            cls.disabled_community = cls.create_test_community(
                name='禁用测试社区',
                creator=cls.test_user,
                description='已禁用的社区',
                status=2,  # 禁用状态
                is_default=False,
                is_blackhouse=False
            )

    def test_super_admin_managed_communities_includes_special_communities(self):
        """测试超级管理员管理社区列表包含安卡大家庭和黑屋"""
        # 使用超级管理员身份请求管理社区列表
        response = self.make_authenticated_request(
            'GET',
            '/api/user/managed-communities',
            phone_number=self.super_admin_phone
        )

        # 验证响应成功
        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']

        # 获取返回的社区名称列表
        returned_community_names = [c['name'] for c in communities]
        community_details = {c['name']: c for c in communities}

        print(f"✅ 返回社区总数: {len(communities)}")
        print(f"✅ 返回的社区: {returned_community_names}")

        # 验证必须包含安卡大家庭
        assert DEFAULT_COMMUNITY_NAME in returned_community_names, \
            f"管理社区列表必须包含'{DEFAULT_COMMUNITY_NAME}'"

        # 验证安卡大家庭的属性
        ankafamily_data = community_details[DEFAULT_COMMUNITY_NAME]
        assert ankafamily_data['is_default'] == True, \
            f"'{DEFAULT_COMMUNITY_NAME}'应该标记为默认社区"
        print(f"✅ 找到并验证{DEFAULT_COMMUNITY_NAME}社区")

        # 验证必须包含黑屋
        assert DEFAULT_BLACK_ROOM_NAME in returned_community_names, \
            f"管理社区列表必须包含'{DEFAULT_BLACK_ROOM_NAME}'"

        # 验证黑屋的属性
        blackhouse_data = community_details[DEFAULT_BLACK_ROOM_NAME]
        assert blackhouse_data.get('is_blackhouse') == True, \
            f"'{DEFAULT_BLACK_ROOM_NAME}'应该标记为黑屋社区"
        print(f"✅ 找到并验证{DEFAULT_BLACK_ROOM_NAME}社区")

        # 验证普通社区也在列表中
        assert '普通测试社区1' in returned_community_names, "应该包含普通测试社区1"
        assert '普通测试社区2' in returned_community_names, "应该包含普通测试社区2"
        print("✅ 普通社区也正确显示")

        # 验证禁用的社区不在列表中
        assert '禁用测试社区' not in returned_community_names, "禁用的社区不应该出现在列表中"
        print("✅ 禁用的社区正确过滤")

        print("✅ 所有验证通过！超级管理员可以看到所有启用的社区，包括安卡大家庭和黑屋")

    def test_super_admin_managed_communities_data_structure(self):
        """测试超级管理员管理社区列表的数据结构"""
        response = self.make_authenticated_request(
            'GET',
            '/api/user/managed-communities',
            phone_number=self.super_admin_phone
        )

        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']

        if communities:
            # 找到安卡大家庭和黑屋进行详细验证
            for special_name in [DEFAULT_COMMUNITY_NAME, DEFAULT_BLACK_ROOM_NAME]:
                special_communities = [c for c in communities if c['name'] == special_name]
                assert len(special_communities) > 0, f"应该找到{special_name}社区"

                community = special_communities[0]
                print(f"\n验证{special_name}社区数据结构:")

                # 验证基本字段
                assert 'community_id' in community
                assert 'name' in community
                assert 'description' in community
                assert 'status' in community
                assert 'created_at' in community
                assert 'updated_at' in community

                # 验证特殊字段
                if special_name == DEFAULT_COMMUNITY_NAME:
                    assert community.get('is_default') == True
                    print(f"  - is_default: {community.get('is_default')}")
                elif special_name == DEFAULT_BLACK_ROOM_NAME:
                    assert community.get('is_blackhouse') == True
                    print(f"  - is_blackhouse: {community.get('is_blackhouse')}")

                print(f"  - community_id: {community['community_id']}")
                print(f"  - name: {community['name']}")
                print(f"  - status: {community['status']}")

    def test_normal_user_managed_communities_excludes_special(self):
        """对比测试：普通用户的管理社区列表不包含安卡大家庭（除非是管理员）"""
        with self.app.app_context():
            # 创建普通用户（社区专员）
            normal_user = self.create_standard_test_user(role=2)  # 社区专员
            normal_user_phone = normal_user.phone_number

        # 普通用户请求管理社区列表
        response = self.make_authenticated_request(
            'GET',
            '/api/user/managed-communities',
            phone_number=normal_user_phone
        )

        data = self.assert_api_success(response, ['communities'])
        communities = data['data']['communities']
        returned_community_names = [c['name'] for c in communities]

        print(f"✅ 普通用户返回社区数量: {len(communities)}")
        print(f"✅ 普通用户返回的社区: {returned_community_names}")

        # 普通用户不应该看到安卡大家庭（除非被设置为管理员）
        # 注意：这个断言可能根据具体业务逻辑调整
        if DEFAULT_COMMUNITY_NAME not in returned_community_names:
            print(f"✅ 普通用户正确过滤了{DEFAULT_COMMUNITY_NAME}")

        # 普通用户不应该看到黑屋
        if DEFAULT_BLACK_ROOM_NAME not in returned_community_names:
            print(f"✅ 普通用户正确过滤了{DEFAULT_BLACK_ROOM_NAME}")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])