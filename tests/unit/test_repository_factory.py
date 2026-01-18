"""
测试 RepositoryFactory
"""
import pytest
from app.infrastructure.persistence.repository_factory import RepositoryFactory

def test_get_outbox_repository():
    """测试获取 Outbox 仓储"""
    repo1 = RepositoryFactory.get_outbox_repository()
    repo2 = RepositoryFactory.get_outbox_repository()

    # 验证单例模式
    assert repo1 is repo2
    assert repo1 is not None

def test_reset_repository_factory():
    """测试重置仓储工厂"""
    repo1 = RepositoryFactory.get_outbox_repository()
    RepositoryFactory.reset()
    repo2 = RepositoryFactory.get_outbox_repository()

    # 验证重置后创建新实例
    assert repo1 is not repo2
