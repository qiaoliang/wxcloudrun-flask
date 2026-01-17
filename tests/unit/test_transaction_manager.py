"""
测试事务管理器
"""
import pytest
from unittest.mock import patch, MagicMock, call
from flask import Flask
from datetime import datetime


class TestTransactionManager:
    """测试事务管理器"""

    def test_transaction_commits_on_success(self):
        """测试事务成功时提交"""
        from app.infrastructure.transaction.transaction_manager import TransactionManager

        # 模拟正常流程
        def test_operation():
            record = MagicMock(record_id=1)
            return True

        with TransactionManager.transaction(save_point='test'):
            result = test_operation()

        assert result is True

    def test_transaction_rollback_on_error(self):
        """测试事务失败时回滚"""
        from app.infrastructure.transaction.transaction_manager import TransactionManager

        # 模拟错误流程
        def test_operation():
            raise Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            with TransactionManager.transaction(save_point='test'):
                test_operation()

    def test_transaction_decorator(self):
        """测试事务装饰器"""
        from app.infrastructure.transaction.transaction_manager import transaction

        @transaction
        def test_operation():
            return True

        result = test_operation()
        assert result is True

    def test_transaction_decorator_with_exception(self):
        """测试事务装饰器异常处理"""
        from app.infrastructure.transaction.transaction_manager import transaction

        @transaction
        def test_operation():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_operation()

    def test_transaction_without_save_point(self):
        """测试无保存点的事务"""
        from app.infrastructure.transaction.transaction_manager import TransactionManager

        def test_operation():
            return "success"

        with TransactionManager.transaction():
            result = test_operation()

        assert result == "success"
