"""
UserService.create_user 方法的单元测试
遵循测试最佳实践，避免测试反模式
"""
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy.exc import OperationalError
from database.models import User, UserAuditLog
from wxcloudrun.user_service import UserService
from wxcloudrun.dao import get_db  # 使用与 UserService 相同的数据库获取方式
from hashutil import phone_hash, pwd_hash


class TestUserService:
    """测试 UserService.create_user 方法"""

    def test_create_user_success_with_openid_and_nickname(self, test_db, test_session):
        """
        测试成功创建用户的情况
        验证真实行为而非 mock 行为
        """
        # Arrange - 只有openid 和 nickname, avatar_url
        new_user = User(
            wechat_openid="test_openid_new",
            nickname="微信新用户",
            avatar_url="https://example.com/1.jpg"
        )

        # Act - 执行被测试的方法
        result = UserService.create_user(new_user)

        # Assert - 验证结果
        assert result is not None
        assert result['wechat_openid'] == "test_openid_new"
        assert result['nickname'] == "微信新用户"
        assert result['name'] == "微信新用户"  # name 设置为 nickname
        assert result['role'] == 1  # 默认角色
        assert result['status'] == 1  # 默认状态
        assert result['verification_status'] == 2  # 默认验证状态
        assert result['_is_community_worker'] is False

        # 验证新微信用户创建时，密码和手机号都是没有值的
        assert result['phone_number'] == ""
        assert result['phone_hash'] == ""
        assert result['password_hash'] ==""

        # 验证用户确实被保存到数据库 - 使用相同的数据库获取方式
        with get_db().get_session() as verify_session:
            saved_user = verify_session.query(User).filter_by(wechat_openid="test_openid_new").first()
            assert saved_user is not None
            assert saved_user.nickname == "微信新用户"

            # 验证审计日志被创建
            audit_log = verify_session.query(UserAuditLog).filter_by(user_id=saved_user.user_id).first()
            assert audit_log is not None
            # 在会话内访问属性
            action = audit_log.action
            detail = audit_log.detail
            assert action == "create_user"
            assert f"创建用户: {saved_user.user_id}" in detail