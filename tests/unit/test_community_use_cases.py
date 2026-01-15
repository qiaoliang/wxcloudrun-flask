"""
社区管理模块 UseCases 单元测试

测试以下 UseCase：
1. CreateCommunityUseCase - 创建社区
2. DeleteCommunityUseCase - 删除社区
3. UpdateCommunityUseCase - 更新社区
4. GetCommunityDetailsUseCase - 获取社区详情
5. JoinCommunityUseCase - 加入社区
6. LeaveCommunityUseCase - 离开社区
7. SearchCommunityUseCase - 搜索社区
8. ListCommunityUsersUseCase - 列出社区用户

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from database.flask_models import User, Community
from app.application.use_cases.community.create_community_use_case import CreateCommunityUseCase
from app.application.use_cases.community.delete_community_use_case import DeleteCommunityUseCase
from app.application.use_cases.community.update_community_use_case import UpdateCommunityUseCase
from app.application.use_cases.community.get_community_details_use_case import GetCommunityDetailsUseCase
from app.application.use_cases.community.join_community_use_case import JoinCommunityUseCase
from app.application.use_cases.community.leave_community_use_case import LeaveCommunityUseCase
from app.application.use_cases.community.search_community_use_case import SearchCommunityUseCase
from app.application.use_cases.community.list_community_users_use_case import ListCommunityUsersUseCase
from app.application.use_cases.base import UseCaseStatus


class TestCreateCommunityUseCase:
    """CreateCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CreateCommunityUseCase()

    def test_validate_success(self, use_case, test_user):
        """
        测试验证成功
        Given: 有效的社区名称和创建者ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        name = "测试社区"
        description = "这是一个测试社区"
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "社区创建成功" in result.message
        assert result.data['community_id'] > 0
        assert result.data['name'] == name

    def test_validate_missing_name(self, use_case, test_user):
        """
        测试验证失败 - 缺少社区名称
        Given: 社区名称为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        name = ""
        description = "测试描述"
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区名称不能为空" in result.message

    def test_validate_whitespace_name(self, use_case, test_user):
        """
        测试验证失败 - 社区名称只有空格
        Given: 社区名称只有空格
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        name = "   "
        description = "测试描述"
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区名称不能为空" in result.message

    def test_validate_creator_not_found(self, use_case):
        """
        测试验证失败 - 创建者不存在
        Given: 创建者ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        name = "测试社区"
        description = "测试描述"
        creator_id = 999999

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "创建者不存在" in result.message

    def test_validate_duplicate_name(self, use_case, test_user, test_community):
        """
        测试验证失败 - 社区名称已存在
        Given: 社区名称已存在
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        name = test_community.name
        description = "测试描述"
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "社区名称已存在" in result.message

    def test_execute_with_all_parameters(self, use_case, test_user):
        """
        测试执行成功 - 使用所有参数
        Given: 有效的所有参数
        When: 调用 execute 方法
        Then: 成功创建社区并返回完整信息
        """
        # Arrange
        name = "完整测试社区"
        description = "这是一个完整的测试社区"
        creator_id = test_user.user_id
        location = "北京市朝阳区"
        settings = {"max_users": 100, "allow_join": True}
        manager_id = test_user.user_id
        location_lat = 39.9042
        location_lon = 116.4074
        province = "北京市"
        city = "北京市"
        district = "朝阳区"
        street = "望京街道"

        # Act
        result = use_case.execute(
            name=name,
            description=description,
            creator_id=creator_id,
            location=location,
            settings=settings,
            manager_id=manager_id,
            location_lat=location_lat,
            location_lon=location_lon,
            province=province,
            city=city,
            district=district,
            street=street
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['community_id'] > 0
        assert result.data['name'] == name
        assert result.data['description'] == description
        assert result.data['creator_id'] == creator_id

    def test_execute_with_default_description(self, use_case, test_user):
        """
        测试执行成功 - 使用默认描述
        Given: 描述为空
        When: 调用 execute 方法
        Then: 使用默认描述
        """
        # Arrange
        name = "默认描述社区"
        description = None
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['description'] == f'{name}的描述'

    def test_execute_with_settings_dict(self, use_case, test_user):
        """
        测试执行成功 - settings 为字典
        Given: settings 为字典
        When: 调用 execute 方法
        Then: settings 被正确序列化为 JSON
        """
        # Arrange
        name = "设置测试社区"
        description = "测试"
        creator_id = test_user.user_id
        settings = {"key1": "value1", "key2": 123}

        # Act
        result = use_case.execute(name, description, creator_id, settings=settings)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 验证社区被保存
        community = use_case.community_repository.find_by_id(result.data['community_id'])
        assert community is not None
        settings_dict = json.loads(community.settings)
        assert settings_dict == settings

    def test_execute_strips_whitespace(self, use_case, test_user):
        """
        测试执行成功 - 自动去除名称前后空格
        Given: 社区名称有前后空格
        When: 调用 execute 方法
        Then: 自动去除前后空格
        """
        # Arrange
        name = "  测试社区  "
        description = "测试"
        creator_id = test_user.user_id

        # Act
        result = use_case.execute(name, description, creator_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['name'] == "测试社区"


class TestDeleteCommunityUseCase:
    """DeleteCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return DeleteCommunityUseCase()

    def test_validate_success(self, use_case, test_community, test_user):
        """
        测试验证成功
        Given: 有效的社区ID和用户ID（创建者）
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        community_id = test_community.community_id
        user_id = test_user.user_id

        # 修改社区的创建者为测试用户
        test_community.creator_id = user_id
        use_case.community_repository.save(test_community)

        # 确保用户不在该社区
        test_user.community_id = None
        use_case.user_repository.save(test_user)

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "社区删除成功" in result.message

    def test_validate_missing_community_id(self, use_case, test_user):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = None
        user_id = test_user.user_id

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_validate_missing_user_id(self, use_case, test_community):
        """
        测试验证失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = test_community.community_id
        user_id = None

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_community_not_found(self, use_case, test_user):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        community_id = 999999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_unauthorized_not_creator(self, use_case, test_community, test_user):
        """
        测试执行失败 - 无权限（不是创建者）
        Given: 用户不是社区创建者
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态
        """
        # Arrange
        community_id = test_community.community_id
        user_id = test_user.user_id

        # 确保用户不是创建者
        test_community.creator_id = 999999
        use_case.community_repository.save(test_community)

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "无权删除此社区" in result.message

    def test_execute_success_as_superuser(self, use_case, test_community, test_superuser):
        """
        测试执行成功 - 超级管理员删除
        Given: 用户是超级管理员
        When: 调用 execute 方法
        Then: 成功删除社区
        """
        # Arrange
        community_id = test_community.community_id
        user_id = test_superuser.user_id

        # 确保创建者不是超级管理员
        test_community.creator_id = 999999
        use_case.community_repository.save(test_community)

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "社区删除成功" in result.message

    def test_execute_community_has_users(self, use_case, test_community, test_user):
        """
        测试执行失败 - 社区中有用户
        Given: 社区中有用户
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        community_id = test_community.community_id
        user_id = test_user.user_id

        # 将用户添加到社区
        test_user.community_id = community_id
        use_case.user_repository.save(test_user)

        # 设置用户为创建者
        test_community.creator_id = user_id
        use_case.community_repository.save(test_community)

        # Act
        result = use_case.execute(community_id, user_id)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "社区中还有用户" in result.message


class TestUpdateCommunityUseCase:
    """UpdateCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UpdateCommunityUseCase()

    def test_validate_success(self, use_case, test_community):
        """
        测试验证成功
        Given: 有效的社区ID和更新参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        community_id = test_community.community_id
        new_name = "更新后的社区名称"

        # Act
        result = use_case.execute(community_id, name=new_name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "社区更新成功" in result.message
        assert result.data['name'] == new_name

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = None

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_execute_community_not_found(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        community_id = 999999

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_update_name(self, use_case, test_community):
        """
        测试执行成功 - 更新社区名称
        Given: 有效的社区ID和新名称
        When: 调用 execute 方法
        Then: 成功更新名称
        """
        # Arrange
        community_id = test_community.community_id
        new_name = "新社区名称"

        # Act
        result = use_case.execute(community_id, name=new_name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['name'] == new_name

    def test_execute_update_description(self, use_case, test_community):
        """
        测试执行成功 - 更新社区描述
        Given: 有效的社区ID和新描述
        When: 调用 execute 方法
        Then: 成功更新描述
        """
        # Arrange
        community_id = test_community.community_id
        new_description = "这是新的社区描述"

        # Act
        result = use_case.execute(community_id, description=new_description)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['description'] == new_description

    def test_execute_update_location(self, use_case, test_community):
        """
        测试执行成功 - 更新位置信息
        Given: 有效的社区ID和新位置
        When: 调用 execute 方法
        Then: 成功更新位置
        """
        # Arrange
        community_id = test_community.community_id
        new_location = "上海市浦东新区"

        # Act
        result = use_case.execute(community_id, location=new_location)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['location'] == new_location

    def test_execute_update_manager(self, use_case, test_community, test_user):
        """
        测试执行成功 - 更新主管
        Given: 有效的社区ID和新主管ID
        When: 调用 execute 方法
        Then: 成功更新主管
        """
        # Arrange
        community_id = test_community.community_id
        manager_id = test_user.user_id

        # Act
        result = use_case.execute(community_id, manager_id=manager_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

    def test_execute_manager_not_found(self, use_case, test_community):
        """
        测试执行失败 - 主管不存在
        Given: 主管ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        community_id = test_community.community_id
        manager_id = 999999

        # Act
        result = use_case.execute(community_id, manager_id=manager_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "主管不存在" in result.message

    def test_execute_update_multiple_fields(self, use_case, test_community, test_user):
        """
        测试执行成功 - 同时更新多个字段
        Given: 有效的社区ID和多个更新字段
        When: 调用 execute 方法
        Then: 成功更新所有字段
        """
        # Arrange
        community_id = test_community.community_id
        new_name = "全面更新的社区"
        new_description = "这是全面更新的描述"
        new_location = "新地址"
        new_manager_id = test_user.user_id

        # Act
        result = use_case.execute(
            community_id,
            name=new_name,
            description=new_description,
            location=new_location,
            manager_id=new_manager_id
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['name'] == new_name
        assert result.data['description'] == new_description
        assert result.data['location'] == new_location


class TestGetCommunityDetailsUseCase:
    """GetCommunityDetailsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityDetailsUseCase()

    def test_validate_success(self, use_case, test_community):
        """
        测试验证成功
        Given: 有效的社区ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和完整社区信息
        """
        # Arrange
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取社区详情成功" in result.message
        assert result.data['community_id'] == community_id
        assert result.data['name'] is not None
        assert result.data['description'] is not None

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = None

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_execute_community_not_found(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        community_id = 999999

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_includes_creator_info(self, use_case, test_community, test_user):
        """
        测试执行成功 - 包含创建者信息
        Given: 社区有创建者
        When: 调用 execute 方法
        Then: 返回包含创建者信息
        """
        # Arrange
        test_community.creator_id = test_user.user_id
        use_case.community_repository.save(test_community)
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['creator'] is not None
        assert result.data['creator']['user_id'] == test_user.user_id
        assert result.data['creator']['nickname'] == test_user.nickname

    def test_execute_includes_manager_info(self, use_case, test_community, test_user):
        """
        测试执行成功 - 包含主管信息
        Given: 社区有主管
        When: 调用 execute 方法
        Then: 返回包含主管信息
        """
        # Arrange
        test_community.manager_id = test_user.user_id
        use_case.community_repository.save(test_community)
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['manager'] is not None
        assert result.data['manager']['user_id'] == test_user.user_id

    def test_execute_includes_user_count(self, use_case, test_community, test_user):
        """
        测试执行成功 - 包含用户数量
        Given: 社区有用户
        When: 调用 execute 方法
        Then: 返回包含用户数量
        """
        # Arrange
        test_user.community_id = test_community.community_id
        use_case.user_repository.save(test_user)
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['user_count'] >= 1

    def test_execute_includes_timestamps(self, use_case, test_community):
        """
        测试执行成功 - 包含时间戳
        Given: 有效的社区
        When: 调用 execute 方法
        Then: 返回包含创建和更新时间
        """
        # Arrange
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['created_at'] is not None
        assert result.data['updated_at'] is not None

    def test_execute_includes_settings(self, use_case, test_community):
        """
        测试执行成功 - 包含设置信息
        Given: 社区有设置
        When: 调用 execute 方法
        Then: 返回包含设置信息
        """
        # Arrange
        test_community.settings = json.dumps({"key": "value"})
        use_case.community_repository.save(test_community)
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['settings'] is not None
        assert result.data['settings']['key'] == "value"


class TestJoinCommunityUseCase:
    """JoinCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return JoinCommunityUseCase()

    def test_validate_success(self, use_case, test_user, test_community):
        """
        测试验证成功
        Given: 有效的用户ID和社区名称
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_name = test_community.name

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "加入社区成功" in result.message
        assert result.data['community_id'] == test_community.community_id

    def test_validate_missing_community_name(self, use_case, test_user):
        """
        测试验证失败 - 社区名称为空
        Given: 社区名称为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_name = ""

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区名称不能为空" in result.message

    def test_validate_whitespace_community_name(self, use_case, test_user):
        """
        测试验证失败 - 社区名称只有空格
        Given: 社区名称只有空格
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_name = "   "

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区名称不能为空" in result.message

    def test_execute_user_not_found(self, use_case, test_community):
        """
        测试执行失败 - 用户不存在
        Given: 用户ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 999999
        community_name = test_community.name

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_community_not_found(self, use_case, test_user):
        """
        测试执行失败 - 社区不存在
        Given: 社区名称不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_name = "不存在的社区"

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_already_in_community(self, use_case, test_user, test_community):
        """
        测试执行失败 - 用户已在社区
        Given: 用户已在社区中
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_user.community_id = test_community.community_id
        use_case.user_repository.save(test_user)

        user_id = test_user.user_id
        community_name = test_community.name

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "用户已在社区" in result.message

    def test_execute_success_updates_user(self, use_case, test_user, test_community):
        """
        测试执行成功 - 更新用户的社区ID
        Given: 有效的用户ID和社区名称
        When: 调用 execute 方法
        Then: 用户的社区ID被更新
        """
        # Arrange
        user_id = test_user.user_id
        community_name = test_community.name
        old_community_id = test_user.community_id

        # Act
        result = use_case.execute(user_id, community_name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        updated_user = use_case.user_repository.find_by_id(user_id)
        assert updated_user.community_id == test_community.community_id
        assert result.data['community_name'] == test_community.name


class TestLeaveCommunityUseCase:
    """LeaveCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return LeaveCommunityUseCase()

    def test_validate_success(self, use_case, test_user, test_community):
        """
        测试验证成功
        Given: 有效的用户ID（用户在社区中）
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        test_user.community_id = test_community.community_id
        use_case.user_repository.save(test_user)

        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "离开社区成功" in result.message
        assert result.data['old_community_id'] == test_community.community_id

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_user_not_found(self, use_case):
        """
        测试执行失败 - 用户不存在
        Given: 用户ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 999999

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_not_in_community(self, use_case, test_user):
        """
        测试执行失败 - 用户不在社区
        Given: 用户不在任何社区
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        test_user.community_id = None
        use_case.user_repository.save(test_user)

        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "用户不在任何社区" in result.message

    def test_execute_success_clears_community_id(self, use_case, test_user, test_community):
        """
        测试执行成功 - 清除用户的社区ID
        Given: 用户在社区中
        When: 调用 execute 方法
        Then: 用户的社区ID被清除
        """
        # Arrange
        test_user.community_id = test_community.community_id
        use_case.user_repository.save(test_user)

        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        updated_user = use_case.user_repository.find_by_id(user_id)
        assert updated_user.community_id is None


class TestSearchCommunityUseCase:
    """SearchCommunityUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return SearchCommunityUseCase()

    @pytest.fixture
    def multiple_communities(self, test_session):
        """创建多个测试社区"""
        communities = []
        for i in range(5):
            community = Community(
                name=f"测试社区{i}",
                description=f"这是测试社区{i}的描述",
                province="北京市",
                city="北京市",
                district="朝阳区",
                status=1
            )
            test_session.add(community)
            communities.append(community)
        test_session.commit()
        return communities

    def test_validate_success(self, use_case, multiple_communities):
        """
        测试验证成功
        Given: 有效的搜索参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和搜索结果
        """
        # Arrange
        keyword = "测试"

        # Act
        result = use_case.execute(keyword=keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索社区成功" in result.message
        assert 'communities' in result.data
        assert result.data['total'] > 0

    def test_validate_invalid_page(self, use_case):
        """
        测试验证失败 - 页码无效
        Given: 页码小于1
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page = 0

        # Act
        result = use_case.execute(keyword=keyword, page=page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_validate_invalid_page_size(self, use_case):
        """
        测试验证失败 - 每页数量无效
        Given: 每页数量超过100
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = "测试"
        page_size = 101

        # Act
        result = use_case.execute(keyword=keyword, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_execute_with_keyword(self, use_case, multiple_communities):
        """
        测试执行成功 - 按关键词搜索
        Given: 有效的搜索关键词
        When: 调用 execute 方法
        Then: 返回匹配的社区
        """
        # Arrange
        keyword = "测试社区"

        # Act
        result = use_case.execute(keyword=keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] > 0

    def test_execute_with_location_filter(self, use_case, multiple_communities):
        """
        测试执行成功 - 按位置筛选
        Given: 有效的位置参数
        When: 调用 execute 方法
        Then: 返回指定位置的社区
        """
        # Arrange
        province = "北京市"
        city = "北京市"

        # Act
        result = use_case.execute(province=province, city=city)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for community in result.data['communities']:
            assert community['province'] == province
            assert community['city'] == city

    def test_execute_with_status_filter(self, use_case, multiple_communities):
        """
        测试执行成功 - 按状态筛选
        Given: 有效的状态参数
        When: 调用 execute 方法
        Then: 返回指定状态的社区
        """
        # Arrange
        status = 1

        # Act
        result = use_case.execute(status=status)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for community in result.data['communities']:
            assert community['status'] == status

    def test_execute_with_pagination(self, use_case, multiple_communities):
        """
        测试执行成功 - 分页搜索
        Given: 有效的分页参数
        When: 调用 execute 方法
        Then: 返回分页结果
        """
        # Arrange
        page = 1
        page_size = 2

        # Act
        result = use_case.execute(page=page, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['communities']) <= page_size
        assert result.data['page'] == page
        assert result.data['page_size'] == page_size

    def test_execute_empty_result(self, use_case):
        """
        测试执行成功 - 搜索结果为空
        Given: 不存在的搜索关键词
        When: 调用 execute 方法
        Then: 返回空结果
        """
        # Arrange
        keyword = "不存在的社区名称"

        # Act
        result = use_case.execute(keyword=keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] == 0
        assert len(result.data['communities']) == 0

    def test_execute_calculates_total_pages(self, use_case, multiple_communities):
        """
        测试执行成功 - 计算总页数
        Given: 有效的搜索结果
        When: 调用 execute 方法
        Then: 正确计算总页数
        """
        # Arrange
        page_size = 2

        # Act
        result = use_case.execute(page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        expected_total_pages = (result.data['total'] + page_size - 1) // page_size
        assert result.data['total_pages'] == expected_total_pages


class TestListCommunityUsersUseCase:
    """ListCommunityUsersUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return ListCommunityUsersUseCase()

    @pytest.fixture
    def multiple_users(self, test_session, test_community):
        """创建多个测试用户"""
        users = []
        for i in range(5):
            user = User(
                wechat_openid=f"test_openid_{i}",
                phone_number=f"1390000{i:04d}",
                phone_hash=f"test_hash_{i}",
                nickname=f"测试用户{i}",
                name=f"用户{i}",
                role=1 if i < 3 else 2,
                community_id=test_community.community_id,
                status=1
            )
            test_session.add(user)
            users.append(user)
        test_session.commit()
        return users

    def test_validate_success(self, use_case, test_community, multiple_users):
        """
        测试验证成功
        Given: 有效的社区ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和用户列表
        """
        # Arrange
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "列出社区用户成功" in result.message
        assert 'users' in result.data
        assert result.data['total'] > 0

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = None

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_validate_invalid_page(self, use_case, test_community):
        """
        测试验证失败 - 页码无效
        Given: 页码小于1
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = test_community.community_id
        page = 0

        # Act
        result = use_case.execute(community_id, page=page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_validate_invalid_page_size(self, use_case, test_community):
        """
        测试验证失败 - 每页数量无效
        Given: 每页数量超过100
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        community_id = test_community.community_id
        page_size = 101

        # Act
        result = use_case.execute(community_id, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_execute_community_not_found(self, use_case):
        """
        测试执行失败 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        community_id = 999999

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_execute_with_role_filter(self, use_case, test_community, multiple_users):
        """
        测试执行成功 - 按角色筛选
        Given: 有效的角色参数
        When: 调用 execute 方法
        Then: 返回指定角色的用户
        """
        # Arrange
        community_id = test_community.community_id
        role = 1

        # Act
        result = use_case.execute(community_id, role=role)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for user in result.data['users']:
            assert user['role'] == role

    def test_execute_with_keyword_filter(self, use_case, test_community, multiple_users):
        """
        测试执行成功 - 按关键词筛选
        Given: 有效的搜索关键词
        When: 调用 execute 方法
        Then: 返回匹配的用户
        """
        # Arrange
        community_id = test_community.community_id
        keyword = "测试用户"

        # Act
        result = use_case.execute(community_id, keyword=keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] > 0

    def test_execute_with_pagination(self, use_case, test_community, multiple_users):
        """
        测试执行成功 - 分页查询
        Given: 有效的分页参数
        When: 调用 execute 方法
        Then: 返回分页结果
        """
        # Arrange
        community_id = test_community.community_id
        page = 1
        page_size = 2

        # Act
        result = use_case.execute(community_id, page=page, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['users']) <= page_size
        assert result.data['page'] == page
        assert result.data['page_size'] == page_size

    def test_execute_empty_result(self, use_case, test_community):
        """
        测试执行成功 - 社区没有用户
        Given: 社区没有用户
        When: 调用 execute 方法
        Then: 返回空结果
        """
        # Arrange
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] == 0
        assert len(result.data['users']) == 0

    def test_execute_includes_user_details(self, use_case, test_community, multiple_users):
        """
        测试执行成功 - 包含用户详细信息
        Given: 社区有用户
        When: 调用 execute 方法
        Then: 返回包含用户详细信息
        """
        # Arrange
        community_id = test_community.community_id

        # Act
        result = use_case.execute(community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for user in result.data['users']:
            assert 'user_id' in user
            assert 'nickname' in user
            assert 'name' in user
            assert 'phone_number' in user
            assert 'role' in user
            assert 'role_name' in user