"""
测试社区位置和行政区划功能
"""
import pytest
from datetime import datetime
from sqlalchemy import select

from database.flask_models import Community, User
from wxcloudrun.community_service import CommunityService


class TestCommunityLocation:
    """测试社区位置和行政区划功能"""

    def test_create_community_with_location(self, test_session):
        """测试创建带位置信息的社区"""
        # 创建测试用户
        user = User(
            nickname='test_user',
            phone_number='13800138000',
            role=2,  # 普通用户
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建带位置信息的社区
        community = CommunityService.create_community(
            name='测试社区',
            description='测试描述',
            creator_id=user.user_id,
            location='北京市朝阳区某某街道123号',
            location_lat=39.9042,
            location_lon=116.4074,
            province='北京市',
            city='北京市',
            district='朝阳区',
            street='某某街道123号'
        )

        # 验证社区创建成功
        assert community.community_id is not None
        assert community.location == '北京市朝阳区某某街道123号'
        assert community.location_lat == 39.9042
        assert community.location_lon == 116.4074
        assert community.province == '北京市'
        assert community.city == '北京市'
        assert community.district == '朝阳区'
        assert community.street == '某某街道123号'

    def test_create_community_without_location(self, test_session):
        """测试创建不带位置信息的社区"""
        # 创建测试用户
        user = User(
            nickname='test_user',
            phone_number='13800138001',
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建不带位置信息的社区
        community = CommunityService.create_community(
            name='测试社区2',
            description='测试描述2',
            creator_id=user.user_id
        )

        # 验证社区创建成功，位置字段为空
        assert community.community_id is not None
        assert community.location is None
        assert community.location_lat is None
        assert community.location_lon is None
        assert community.province is None
        assert community.city is None
        assert community.district is None
        assert community.street is None

    def test_update_community_location(self, test_session):
        """测试更新社区位置信息"""
        # 创建测试用户和社区
        user = User(
            nickname='test_user',
            phone_number='13800138002',
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        community = CommunityService.create_community(
            name='测试社区3',
            description='测试描述3',
            creator_id=user.user_id
        )

        # 更新社区位置信息
        updated_community = CommunityService.update_community_info(
            community_id=community.community_id,
            location='上海市浦东新区张江高科技园区',
            location_lat=31.2304,
            location_lon=121.4737,
            province='上海市',
            city='上海市',
            district='浦东新区',
            street='张江高科技园区'
        )

        # 验证更新成功
        assert updated_community.location == '上海市浦东新区张江高科技园区'
        assert updated_community.location_lat == 31.2304
        assert updated_community.location_lon == 121.4737
        assert updated_community.province == '上海市'
        assert updated_community.city == '上海市'
        assert updated_community.district == '浦东新区'
        assert updated_community.street == '张江高科技园区'

    def test_partial_update_community_location(self, test_session):
        """测试部分更新社区位置信息"""
        # 创建测试用户和社区
        user = User(
            nickname='test_user',
            phone_number='13800138003',
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        community = CommunityService.create_community(
            name='测试社区4',
            description='测试描述4',
            creator_id=user.user_id,
            location='完整地址',
            location_lat=39.9042,
            location_lon=116.4074,
            province='北京市',
            city='北京市',
            district='朝阳区',
            street='某某街道'
        )

        # 只更新部分位置信息
        updated_community = CommunityService.update_community_info(
            community_id=community.community_id,
            street='更新后的街道'
        )

        # 验证部分更新成功
        assert updated_community.street == '更新后的街道'
        assert updated_community.province == '北京市'  # 其他字段保持不变
        assert updated_community.city == '北京市'
        assert updated_community.district == '朝阳区'

    def test_community_location_coordinates_validation(self, test_session):
        """测试社区位置坐标的有效性"""
        # 创建测试用户
        user = User(
            nickname='test_user',
            phone_number='13800138004',
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 测试有效的经纬度范围
        valid_lat = 39.9042  # 有效纬度
        valid_lon = 116.4074  # 有效经度

        community = CommunityService.create_community(
            name='测试社区5',
            description='测试描述5',
            creator_id=user.user_id,
            location_lat=valid_lat,
            location_lon=valid_lon
        )

        # 验证坐标保存成功
        assert community.location_lat == valid_lat
        assert community.location_lon == valid_lon

    def test_query_communities_by_location(self, test_session):
        """测试按位置查询社区"""
        # 创建测试用户
        user = User(
            nickname='test_user',
            phone_number='13800138005',
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建多个社区
        community1 = CommunityService.create_community(
            name='北京社区',
            description='北京',
            creator_id=user.user_id,
            location='北京市朝阳区',
            province='北京市',
            city='北京市',
            district='朝阳区'
        )

        community2 = CommunityService.create_community(
            name='上海社区',
            description='上海',
            creator_id=user.user_id,
            location='上海市浦东新区',
            province='上海市',
            city='上海市',
            district='浦东新区'
        )

        # 按省份查询
        stmt = select(Community).where(Community.province == '北京市')
        beijing_communities = test_session.execute(stmt).scalars().all()

        assert len(beijing_communities) == 1
        assert beijing_communities[0].community_id == community1.community_id