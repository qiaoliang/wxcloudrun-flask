"""
用户管理模块 UseCases 单元测试

测试以下 UseCase：
1. UpdateProfileUseCase - 更新用户资料
2. ChangePasswordUseCase - 修改密码
3. UploadAvatarUseCase - 上传头像
4. SearchUsersUseCase - 搜索用户
5. GetUserDetailsUseCase - 获取用户详情

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from database.flask_models import User, Community
from app.application.use_cases.user.update_profile_use_case import UpdateProfileUseCase
from app.application.use_cases.user.change_password_use_case import ChangePasswordUseCase
from app.application.use_cases.user.upload_avatar_use_case import UploadAvatarUseCase
from app.application.use_cases.user.search_users_use_case import SearchUsersUseCase
from app.application.use_cases.user.get_user_details_use_case import GetUserDetailsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestUpdateProfileUseCase:
    """UpdateProfileUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UpdateProfileUseCase()

    def test_validate_success(self, use_case, test_user):
        """
        测试验证成功
        Given: 有效的用户ID和更新参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态
        """
        # Arrange
        user_id = test_user.user_id
        nickname = "新昵称"

        # Act
        result = use_case.execute(user_id, nickname=nickname)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "用户资料更新成功" in result.message

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 缺少用户ID
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

    def test_validate_empty_nickname(self, use_case, test_user):
        """
        测试验证失败 - 昵称为空字符串
        Given: 昵称为空字符串
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        nickname = ""

        # Act
        result = use_case.execute(user_id, nickname=nickname)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "昵称不能为空" in result.message

    def test_execute_update_nickname(self, use_case, test_user):
        """
        测试执行成功 - 更新昵称
        Given: 有效的用户ID和新昵称
        When: 调用 execute 方法
        Then: 成功更新昵称
        """
        # Arrange
        user_id = test_user.user_id
        new_nickname = "更新后的昵称"

        # Act
        result = use_case.execute(user_id, nickname=new_nickname)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['nickname'] == new_nickname

    def test_execute_update_name(self, use_case, test_user):
        """
        测试执行成功 - 更新姓名
        Given: 有效的用户ID和新姓名
        When: 调用 execute 方法
        Then: 成功更新姓名
        """
        # Arrange
        user_id = test_user.user_id
        new_name = "张三"

        # Act
        result = use_case.execute(user_id, name=new_name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['name'] == new_name

    def test_execute_update_avatar_url(self, use_case, test_user):
        """
        测试执行成功 - 更新头像URL
        Given: 有效的用户ID和新头像URL
        When: 调用 execute 方法
        Then: 成功更新头像URL
        """
        # Arrange
        user_id = test_user.user_id
        new_avatar = "https://example.com/new-avatar.jpg"

        # Act
        result = use_case.execute(user_id, avatar_url=new_avatar)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['avatar_url'] == new_avatar

    def test_execute_update_multiple_fields(self, use_case, test_user):
        """
        测试执行成功 - 同时更新多个字段
        Given: 有效的用户ID和多个更新字段
        When: 调用 execute 方法
        Then: 成功更新所有字段
        """
        # Arrange
        user_id = test_user.user_id
        new_nickname = "新昵称"
        new_name = "李四"
        new_avatar = "https://example.com/new-avatar.jpg"

        # Act
        result = use_case.execute(
            user_id,
            nickname=new_nickname,
            name=new_name,
            avatar_url=new_avatar
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['nickname'] == new_nickname
        assert result.data['name'] == new_name
        assert result.data['avatar_url'] == new_avatar

    def test_execute_user_not_found(self, use_case):
        """
        测试执行失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 999999

        # Act
        result = use_case.execute(user_id, nickname="测试")

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_strip_whitespace(self, use_case, test_user):
        """
        测试执行成功 - 自动去除前后空格
        Given: 带有前后空格的昵称和姓名
        When: 调用 execute 方法
        Then: 自动去除前后空格
        """
        # Arrange
        user_id = test_user.user_id
        nickname = "  新昵称  "
        name = "  张三  "

        # Act
        result = use_case.execute(user_id, nickname=nickname, name=name)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['nickname'] == "新昵称"
        assert result.data['name'] == "张三"


