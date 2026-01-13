"""
事务管理工具类的单元测试
测试装饰器模式和上下文管理器模式的事务管理
"""
import pytest
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from database.flask_models import User, Community
from app.shared.utils.transaction import transactional, transactional_nested, transaction, TransactionManager
from test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname,
    generate_unique_username,
    TestDataManager
)
from test_constants import TEST_CONSTANTS
from hashlib import sha256


class TestTransactionalDecorator:
    """测试 @transactional 装饰器"""

    def test_decorator_success_commit(self, test_session):
        """
        测试装饰器模式 - 正常提交
        验证：成功创建用户并自动提交
        """
        # Arrange
        phone_number = generate_unique_phone_number("decorator_success")
        openid = generate_unique_openid(phone_number, "decorator_success")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act
        @transactional
        def create_user_with_decorator():
            user = User(
                wechat_openid=openid,
                phone_number=phone_number,
                phone_hash=phone_hash,
                nickname=generate_unique_nickname("decorator_success"),
                name=generate_unique_username("decorator_success"),
                role=1,
                status=1
            )
            test_session.add(user)
            return user

        result = create_user_with_decorator()

        # Assert
        assert result is not None
        assert result.phone_number == phone_number

        # 验证用户已保存到数据库
        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is not None
        assert saved_user.wechat_openid == openid

    def test_decorator_exception_rollback(self, test_session):
        """
        测试装饰器模式 - 异常回滚
        验证：发生异常时自动回滚，数据不会保存
        """
        # Arrange
        phone_number = generate_unique_phone_number("decorator_rollback")
        openid = generate_unique_openid(phone_number, "decorator_rollback")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            @transactional
            def create_user_with_error():
                user = User(
                    wechat_openid=openid,
                    phone_number=phone_number,
                    phone_hash=phone_hash,
                    nickname=generate_unique_nickname("decorator_rollback"),
                    name=generate_unique_username("decorator_rollback"),
                    role=1,
                    status=1
                )
                test_session.add(user)
                # 故意抛出异常
                raise SQLAlchemyError("测试异常")

            create_user_with_error()

        # 验证用户未被保存到数据库
        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is None

    def test_decorator_integrity_error(self, test_session):
        """
        测试装饰器模式 - 完整性约束错误
        验证：违反数据库约束时自动回滚
        """
        # Arrange - 创建一个用户
        phone_number = generate_unique_phone_number("decorator_integrity")
        openid = generate_unique_openid(phone_number, "decorator_integrity")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        user = User(
            wechat_openid=openid,
            phone_number=phone_number,
            phone_hash=phone_hash,
            nickname=generate_unique_nickname("decorator_integrity"),
            name=generate_unique_username("decorator_integrity"),
            role=1,
            status=1
        )
        test_session.add(user)
        test_session.commit()

        # Act & Assert - 尝试创建重复 openid 的用户
        with pytest.raises(IntegrityError):
            @transactional
            def create_duplicate_user():
                duplicate_user = User(
                    wechat_openid=openid,  # 重复的 openid
                    phone_number=generate_unique_phone_number("duplicate"),
                    phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:duplicate".encode('utf-8')).hexdigest(),
                    nickname=generate_unique_nickname("duplicate"),
                    name=generate_unique_username("duplicate"),
                    role=1,
                    status=1
                )
                test_session.add(duplicate_user)

            create_duplicate_user()


