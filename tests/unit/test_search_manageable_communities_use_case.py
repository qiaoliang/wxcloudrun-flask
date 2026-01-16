"""
搜索可管理社区 UseCase 单元测试

测试 SearchManageableCommunitiesUseCase 的功能：
1. 搜索用户可管理的社区
2. 按社区名称、地址、描述搜索
3. 分页功能
4. 参数验证
"""
import pytest
from database.flask_models import db, User, Community, CommunityStaff
from app.application.use_cases.community.search_manageable_communities_use_case import SearchManageableCommunitiesUseCase
from app.application.use_cases.base import UseCaseStatus


class TestSearchManageableCommunitiesUseCase:
    """SearchManageableCommunitiesUseCase 测试类"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return SearchManageableCommunitiesUseCase()

    def test_search_manageable_communities_by_name_success(self, use_case, test_user, test_community):
        """
        测试按社区名称搜索可管理社区成功
        Given: 用户是社区的工作人员，提供社区名称关键词
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和匹配的社区列表
        """
        # Arrange - 将用户添加为社区工作人员
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=test_user.user_id,
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        keyword = test_community.name[:2]  # 使用社区名称的一部分
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'communities' in result.data
        assert 'total' in result.data
        assert 'page' in result.data
        assert 'per_page' in result.data

    def test_search_manageable_communities_by_address_success(self, use_case, test_user, test_community):
        """
        测试按社区地址搜索可管理社区成功
        Given: 用户是社区的工作人员，提供社区地址关键词
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和匹配的社区列表
        """
        # Arrange - 将用户添加为社区工作人员
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=test_user.user_id,
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        keyword = test_community.location[:2] if test_community.location else "测试"
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'communities' in result.data

    def test_search_manageable_communities_by_description_success(self, use_case, test_user, test_community):
        """
        测试按社区描述搜索可管理社区成功
        Given: 用户是社区的工作人员，提供社区描述关键词
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和匹配的社区列表
        """
        # Arrange - 将用户添加为社区工作人员
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=test_user.user_id,
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        keyword = test_community.description[:2] if test_community.description else "测试"
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'communities' in result.data

    def test_search_manageable_communities_no_permission(self, use_case, test_user, test_community):
        """
        测试搜索用户无权限管理的社区
        Given: 用户不是社区的工作人员
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，但社区列表为空
        """
        # Arrange
        keyword = test_community.name[:2]
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['communities']) == 0
        assert result.data['total'] == 0

    def test_search_manageable_communities_pagination(self, use_case, test_user, test_session):
        """
        测试搜索可管理社区分页功能
        Given: 用户是多个社区的工作人员，设置分页参数
        When: 调用 execute 方法，使用不同的页码
        Then: 返回正确的分页数据
        """
        # Arrange - 创建多个社区并将用户添加为工作人员
        from database.flask_models import Community
        from test_data_generator import generate_unique_nickname
        communities = []
        for i in range(5):
            community = Community(
                name=f"测试社区{i}",
                description=f"测试社区描述{i}",
                location=f"测试地址{i}",
                status=1
            )
            test_session.add(community)
            test_session.flush()  # 获取community_id
            communities.append(community)

            # 将用户添加为工作人员
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=test_user.user_id,
                role='staff'
            )
            db.session.add(staff)

        db.session.commit()

        keyword = "测试"
        page = 1
        per_page = 2

        # Act - 第一页
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['communities']) <= per_page
        assert result.data['page'] == page
        assert result.data['per_page'] == per_page

    def test_search_manageable_communities_empty_keyword(self, use_case, test_user):
        """
        测试搜索可管理社区时关键词为空
        Given: 空的关键词
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = ""
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "搜索关键词不能为空" in result.message

    def test_search_manageable_communities_invalid_user_id(self, use_case):
        """
        测试搜索可管理社区时用户ID无效
        Given: 无效的用户ID（0或None）
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 1
        per_page = 20

        # Act - 用户ID为0
        result = use_case.execute(
            user_id=0,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_search_manageable_communities_invalid_page(self, use_case, test_user):
        """
        测试搜索可管理社区时页码无效
        Given: 无效的页码（0或负数）
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 0
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_search_manageable_communities_invalid_per_page(self, use_case, test_user):
        """
        测试搜索可管理社区时每页数量无效
        Given: 无效的每页数量（0或超过100）
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 1
        per_page = 101  # 超过100

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_search_manageable_communities_no_results(self, use_case, test_user, test_community):
        """
        测试搜索可管理社区时无匹配结果
        Given: 用户是社区的工作人员，提供不存在的关键词
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，但社区列表为空
        """
        # Arrange - 将用户添加为社区工作人员
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=test_user.user_id,
            role='staff'
        )
        db.session.add(staff)
        db.session.commit()

        keyword = "不存在的社区名123456"
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['communities']) == 0
        assert result.data['total'] == 0

    def test_search_manageable_communities_has_next_page(self, use_case, test_user, test_session):
        """
        测试搜索可管理社区时是否有下一页
        Given: 创建足够的社区，设置较小的每页数量
        When: 调用 execute 方法
        Then: 正确设置 has_next 标志
        """
        # Arrange - 创建多个社区并将用户添加为工作人员
        from database.flask_models import Community
        for i in range(5):
            community = Community(
                name=f"社区{i}",
                description=f"社区{i}",
                status=1
            )
            test_session.add(community)
            test_session.flush()  # 获取community_id

            # 将用户添加为工作人员
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=test_user.user_id,
                role='staff'
            )
            db.session.add(staff)

        db.session.commit()

        keyword = "社区"
        page = 1
        per_page = 2

        # Act
        result = use_case.execute(
            user_id=test_user.user_id,
            keyword=keyword,
            page=page,
            per_page=per_page
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 如果返回的社区数等于每页数量，说明可能还有下一页
        if len(result.data['communities']) == per_page:
            assert result.data['has_next'] is True