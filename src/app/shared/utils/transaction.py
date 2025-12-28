"""
事务管理工具模块
提供 Flask-SQLAlchemy 事务管理的最佳实践
"""

import logging
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from app.extensions import db

logger = logging.getLogger(__name__)


def transactional(f):
    """
    事务管理装饰器

    使用上下文管理器确保事务的原子性：
    - 成功时自动提交
    - 失败时自动回滚
    - 记录详细的错误日志
    - 支持嵌套事务（使用 SAVEPOINT）
    - 在测试环境中使用 begin_nested() + commit()，让外层事务回滚时自动回滚所有修改

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
        try:
            # 检查是否在测试环境中
            import config_manager
            if config_manager.is_unit_environment():
                # 测试环境：使用 begin_nested() + commit()，让外层事务回滚时自动回滚所有修改
                with db.session.begin_nested():
                    result = f(*args, **kwargs)
                    db.session.commit()  # 提交到 SAVEPOINT，让 test_client 可以访问
                    return result
            else:
                # 生产环境：使用 begin_nested 支持 SAVEPOINT，允许嵌套事务
                with db.session.begin_nested():
                    result = f(*args, **kwargs)
                    return result
        except SQLAlchemyError as e:
            logger.error(f"事务失败 - 函数: {f.__name__}, 错误: {str(e)}")
            # 上下文管理器会自动回滚到 SAVEPOINT
            raise
    return decorated_function


def transactional_nested(f):
    """
    嵌套事务管理装饰器

    用于需要独立回滚的嵌套操作场景：
    - 内层事务失败不影响外层事务
    - 适用于可选操作或可容忍失败的场景

    使用示例:
        @transactional_nested
        def optional_operation(user_id):
            # 这个操作失败不会影响主事务
            record = AuditLog(user_id=user_id, action="optional")
            db.session.add(record)

    Args:
        f: 被装饰的函数

    Returns:
        装饰后的函数
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            with db.session.begin_nested():
                result = f(*args, **kwargs)
                return result
        except SQLAlchemyError as e:
            logger.warning(f"嵌套事务失败 - 函数: {f.__name__}, 错误: {str(e)}")
            # 嵌套事务失败会回滚到保存点，不影响外层事务
            return None
    return decorated_function


class TransactionManager:
    """
    事务管理器类

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