class TestTransactionContextManager:
    """测试 with transaction() 上下文管理器"""

    def test_context_manager_success_commit(self, test_session):
        """
        测试上下文管理器模式 - 正常提交
        验证：成功创建用户并自动提交
        """
        # Arrange
        phone_number = generate_unique_phone_number("context_success")
        openid = generate_unique_openid(phone_number, "context_success")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act
        with transaction():
            user = User(
                wechat_openid=openid,
                phone_number=phone_number,
                phone_hash=phone_hash,
                nickname=generate_unique_nickname("context_success"),
                name=generate_unique_username("context_success"),
                role=1,
                status=1
            )
            test_session.add(user)

        # Assert
        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is not None
        assert saved_user.wechat_openid == openid

    def test_context_manager_exception_rollback(self, test_session):
        """
        测试上下文管理器模式 - 异常回滚
        验证：发生异常时自动回滚，数据不会保存
        """
        # Arrange
        phone_number = generate_unique_phone_number("context_rollback")
        openid = generate_unique_openid(phone_number, "context_rollback")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            with transaction():
                user = User(
                    wechat_openid=openid,
                    phone_number=phone_number,
                    phone_hash=phone_hash,
                    nickname=generate_unique_nickname("context_rollback"),
                    name=generate_unique_username("context_rollback"),
                    role=1,
                    status=1
                )
                test_session.add(user)
                # 故意抛出异常
                raise SQLAlchemyError("测试异常")

        # 验证用户未被保存到数据库
        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is None

    def test_context_manager_multiple_operations(self, test_session):
        """
        测试上下文管理器模式 - 批量操作
        验证：批量创建用户，全部成功或全部失败
        """
        # Arrange
        user_data_list = []
        for i in range(3):
            phone_number = generate_unique_phone_number(f"context_batch_{i}")
            openid = generate_unique_openid(phone_number, f"context_batch_{i}")
            phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()
            user_data_list.append({
                'openid': openid,
                'phone_number': phone_number,
                'phone_hash': phone_hash,
                'nickname': generate_unique_nickname(f"context_batch_{i}"),
                'name': generate_unique_username(f"context_batch_{i}"),
            })

        # Act
        with transaction():
            for data in user_data_list:
                user = User(
                    wechat_openid=data['openid'],
                    phone_number=data['phone_number'],
                    phone_hash=data['phone_hash'],
                    nickname=data['nickname'],
                    name=data['name'],
                    role=1,
                    status=1
                )
                test_session.add(user)

        # Assert - 验证所有用户都已保存
        test_session.expire_all()
        for data in user_data_list:
            saved_user = test_session.query(User).filter_by(phone_number=data['phone_number']).first()
            assert saved_user is not None
            assert saved_user.wechat_openid == data['openid']

    def test_context_manager_partial_failure_rollback(self, test_session):
        """
        测试上下文管理器模式 - 部分失败回滚
        验证：中间步骤失败时，之前的数据也会回滚
        """
        # Arrange
        phone_number1 = generate_unique_phone_number("context_partial_1")
        phone_number2 = generate_unique_phone_number("context_partial_2")
        phone_number3 = generate_unique_phone_number("context_partial_3")

        # Act & Assert
        with pytest.raises(SQLAlchemyError):
            with transaction():
                # 第一个用户
                user1 = User(
                    wechat_openid=generate_unique_openid(phone_number1, "context_partial_1"),
                    phone_number=phone_number1,
                    phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number1}".encode('utf-8')).hexdigest(),
                    nickname=generate_unique_nickname("context_partial_1"),
                    name=generate_unique_username("context_partial_1"),
                    role=1,
                    status=1
                )
                test_session.add(user1)

                # 第二个用户
                user2 = User(
                    wechat_openid=generate_unique_openid(phone_number2, "context_partial_2"),
                    phone_number=phone_number2,
                    phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number2}".encode('utf-8')).hexdigest(),
                    nickname=generate_unique_nickname("context_partial_2"),
                    name=generate_unique_username("context_partial_2"),
                    role=1,
                    status=1
                )
                test_session.add(user2)

                # 抛出异常
                raise SQLAlchemyError("模拟失败")

                # 第三个用户（不会执行）
                user3 = User(
                    wechat_openid=generate_unique_openid(phone_number3, "context_partial_3"),
                    phone_number=phone_number3,
                    phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number3}".encode('utf-8')).hexdigest(),
                    nickname=generate_unique_nickname("context_partial_3"),
                    name=generate_unique_username("context_partial_3"),
                    role=1,
                    status=1
                )
                test_session.add(user3)

        # Assert - 验证所有用户都未被保存
        test_session.expire_all()
        assert test_session.query(User).filter_by(phone_number=phone_number1).first() is None
        assert test_session.query(User).filter_by(phone_number=phone_number2).first() is None
        assert test_session.query(User).filter_by(phone_number=phone_number3).first() is None


