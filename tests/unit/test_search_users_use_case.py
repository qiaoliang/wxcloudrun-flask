"""
搜索用户 UseCase 单元测试

测试 SearchUsersUseCase 的功能：
1. 按手机号搜索用户
2. 按昵称搜索用户
3. 全局搜索（手机号或昵称）
4. 排除黑名单房间搜索
5. 分页功能
6. 参数验证
"""
import pytest
from database.flask_models import db, User, Community
from app.application.use_cases.community.search_users_use_case import SearchUsersUseCase
from app.application.use_cases.base import UseCaseStatus
from test_data_generator import generate_unique_phone_number, generate_unique_openid


class TestSearchUsersUseCase:
    """SearchUsersUseCase 测试类"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return SearchUsersUseCase()

    def test_search_users_by_phone_success(self, use_case, test_user):
        """
        测试按手机号搜索用户成功
        Given: 有效的手机号关键词和分页参数
        When: 调用 execute 方法，搜索类型为 phone
        Then: 返回 SUCCESS 状态和匹配的用户列表
        """
        # Arrange
        keyword = test_user.phone_number[:5]  # 使用手机号的一部分
        page = 1
        per_page = 20
        search_type = 'phone'

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page, search_type=search_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'users' in result.data
        assert 'total' in result.data
        assert 'page' in result.data
        assert 'per_page' in result.data

    def test_search_users_by_nickname_success(self, use_case, test_user):
        """
        测试按昵称搜索用户成功
        Given: 有效的昵称关键词和分页参数
        When: 调用 execute 方法，搜索类型为 nickname
        Then: 返回 SUCCESS 状态和匹配的用户列表
        """
        # Arrange
        keyword = test_user.nickname[:2]  # 使用昵称的一部分
        page = 1
        per_page = 20
        search_type = 'nickname'

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page, search_type=search_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'users' in result.data
        assert 'total' in result.data

    def test_search_users_all_type_success(self, use_case, test_user):
        """
        测试全局搜索用户成功
        Given: 有效的关键词和分页参数
        When: 调用 execute 方法，搜索类型为 all
        Then: 返回 SUCCESS 状态和匹配的用户列表（手机号或昵称）
        """
        # Arrange
        keyword = test_user.nickname[:2]
        page = 1
        per_page = 20
        search_type = 'all'

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page, search_type=search_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'users' in result.data
        assert 'total' in result.data

    def test_search_users_excluding_blackroom(self, use_case, test_user, test_community):
        """
        测试排除黑名单房间搜索
        Given: 有效的关键词和分页参数，要求排除黑名单房间
        When: 调用 execute 方法，exclude_blackroom=True
        Then: 返回 SUCCESS 状态和排除黑名单房间的用户列表
        """
        # Arrange
        keyword = test_user.nickname[:2]
        page = 1
        per_page = 20
        exclude_blackroom = True

        # Act
        result = use_case.execute(
            keyword=keyword,
            page=page,
            per_page=per_page,
            search_type='all',
            exclude_blackroom=exclude_blackroom
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索成功" in result.message
        assert 'users' in result.data

    def test_search_users_pagination(self, use_case, test_session):
        """
        测试搜索用户分页功能
        Given: 创建多个用户，设置分页参数
        When: 调用 execute 方法，使用不同的页码
        Then: 返回正确的分页数据
        """
        # Arrange - 创建多个用户
        from database.flask_models import User
        from test_data_generator import generate_unique_phone_number, generate_unique_nickname
        for i in range(5):
            phone = generate_unique_phone_number()
            user = User(
                phone_number=phone,
                nickname=f"测试用户{i}",
                name=f"测试{i}",
                wechat_openid=generate_unique_openid(phone),
                role=1,
                status=1
            )
            test_session.add(user)
        test_session.commit()

        keyword = "测试"
        page = 1
        per_page = 2

        # Act - 第一页
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page, search_type='nickname')

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['users']) <= per_page
        assert result.data['page'] == page
        assert result.data['per_page'] == per_page

    def test_search_users_empty_keyword(self, use_case):
        """
        测试搜索用户时关键词为空
        Given: 空的关键词
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = ""
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "搜索关键词不能为空" in result.message

    def test_search_users_invalid_page(self, use_case):
        """
        测试搜索用户时页码无效
        Given: 无效的页码（0或负数）
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 0
        per_page = 20

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_search_users_invalid_per_page(self, use_case):
        """
        测试搜索用户时每页数量无效
        Given: 无效的每页数量（0或超过100）
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 1
        per_page = 101  # 超过100

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_search_users_no_results(self, use_case, test_app):
        """
        测试搜索用户时无匹配结果
        Given: 不存在的关键词
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，但用户列表为空
        """
        # Arrange
        keyword = "不存在的用户名123456"
        page = 1
        per_page = 20

        # Act - 在应用上下文中执行
        with test_app.app_context():
            result = use_case.execute(keyword=keyword, page=page, per_page=per_page)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['users']) == 0
        assert result.data['total'] == 0

    def test_search_users_has_next_page(self, use_case, test_session):
        """
        测试搜索用户时是否有下一页
        Given: 创建足够的用户，设置较小的每页数量
        When: 调用 execute 方法
        Then: 正确设置 has_next 标志
        """
        # Arrange - 创建多个用户
        from database.flask_models import User
        from test_data_generator import generate_unique_phone_number, generate_unique_openid
        for i in range(5):
            phone = generate_unique_phone_number()
            user = User(
                phone_number=phone,
                nickname=f"用户{i}",
                name=f"用户{i}",
                wechat_openid=generate_unique_openid(phone),
                role=1,
                status=1
            )
            test_session.add(user)
        test_session.commit()

        keyword = "用户"
        page = 1
        per_page = 2

        # Act
        result = use_case.execute(keyword=keyword, page=page, per_page=per_page, search_type='nickname')

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 如果返回的用户数等于每页数量，说明可能还有下一页
        if len(result.data['users']) == per_page:
            assert result.data['has_next'] is True