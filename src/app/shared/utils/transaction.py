"""
事务管理工具模块
提供 Flask-SQLAlchemy 事务管理的最佳实践
"""

import logging
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from flask import has_app_context
from app.extensions import db
from config import EnvironmentHelper

logger = logging.getLogger(__name__)


def transactional(f):
    """
    事务管理装饰器（简化版，符合 DDD 文档示例）

    功能：
    - 成功时自动提交事务
    - 失败时自动回滚事务
    - 记录详细的错误日志
    - 测试环境使用 begin_nested() + commit()，让外层事务回滚时自动回滚所有修改
    - 在没有应用上下文时（如使用 Mock 的单元测试）跳过事务管理

    使用示例:
        @transactional
        def create_user(user_data):
            user = User(**user_data)
            db.session.add(user)
            return user

    Args:
        f: 被装饰的函数

    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 如果没有应用上下文（如使用 Mock 的单元测试），直接执行函数
        if not has_app_context():
            try:
                return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"执行失败（无应用上下文）- 函数: {f.__name__}, 错误: {str(e)}")
                raise

        try:
            # 执行被装饰的函数
            result = f(*args, **kwargs)

            # 检查是否在测试环境中
            if EnvironmentHelper.is_unit():
                # 测试环境：使用 begin_nested() + commit()，让外层事务回滚时自动回滚所有修改
                with db.session.begin_nested():
                    db.session.commit()  # 提交到 SAVEPOINT，让 test_client 可以访问
                    return result
            else:
                # 生产环境：直接提交事务
                db.session.commit()
                logger.debug(f"事务提交成功 - 函数: {f.__name__}")
                return result

        except SQLAlchemyError as e:
            # 数据库异常，回滚事务
            db.session.rollback()
            logger.error(f"事务失败（数据库错误）- 函数: {f.__name__}, 错误: {str(e)}")
            raise

        except Exception as e:
            # 其他异常，回滚事务
            db.session.rollback()
            logger.error(f"事务失败（业务异常）- 函数: {f.__name__}, 错误: {str(e)}")
            raise

    return decorated_function


def transactional_nested(f):
    """
    嵌套事务管理装饰器（保持不变）

    用于需要独立回滚的嵌套操作场景：
    - 内层事务失败不影响外层事务
    - 适用于可选操作或可容忍失败的场景
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            with db.session.begin_nested():
                result = f(*args, **kwargs)
                return result
        except SQLAlchemyError as e:
            logger.warning(f"嵌套事务失败 - 函数: {f.__name__}, 错误: {str(e)}")
            return None
    return decorated_function


class TransactionManager:
    """
    事务管理器类（保持不变）

    提供更灵活的事务控制方式，适用于复杂场景
    """

    @staticmethod
    def execute_in_transaction(func, *args, **kwargs):
        """
        在事务中执行函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果

        Raises:
            SQLAlchemyError: 事务执行失败
        """
        try:
            with db.session.begin():
                return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.error(f"事务执行失败: {str(e)}")
            raise

    @staticmethod
    def execute_in_nested_transaction(func, *args, **kwargs):
        """
        在嵌套事务中执行函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            函数执行结果，失败时返回 None
        """
        try:
            with db.session.begin_nested():
                return func(*args, **kwargs)
        except SQLAlchemyError as e:
            logger.warning(f"嵌套事务执行失败: {str(e)}")
            return None

    @staticmethod
    def commit():
        """手动提交事务（谨慎使用）"""
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            logger.error(f"提交失败: {str(e)}")
            db.session.rollback()
            raise

    @staticmethod
    def rollback():
        """手动回滚事务"""
        try:
            db.session.rollback()
        except SQLAlchemyError as e:
            logger.error(f"回滚失败: {str(e)}")
            raise

    @staticmethod
    def flush():
        """
        刷新会话，但不提交

        用于获取数据库生成的ID，同时保持事务开启
        """
        try:
            db.session.flush()
        except SQLAlchemyError as e:
            logger.error(f"刷新失败: {str(e)}")
            db.session.rollback()
            raise


def transaction():
    """
    事务上下文管理器（保持不变）

    用于复杂操作场景，特别是批量操作或多步骤操作：
    - 成功时自动提交
    - 失败时自动回滚
    - 适用于需要多个数据库操作的场景
    - 支持条件跳过、循环等复杂逻辑

    使用示例:
        def add_staff(community_id, user_ids, role):
            added_count = 0
            with transaction():
                for uid in user_ids:
                    staff = CommunityStaff(community_id=community_id, user_id=uid, role=role)
                    db.session.add(staff)
                    added_count += 1
            return added_count

    Returns:
        TransactionContext: 事务上下文管理器
    """

    class TransactionContext:
        def __enter__(self):
            # 在所有环境下都使用 begin_nested()
            # begin_nested() 会智能地检查 Session 是否已有事务：
            # - 如果已有事务，则创建 SAVEPOINT
            # - 如果没有事务，则创建新事务
            # 这样可以避免 "A transaction is already begun on this Session" 错误
            self.session = db.session.begin_nested()
            return self.session

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type is not None:
                # 发生异常，自动回滚
                try:
                    self.session.rollback()
                    logger.error(f"事务回滚: {exc_type.__name__}: {str(exc_val)}")
                except Exception as rollback_error:
                    logger.error(f"回滚失败: {str(rollback_error)}")
                # 返回 False 让异常被重新抛出
                return False
            else:
                # 正常退出，自动提交
                try:
                    self.session.commit()
                    logger.debug("事务提交成功")
                except Exception as commit_error:
                    logger.error(f"提交失败: {str(commit_error)}")
                    # 返回 False 让异常被重新抛出
                    return False
            return False

    return TransactionContext()