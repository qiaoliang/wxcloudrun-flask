"""
模型查询混入类
为纯 SQLAlchemy 模型提供类似 Flask-SQLAlchemy 的查询接口
"""
from typing import TypeVar, TYPE_CHECKING
from .core import get_database

if TYPE_CHECKING:
    from sqlalchemy.orm import Query

T = TypeVar('T', bound='QueryMixin')


class QueryProperty:
    """查询属性描述符，模仿 Flask-SQLAlchemy 的 query 属性"""
    
    def __get__(self, instance, owner):
        if instance is not None:
            # 实例访问时返回 None
            return None
        
        # 类访问时返回查询对象
        # 尝试检测是否在 Flask 应用上下文中
        try:
            from flask import current_app
            # 如果在 Flask 应用上下文中，使用应用的数据库核心
            if hasattr(current_app, 'db_core'):
                return current_app.db_core.query(owner)
        except (RuntimeError, ImportError):
            # 不在 Flask 应用上下文中，使用全局数据库
            pass
        
        # 使用全局数据库
        db = get_database()
        return db.query(owner)


class QueryMixin:
    """
    查询混入类，为模型提供 query 属性
    """
    
    # 将 query 定义为类属性
    query = QueryProperty()
    
    @classmethod
    def get(cls: type[T], ident):
        """
        根据主键获取对象，模仿 Flask-SQLAlchemy 的 get 方法
        """
        return cls.query.get(ident)
    
    @classmethod
    def filter_by(cls: type[T], **kwargs):
        """
        过滤查询，模仿 Flask-SQLAlchemy 的 filter_by 方法
        """
        return cls.query.filter_by(**kwargs)
    
    @classmethod
    def filter(cls: type[T], *criterion):
        """
        过滤查询，模仿 Flask-SQLAlchemy 的 filter 方法
        """
        return cls.query.filter(*criterion)
    
    @classmethod
    def all(cls: type[T]):
        """
        获取所有记录，模仿 Flask-SQLAlchemy 的 all 方法
        """
        return cls.query.all()
    
    @classmethod
    def first(cls: type[T]):
        """
        获取第一条记录，模仿 Flask-SQLAlchemy 的 first 方法
        """
        return cls.query.first()
    
    @classmethod
    def count(cls: type[T]):
        """
        获取记录数量，模仿 Flask-SQLAlchemy 的 count 方法
        """
        return cls.query.count()