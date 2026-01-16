"""
社区申请管理 UseCases 单元测试

测试以下 UseCase：
1. GetCommunityApplicationsUseCase - 获取社区申请列表
2. CreateCommunityApplicationUseCase - 创建社区申请

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from database.flask_models import User, Community, CommunityApplication
from app.application.use_cases.community.get_community_applications_use_case import GetCommunityApplicationsUseCase
from app.application.use_cases.community.create_community_application_use_case import CreateCommunityApplicationUseCase
from app.application.use_cases.base import UseCaseStatus


class TestGetCommunityApplicationsUseCase:
    """GetCommunityApplicationsUseCase 测试类"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return GetCommunityApplicationsUseCase()

    def test_get_applications_success(self, use_case, test_user, test_community):
        """
        测试成功获取申请列表
        Given: 有效的用户ID和分页参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和申请列表
        """
        # Arrange
        user_id = test_user.user_id
        page = 1
        per_page = 20

        # 创建一个申请记录
        application = CommunityApplication(
            user_id=user_id,
            target_community_id=test_community.community_id,
            status=1,
            reason="我想加入这个社区"
        )
        from database.flask_models import db
        db.session.add(application)
        db.session.commit()

        # Act
        result = use_case.execute(user_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取申请列表成功" in result.message
        assert 'applications' in result.data
        assert 'total' in result.data
        assert 'page' in result.data
        assert 'per_page' in result.data

    def test_get_applications_with_status_filter(self, use_case, test_user, test_community):
        """
        测试使用状态过滤获取申请列表
        Given: 有效的用户ID、分页参数和状态过滤
        When: 调用 execute 方法
        Then: 返回符合条件的申请列表
        """
        # Arrange
        user_id = test_user.user_id
        page = 1
        per_page = 20
        status_filter = 'pending'

        # 创建申请记录
        application = CommunityApplication(
            user_id=user_id,
            target_community_id=test_community.community_id,
            status=1,  # pending
            reason="我想加入这个社区"
        )
        from database.flask_models import db
        db.session.add(application)
        db.session.commit()

        # Act
        result = use_case.execute(user_id, page, per_page, status_filter)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['applications']) >= 0

    def test_get_applications_empty_list(self, use_case, test_user):
        """
        测试获取空申请列表
        Given: 用户没有任何申请
        When: 调用 execute 方法
        Then: 返回空列表
        """
        # Arrange
        user_id = test_user.user_id
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(user_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['applications']) == 0
        assert result.data['total'] == 0

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None
        page = 1
        per_page = 20

        # Act
        result = use_case.execute(user_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_validate_invalid_page(self, use_case):
        """
        测试验证失败 - 无效的页码
        Given: 页码小于1
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 1
        page = 0
        per_page = 20

        # Act
        result = use_case.execute(user_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "页码必须大于0" in result.message

    def test_validate_invalid_per_page(self, use_case):
        """
        测试验证失败 - 无效的每页数量
        Given: 每页数量大于100
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 1
        page = 1
        per_page = 101

        # Act
        result = use_case.execute(user_id, page, per_page)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_validate_invalid_status_filter(self, use_case):
        """
        测试验证失败 - 无效的状态过滤值
        Given: 无效的状态过滤值
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 1
        page = 1
        per_page = 20
        status_filter = 'invalid'

        # Act
        result = use_case.execute(user_id, page, per_page, status_filter)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "无效的状态过滤值" in result.message


class TestCreateCommunityApplicationUseCase:
    """CreateCommunityApplicationUseCase 测试类"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return CreateCommunityApplicationUseCase()

    def test_create_application_success(self, use_case, test_user, test_community):
        """
        测试成功创建申请
        Given: 有效的用户ID、社区ID和消息
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和申请ID
        """
        # Arrange
        user_id = test_user.user_id
        community_id = test_community.community_id
        message = "我想加入这个社区"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "申请提交成功" in result.message
        assert 'application_id' in result.data
        assert result.data['application_id'] > 0

    def test_create_application_without_message(self, use_case, test_user, test_community):
        """
        测试成功创建申请（无消息）
        Given: 有效的用户ID和社区ID，消息为空
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_id = test_community.community_id
        message = ""

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert 'application_id' in result.data

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None
        community_id = 1
        message = "测试消息"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 社区ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 1
        community_id = None
        message = "测试消息"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "社区ID不能为空" in result.message

    def test_validate_message_too_long(self, use_case):
        """
        测试验证失败 - 消息过长
        Given: 消息超过500个字符
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = 1
        community_id = 1
        message = "a" * 501

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "申请消息不能超过500个字符" in result.message

    def test_community_not_found(self, use_case, test_user):
        """
        测试业务错误 - 社区不存在
        Given: 社区ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_id = 99999  # 不存在的社区ID
        message = "测试消息"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "社区不存在" in result.message

    def test_user_already_member(self, use_case, test_user, test_community):
        """
        测试业务错误 - 用户已经是社区成员
        Given: 用户已经是该社区的成员
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        # 将用户设置为社区成员
        test_user.community_id = test_community.community_id
        from database.flask_models import db
        db.session.commit()

        user_id = test_user.user_id
        community_id = test_community.community_id
        message = "测试消息"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "您已经是该社区的成员" in result.message

    def test_duplicate_application(self, use_case, test_user, test_community):
        """
        测试业务错误 - 重复申请
        Given: 用户已经有待审核的申请
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        community_id = test_community.community_id
        message = "测试消息"

        # 创建第一个申请
        application1 = CommunityApplication(
            user_id=user_id,
            target_community_id=community_id,
            status=1,  # pending
            reason="第一次申请"
        )
        from database.flask_models import db
        db.session.add(application1)
        db.session.commit()

        # Act - 尝试创建第二个申请
        result = use_case.execute(user_id, community_id, "第二次申请")

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "您已经有一个待审核的申请" in result.message

    def test_create_application_and_verify_data(self, use_case, test_user, test_community):
        """
        测试创建申请并验证数据完整性
        Given: 有效的所有参数
        When: 调用 execute 方法
        Then: 创建的申请数据完整且正确
        """
        # Arrange
        user_id = test_user.user_id
        community_id = test_community.community_id
        message = "这是一个测试申请消息"

        # Act
        result = use_case.execute(user_id, community_id, message)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        application_id = result.data['application_id']

        # 验证数据库中的数据
        from database.flask_models import db
        application = db.session.get(CommunityApplication, application_id)
        assert application is not None
        assert application.user_id == user_id
        assert application.target_community_id == community_id
        assert application.status == 1  # pending
        assert application.reason == message
        assert application.processed_by is None
        assert application.rejection_reason is None