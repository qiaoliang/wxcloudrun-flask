"""
测试社区位置和行政区划功能
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from hashlib import sha256

from database.flask_models import Community, User
from wxcloudrun.community_service import CommunityService
from test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname
)
from test_constants import TEST_CONSTANTS


class TestCommunityLocation:
    """测试社区位置和行政区划功能"""

    def test_create_community_with_location(self, test_session):
        """测试创建带位置信息的社区"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_create_community_with_location")
        openid = generate_unique_openid(phone_number, "test_create_community_with_location")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_create_community_with_location"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,  # 普通用户
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建带位置信息的社区
        community = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("with_location"),
            description=TEST_CONSTANTS.generate_community_description("with_location"),
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
        phone_number = generate_unique_phone_number("test_create_community_without_location")
        openid = generate_unique_openid(phone_number, "test_create_community_without_location")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_create_community_without_location"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 创建不带位置信息的社区
        community = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("without_location"),
            description=TEST_CONSTANTS.generate_community_description("without_location"),
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
        phone_number = generate_unique_phone_number("test_update_community_location")
        openid = generate_unique_openid(phone_number, "test_update_community_location")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_update_community_location"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        community = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("update_location"),
            description=TEST_CONSTANTS.generate_community_description("update_location"),
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
        phone_number = generate_unique_phone_number("test_partial_update_community_location")
        openid = generate_unique_openid(phone_number, "test_partial_update_community_location")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_partial_update_community_location"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        community = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("partial_update"),
            description=TEST_CONSTANTS.generate_community_description("partial_update"),
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
        phone_number = generate_unique_phone_number("test_community_location_coordinates_validation")
        openid = generate_unique_openid(phone_number, "test_community_location_coordinates_validation")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_community_location_coordinates_validation"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 测试有效的经纬度范围
        valid_lat = 39.9042  # 有效纬度
        valid_lon = 116.4074  # 有效经度

        community = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("coordinates_validation"),
            description=TEST_CONSTANTS.generate_community_description("coordinates_validation"),
            creator_id=user.user_id,
            location_lat=valid_lat,
            location_lon=valid_lon
        )

        # 验证坐标保存成功
        assert community.location_lat == valid_lat
        assert community.location_lon == valid_lon

    def test_query_communities_by_province(self, test_session):
        """测试按位置查询社区"""
        # 创建测试用户
        phone_number = generate_unique_phone_number("test_query_communities_by_location")
        openid = generate_unique_openid(phone_number, "test_query_communities_by_location")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            nickname=generate_unique_nickname("test_query_communities_by_location"),
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            role=2,
            status=1
        )
        test_session.add(user)
        test_session.flush()
        # 按省份查询
        stmt = select(Community).where(Community.province == '北京市')
        org_beijing_communities = test_session.execute(stmt).scalars().all()
        # 创建多个社区
        community1 = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("beijing"),
            description='北京',
            creator_id=user.user_id,
            location='北京市朝阳区',
            province='北京市',
            city='北京市',
            district='朝阳区'
        )

        community2 = CommunityService.create_community(
            name=TEST_CONSTANTS.generate_community_name("shanghai"),
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

        assert len(beijing_communities) == len(org_beijing_communities)+1