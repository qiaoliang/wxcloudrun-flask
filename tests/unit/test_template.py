"""
UseCase单元测试模板

使用说明:
1. 复制此文件并重命名为 test_<module>_use_cases.py
2. 替换所有 <UseCaseName> 为实际的UseCase名称
3. 根据实际UseCase的接口调整测试用例
4. 遵循AAA模式（Arrange-Act-Assert）
5. 测试命名使用 "test_should_<expected_behavior>_<scenario>" 格式
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.application.use_cases.base import UseCaseStatus, UseCaseResult
# 导入需要测试的UseCase
# from app.application.use_cases.<module>.<usecase_file> import <UseCaseName>


class Test<UseCaseName>:
    """<UseCaseName> 测试类"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return <UseCaseName>()

    @pytest.fixture
    def test_user(self, test_session):
        """创建测试用户"""
        from database.flask_models import User
        from tests.test_data_generator import generate_unique_phone_number, generate_unique_nickname

        user = User(
            phone_number=generate_unique_phone_number("test_user"),
            nickname=generate_unique_nickname("test_user"),
            wechat_openid="openid_test",
            role=1  # 根据需要调整
        )
        test_session.add(user)
        test_session.flush()
        return user

    def test_should_successfully_execute_with_valid_parameters(self, use_case, test_user):
        """
        测试成功执行 - 参数有效
        Given: 有效的输入参数
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态和正确数据
        """
        # Arrange - 准备测试数据
        param1 = "valid_value"
        param2 = test_user.user_id

        # Act - 执行被测试的方法
        result = use_case.execute(param1, param2)

        # Assert - 验证结果
        assert result.status == UseCaseStatus.SUCCESS
        assert "成功" in result.message
        assert result.data is not None

    def test_should_return_validation_error_when_parameter_is_missing(self, use_case):
        """
        测试验证失败 - 缺少必需参数
        Given: 缺少必需参数
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        param1 = None  # 必需参数为空

        # Act
        result = use_case.execute(param1)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "不能为空" in result.message or "缺少" in result.message

    def test_should_return_not_found_when_resource_does_not_exist(self, use_case):
        """
        测试业务错误 - 资源不存在
        Given: 资源ID不存在
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        non_existent_id = 99999

        # Act
        result = use_case.execute(non_existent_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "不存在" in result.message

    def test_should_return_forbidden_when_user_lacks_permission(self, use_case, test_user):
        """
        测试权限不足 - 用户无权限
        Given: 用户没有执行操作的权限
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        # 设置用户为无权限角色
        test_user.role = 1  # 普通用户

        # Act
        result = use_case.execute(test_user.user_id, resource_id=1)

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "权限" in result.message

    def test_should_return_business_error_when_business_rule_violated(self, use_case, test_user):
        """
        测试业务错误 - 违反业务规则
        Given: 操作违反业务规则
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        # 设置违反业务规则的条件
        invalid_param = "invalid_value"

        # Act
        result = use_case.execute(test_user.user_id, invalid_param)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert result.message is not None and len(result.message) > 0

    def test_should_handle_edge_case_with_boundary_value(self, use_case):
        """
        测试边界条件 - 边界值
        Given: 参数为边界值
        When: 调用 execute 方法
        Then: 正确处理边界条件
        """
        # Arrange
        boundary_value = 100  # 最大值或最小值

        # Act
        result = use_case.execute(boundary_value)

        # Assert
        # 根据业务规则验证结果
        assert result.status in [UseCaseStatus.SUCCESS, UseCaseStatus.VALIDATION_ERROR]

    def test_should_return_error_on_repository_exception(self, use_case):
        """
        测试异常处理 - Repository抛出异常
        Given: Repository抛出异常
        When: 调用 execute 方法
        Then: 返回 FAILURE 状态并记录错误
        """
        # Arrange
        # Mock Repository抛出异常
        with patch.object(use_case, 'repository') as mock_repo:
            mock_repo.find_by_id.side_effect = Exception("Database error")

            # Act
            result = use_case.execute(1)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert "系统错误" in result.message or "失败" in result.message


# 集成测试示例（如果有需要）
class Test<UseCaseName>Integration:
    """<UseCaseName> 集成测试类"""

    def test_should_work_with_database(self, use_case, test_session):
        """
        测试与数据库的集成
        Given: 使用真实数据库会话
        When: 执行UseCase
        Then: 数据正确持久化到数据库
        """
        # Arrange
        # 创建必要的测试数据
        test_data = create_test_data(test_session)

        # Act
        result = use_case.execute(test_data.id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 验证数据库中的数据
        db_data = test_session.get(Model, result.data['id'])
        assert db_data is not None


# 测试辅助函数
def create_test_data(session):
    """创建测试数据的辅助函数"""
    from database.flask_models import Model
    from tests.test_data_generator import generate_unique_phone_number

    data = Model(
        field1=generate_unique_phone_number("test"),
        field2="test_value"
    )
    session.add(data)
    session.flush()
    return data


# 测试配置
# pytest.ini 配置示例:
# [pytest]
# testpaths = tests
# python_files = test_*.py
# python_classes = Test*
# python_functions = test_*
# addopts = -v --tb=short --strict-markers
# markers =
#     slow: marks tests as slow (deselect with '-m "not slow"')
#     integration: marks tests as integration tests