class TestChangePasswordUseCase:
    """ChangePasswordUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return ChangePasswordUseCase()

    @pytest.fixture
    def test_user_with_password(self, test_session):
        """创建带有密码的测试用户"""
        from app.domain.entities.user_entity import UserEntity

        phone_number = "13900001111"
        user = User(
            wechat_openid="test_openid_1111",
            phone_number=phone_number,
            phone_hash="test_hash_1111",
            nickname="测试用户",
            name="测试",
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.flush()

        # 设置初始密码
        user_entity = UserEntity(user)
        user_entity.set_password("old_password123")

        test_session.commit()
        return user

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 缺少用户ID
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None
        old_password = "old_password"
        new_password = "new_password123"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_validate_missing_old_password(self, use_case, test_user):
        """
        测试验证失败 - 缺少旧密码
        Given: 缺少旧密码
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        old_password = None
        new_password = "new_password123"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "旧密码不能为空" in result.message

    def test_validate_missing_new_password(self, use_case, test_user):
        """
        测试验证失败 - 缺少新密码
        Given: 缺少新密码
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        old_password = "old_password"
        new_password = None

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "新密码不能为空" in result.message

    def test_validate_new_password_too_short(self, use_case, test_user):
        """
        测试验证失败 - 新密码太短
        Given: 新密码少于8位
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        old_password = "old_password"
        new_password = "short"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "新密码长度不能少于8位" in result.message

    def test_validate_new_password_no_letters(self, use_case, test_user):
        """
        测试验证失败 - 新密码不包含字母
        Given: 新密码只包含数字
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        old_password = "old_password"
        new_password = "12345678"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "新密码必须包含字母和数字" in result.message

    def test_validate_new_password_no_digits(self, use_case, test_user):
        """
        测试验证失败 - 新密码不包含数字
        Given: 新密码只包含字母
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        old_password = "old_password"
        new_password = "abcdefgh"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "新密码必须包含字母和数字" in result.message

    def test_execute_success(self, use_case, test_user_with_password):
        """
        测试执行成功 - 修改密码
        Given: 有效的用户ID、旧密码和新密码
        When: 调用 execute 方法
        Then: 成功修改密码
        """
        # Arrange
        user_id = test_user_with_password.user_id
        old_password = "old_password123"
        new_password = "new_password456"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "密码修改成功" in result.message

    def test_execute_wrong_old_password(self, use_case, test_user_with_password):
        """
        测试执行失败 - 旧密码错误
        Given: 旧密码不正确
        When: 调用 execute 方法
        Then: 返回 UNAUTHORIZED 状态
        """
        # Arrange
        user_id = test_user_with_password.user_id
        old_password = "wrong_password"
        new_password = "new_password456"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.UNAUTHORIZED
        assert "旧密码" in result.message and "不正确" in result.message

    def test_execute_user_not_found(self, use_case):
        """
        测试执行失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 999999
        old_password = "old_password"
        new_password = "new_password123"

        # Act
        result = use_case.execute(user_id, old_password, new_password)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message


class TestUploadAvatarUseCase:
    """UploadAvatarUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UploadAvatarUseCase()

    @pytest.fixture
    def mock_file_data(self):
        """模拟文件数据"""
        return b"fake_image_data"

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 缺少用户ID
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None
        file_data = b"test_data"
        file_name = "test.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_validate_missing_file_data(self, use_case, test_user):
        """
        测试验证失败 - 缺少文件数据
        Given: 文件数据为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        file_data = None
        file_name = "test.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "文件数据不能为空" in result.message

    def test_validate_missing_file_name(self, use_case, test_user, mock_file_data):
        """
        测试验证失败 - 缺少文件名
        Given: 文件名为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        file_data = mock_file_data
        file_name = None
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "文件名不能为空" in result.message

    def test_validate_invalid_file_type(self, use_case, test_user, mock_file_data):
        """
        测试验证失败 - 不支持的文件类型
        Given: 不支持的文件类型
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        file_data = mock_file_data
        file_name = "test.pdf"
        content_type = "application/pdf"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "不支持的文件类型" in result.message

    def test_validate_file_too_large(self, use_case, test_user):
        """
        测试验证失败 - 文件太大
        Given: 文件大小超过5MB
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        file_data = b"x" * (5 * 1024 * 1024 + 1)  # 5MB + 1 byte
        file_name = "test.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "文件大小不能超过 5MB" in result.message

    def test_execute_success_jpeg(self, use_case, test_user, mock_file_data):
        """
        测试执行成功 - 上传JPEG图片
        Given: 有效的JPEG图片数据
        When: 调用 execute 方法
        Then: 成功上传头像
        """
        # Arrange
        user_id = test_user.user_id
        file_data = mock_file_data
        file_name = "avatar.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "头像上传成功" in result.message
        assert result.data['user_id'] == user_id
        assert 'avatar_url' in result.data

    def test_execute_success_png(self, use_case, test_user, mock_file_data):
        """
        测试执行成功 - 上传PNG图片
        Given: 有效的PNG图片数据
        When: 调用 execute 方法
        Then: 成功上传头像
        """
        # Arrange
        user_id = test_user.user_id
        file_data = mock_file_data
        file_name = "avatar.png"
        content_type = "image/png"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "头像上传成功" in result.message

    def test_execute_user_not_found(self, use_case, mock_file_data):
        """
        测试执行失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 999999
        file_data = mock_file_data
        file_name = "test.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_generates_unique_filename(self, use_case, test_user, mock_file_data):
        """
        测试执行成功 - 生成唯一文件名
        Given: 有效的用户ID和文件数据
        When: 调用 execute 方法
        Then: 生成包含用户ID和时间戳的唯一文件名
        """
        # Arrange
        user_id = test_user.user_id
        file_data = mock_file_data
        file_name = "avatar.jpg"
        content_type = "image/jpeg"

        # Act
        result = use_case.execute(user_id, file_data, file_name, content_type)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert f"avatar_{user_id}_" in result.data['file_name']
        assert result.data['file_name'].endswith('.jpg')


class TestSearchUsersUseCase:
    """SearchUsersUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return SearchUsersUseCase()

    @pytest.fixture
    def multiple_test_users(self, test_session, test_community):
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
                community_id=test_community.community_id if i < 3 else None,
                status=1
            )
            test_session.add(user)
            users.append(user)
        test_session.commit()
        return users

    def test_validate_missing_keyword(self, use_case):
        """
        测试验证失败 - 缺少搜索关键词
        Given: 搜索关键词为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        keyword = ""

        # Act
        result = use_case.execute(keyword)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "搜索关键词不能为空" in result.message

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
        result = use_case.execute(keyword, page=page)

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
        result = use_case.execute(keyword, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "每页数量必须在1-100之间" in result.message

    def test_execute_success(self, use_case, multiple_test_users):
        """
        测试执行成功 - 搜索用户
        Given: 有效的搜索关键词
        When: 调用 execute 方法
        Then: 返回搜索结果
        """
        # Arrange
        keyword = "测试"

        # Act
        result = use_case.execute(keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "搜索用户成功" in result.message
        assert 'users' in result.data
        assert 'total' in result.data
        assert result.data['total'] > 0

    def test_execute_with_pagination(self, use_case, multiple_test_users):
        """
        测试执行成功 - 分页搜索
        Given: 有效的搜索关键词和分页参数
        When: 调用 execute 方法
        Then: 返回分页结果
        """
        # Arrange
        keyword = "测试"
        page = 1
        page_size = 2

        # Act
        result = use_case.execute(keyword, page=page, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['users']) <= page_size
        assert result.data['page'] == page
        assert result.data['page_size'] == page_size

    def test_execute_with_community_filter(self, use_case, multiple_test_users, test_community):
        """
        测试执行成功 - 按社区筛选
        Given: 有效的搜索关键词和社区ID
        When: 调用 execute 方法
        Then: 返回指定社区的用户
        """
        # Arrange
        keyword = "测试"
        community_id = test_community.community_id

        # Act
        result = use_case.execute(keyword, community_id=community_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for user in result.data['users']:
            assert user['community_id'] == community_id

    def test_execute_with_role_filter(self, use_case, multiple_test_users):
        """
        测试执行成功 - 按角色筛选
        Given: 有效的搜索关键词和角色
        When: 调用 execute 方法
        Then: 返回指定角色的用户
        """
        # Arrange
        keyword = "测试"
        role = 1

        # Act
        result = use_case.execute(keyword, role=role)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        for user in result.data['users']:
            assert user['role'] == role

    def test_execute_empty_result(self, use_case):
        """
        测试执行成功 - 搜索结果为空
        Given: 不存在的搜索关键词
        When: 调用 execute 方法
        Then: 返回空结果
        """
        # Arrange
        keyword = "不存在的用户名"

        # Act
        result = use_case.execute(keyword)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] == 0
        assert len(result.data['users']) == 0

    def test_execute_calculates_total_pages(self, use_case, multiple_test_users):
        """
        测试执行成功 - 计算总页数
        Given: 有效的搜索结果
        When: 调用 execute 方法
        Then: 正确计算总页数
        """
        # Arrange
        keyword = "测试"
        page_size = 2

        # Act
        result = use_case.execute(keyword, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        expected_total_pages = (result.data['total'] + page_size - 1) // page_size
        assert result.data['total_pages'] == expected_total_pages


class TestGetUserDetailsUseCase:
    """GetUserDetailsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetUserDetailsUseCase()

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 缺少用户ID
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

    def test_execute_success(self, use_case, test_user):
        """
        测试执行成功 - 获取用户详情
        Given: 有效的用户ID
        When: 调用 execute 方法
        Then: 返回完整的用户详情
        """
        # Arrange
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取用户详情成功" in result.message
        assert result.data['user_id'] == user_id
        assert 'nickname' in result.data
        assert 'name' in result.data
        assert 'phone_number' in result.data
        assert 'role' in result.data
        assert 'role_name' in result.data

    def test_execute_user_not_found(self, use_case):
        """
        测试执行失败 - 用户不存在
        Given: 不存在的用户ID
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

    def test_execute_with_community(self, use_case, test_user, test_community):
        """
        测试执行成功 - 获取有社区的用户详情
        Given: 属于社区的用户
        When: 调用 execute 方法
        Then: 返回包含社区信息的用户详情
        """
        # Arrange
        test_user.community_id = test_community.community_id
        use_case.user_repository.save(test_user)
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['community_id'] == test_community.community_id
        assert result.data['community_name'] == test_community.name

    def test_execute_without_community(self, use_case, test_user):
        """
        测试执行成功 - 获取无社区的用户详情
        Given: 不属于社区的用户
        When: 调用 execute 方法
        Then: 返回社区信息为空的用户详情
        """
        # Arrange
        test_user.community_id = None
        use_case.user_repository.save(test_user)
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['community_id'] is None
        assert result.data['community_name'] is None

    def test_execute_includes_timestamps(self, use_case, test_user):
        """
        测试执行成功 - 包含时间戳信息
        Given: 有效的用户
        When: 调用 execute 方法
        Then: 返回包含创建和更新时间的信息
        """
        # Arrange
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert 'created_at' in result.data
        assert 'updated_at' in result.data
        assert result.data['created_at'] is not None

    def test_execute_includes_emergency_contact(self, use_case, test_user):
        """
        测试执行成功 - 包含紧急联系人信息
        Given: 有紧急联系人的用户
        When: 调用 execute 方法
        Then: 返回包含紧急联系人信息
        """
        # Arrange
        test_user.emergency_contact_name = "紧急联系人"
        test_user.emergency_contact_phone = "13900009999"
        test_user.emergency_contact_address = "紧急地址"
        use_case.user_repository.save(test_user)
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['emergency_contact_name'] == "紧急联系人"
        assert result.data['emergency_contact_phone'] == "13900009999"
        assert result.data['emergency_contact_address'] == "紧急地址"