"""
事务管理器

提供事务装饰器和事务上下文管理
"""
import logging
from contextlib import contextmanager
from typing import Callable, Optional
from flask import current_app, has_app_context

from database.flask_models import db


logger = logging.getLogger(__name__)


class TransactionManager:
    """事务管理器"""

    @staticmethod
    @contextmanager
    def transaction(save_point: Optional[str] = None):
        """
        事务上下文管理器

        Args:
            save_point: 保存点名称,用于嵌套事务

        Yields:
            None

        Raises:
            Exception: 事务失败时抛出异常
        """
        # 使用可用的 logger
        log = current_app.logger if has_app_context() else logger

        if save_point:
            log.debug(f'开始事务,保存点: {save_point}')

        try:
            yield
            if save_point:
                log.debug(f'事务成功,保存点: {save_point}')
        except Exception as e:
            log.error(f'事务失败,保存点: {save_point}, 错误: {str(e)}')
            raise


class TransactionDecorator:
    """事务装饰器"""

    def __call__(self, func: Callable) -> Callable:
        """
        装饰器方法

        Args:
            func: 被装饰的函数

        Returns:
            Callable: 包装后的函数
        """
        def wrapper(*args, **kwargs):
            with TransactionManager.transaction(save_point=func.__name__):
                return func(*args, **kwargs)
        return wrapper


# 便捷装饰器
transaction = TransactionDecorator()
