"""
领域事件

从 domain_event 重新导出 DomainEvent，保持向后兼容
"""
from .domain_event import DomainEvent

__all__ = ['DomainEvent']