class TestTransactionalNested:
    """测试 @transactional_nested 嵌套事务装饰器"""

    def test_nested_transaction_success(self, test_session):
        """
        测试嵌套事务 - 成功场景
        验证：嵌套事务成功时，数据正常保存
        """
        # Arrange
        phone_number = generate_unique_phone_number("nested_success")
        openid = generate_unique_openid(phone_number, "nested_success")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act
        @transactional
        def create_user_with_nested():
            user = User(
                wechat_openid=openid,
                phone_number=phone_number,
                phone_hash=phone_hash,
                nickname=generate_unique_nickname("nested_success"),
                name=generate_unique_username("nested_success"),
                role=1,
                status=1
            )
            test_session.add(user)

            # 嵌套事务
            @transactional_nested
            def create_community():
                community = Community(
                    name=generate_unique_nickname("nested_success"),
                    status=1
                )
                test_session.add(community)
                return community

            community = create_community()
            return user, community

        user, community = create_user_with_nested()

        # Assert
        assert user is not None
        assert community is not None
        assert user.phone_number == phone_number
        assert community.name.startswith("nickname_nested_s")  # context被截断到8个字符

    def test_nested_transaction_failure_isolated(self, test_session):
        """
        测试嵌套事务 - 失败隔离
        验证：嵌套事务失败时，不影响外层事务
        """
        # Arrange
        phone_number = generate_unique_phone_number("nested_isolated")
        openid = generate_unique_openid(phone_number, "nested_isolated")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act
        @transactional
        def create_user_with_nested_error():
            user = User(
                wechat_openid=openid,
                phone_number=phone_number,
                phone_hash=phone_hash,
                nickname=generate_unique_nickname("nested_isolated"),
                name=generate_unique_username("nested_isolated"),
                role=1,
                status=1
            )
            test_session.add(user)

            # 嵌套事务失败
            @transactional_nested
            def failing_nested():
                raise SQLAlchemyError("嵌套事务失败")

            result = failing_nested()
            assert result is None  # 嵌套事务失败返回 None
            return user

        user = create_user_with_nested_error()

        # Assert - 外层事务的用户应该被保存
        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is not None
        assert saved_user.wechat_openid == openid


class TestTransactionManager:
    """测试 TransactionManager 类"""

    def test_execute_in_transaction(self, test_session):
        """
        测试 TransactionManager.execute_in_transaction
        验证：成功执行并提交
        """
        # Arrange
        phone_number = generate_unique_phone_number("tm_execute")
        openid = generate_unique_openid(phone_number, "tm_execute")
        phone_hash = sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest()

        # Act
        def create_user():
            user = User(
                wechat_openid=openid,
                phone_number=phone_number,
                phone_hash=phone_hash,
                nickname=generate_unique_nickname("tm_execute"),
                name=generate_unique_username("tm_execute"),
                role=1,
                status=1
            )
            test_session.add(user)
            return user

        result = TransactionManager.execute_in_transaction(create_user)

        # Assert
        assert result is not None
        assert result.phone_number == phone_number

        test_session.expire_all()
        saved_user = test_session.query(User).filter_by(phone_number=phone_number).first()
        assert saved_user is not None

    def test_flush_without_commit(self, test_session):
        """
        测试 TransactionManager.flush
        验证：刷新但不提交，可以获取生成的ID
        """
        # Arrange
        community_name = generate_unique_nickname("flush_test")
        community = Community(
            name=community_name,
            status=1
        )
        test_session.add(community)

        # Act
        TransactionManager.flush()

        # Assert - 可以获取生成的ID，但事务未提交
        assert community.community_id is not None

        # 提交事务
        test_session.commit()

        test_session.expire_all()
        saved_community = test_session.query(Community).filter_by(name=community_name).first()
        assert saved_community is not None
        assert saved_community.community_id == community.community_id