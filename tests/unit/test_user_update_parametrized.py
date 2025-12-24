"""
用户更新的参数化测试
遵循KISS和DRY原则，减少重复代码
"""

import pytest
from database.flask_models import User
from wxcloudrun.user_service import UserService
from test_utils import TestUserFactory
from test_constants import TEST_CONSTANTS


class TestUserUpdateParametrized:
    """用户更新的参数化测试类"""

    @pytest.mark.parametrize("update_data,expected_behavior,description", [
        # 成功更新
        (
            {"nickname": "新昵称", "name": "新姓名"},
            "success",
            "成功更新昵称和姓名"
        ),
        (
            {"nickname": "部分更新"},
            "success", 
            "部分更新用户信息"
        ),
        # 字符串角色（应该被忽略）
        (
            {"role": "community_worker"},
            "role_unchanged",
            "字符串角色应被忽略"
        ),
        # 字符串状态（应该被忽略）
        (
            {"status": "inactive"},
            "status_unchanged", 
            "字符串状态应被忽略"
        ),
        # None值（应该被忽略）
        (
            {"nickname": None, "avatar_url": None},
            "none_ignored",
            "None值应被忽略"
        ),
    ])
    def test_update_user_by_id_parametrized(self, test_session, update_data, expected_behavior, description):
        """
        参数化测试：用户更新各种场景
        """
        # Arrange - 创建测试用户
        original_user = TestUserFactory.create_user(
            session=test_session,
            test_context="update_param_test"
        )
        
        # 记录原始值用于验证
        original_role = original_user.role
        original_status = original_user.status
        
        # 创建更新用户对象
        update_user = User()
        update_user.user_id = original_user.user_id
        
        # 设置更新数据
        for key, value in update_data.items():
            setattr(update_user, key, value)
        
        # Act - 执行更新
        UserService.update_user_by_id(update_user)
        
        # Assert - 验证结果
        test_session.expire_all()  # 刷新会话
        updated_user = test_session.query(User).filter_by(
            user_id=original_user.user_id).first()
        
        assert updated_user is not None, f"用户应该存在: {description}"
        
        if expected_behavior == "success":
            # 验证更新的字段
            for key, expected_value in update_data.items():
                if expected_value is not None:
                    actual_value = getattr(updated_user, key)
                    assert actual_value == expected_value, f"{key}应该被更新: {description}"
        
        elif expected_behavior == "role_unchanged":
            # 角色应该保持不变
            assert updated_user.role == original_role, f"角色应该保持不变: {description}"
        
        elif expected_behavior == "status_unchanged":
            # 状态应该保持不变
            assert updated_user.status == original_status, f"状态应该保持不变: {description}"
        
        elif expected_behavior == "none_ignored":
            # None值应该被忽略，保持原值
            for key, expected_value in update_data.items():
                if expected_value is None:
                    original_value = getattr(original_user, key)
                    actual_value = getattr(updated_user, key)
                    assert actual_value == original_value, f"None值的{key}应该被忽略: {description}"

    def test_update_user_by_id_nonexistent(self, test_session):
        """
        测试更新不存在的用户
        """
        # Arrange - 创建更新用户对象，使用不存在的ID
        update_user = User()
        update_user.user_id = 999999  # 不存在的用户ID
        update_user.nickname = "不存在的用户"

        # Act - 更新用户
        UserService.update_user_by_id(update_user)

        # Assert - 方法应该静默处理，不抛出异常
        test_session.expire_all()
        nonexistent_user = test_session.query(User).filter_by(user_id=999999).first()
        assert nonexistent_user is None, "不存在的用户不应该被创建"

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("user_id", None),
        ("user_id", -1),
        ("user_id", 0),
    ])
    def test_update_user_invalid_id(self, test_session, field_name, invalid_value):
        """
        测试无效用户ID的处理
        """
        # Arrange - 创建更新用户对象
        update_user = User()
        setattr(update_user, field_name, invalid_value)
        update_user.nickname = "测试更新"

        # Act & Assert - 应该静默处理，不抛出异常
        UserService.update_user_by_id(update_user)  # 不应该抛出异常

    def test_update_user_multiple_fields(self, test_session):
        """
        测试同时更新多个字段
        """
        # Arrange - 创建测试用户
        original_user = TestUserFactory.create_user(
            session=test_session,
            test_context="multi_field_test"
        )
        
        # Act - 同时更新多个字段
        update_user = User()
        update_user.user_id = original_user.user_id
        update_user.nickname = "新昵称"
        update_user.name = "新姓名"
        update_user.avatar_url = TEST_CONSTANTS.generate_avatar_url("updated")
        
        UserService.update_user_by_id(update_user)
        
        # Assert - 验证所有字段都被正确更新
        test_session.expire_all()
        updated_user = test_session.query(User).filter_by(
            user_id=original_user.user_id).first()
        
        assert updated_user.nickname == "新昵称"
        assert updated_user.name == "新姓名"
        assert updated_user.avatar_url == TEST_CONSTANTS.generate_avatar_url("updated")
        # 验证 updated_at 被更新
        assert updated_user.updated_at is not None