"""
模型查询混入类
为纯 SQLAlchemy 模型提供类似 Flask-SQLAlchemy 的查询接口
"""
from typing import TypeVar, TYPE_CHECKING
from .core import get_database

if TYPE_CHECKING:
    from sqlalchemy.orm import Query

T = TypeVar('T', bound='QueryMixin')


class QueryMixin:
    """
    查询混入类，为模型提供 query 属性
    """
    
    @classmethod
    def query(cls: type[T]) -> 'Query':
        """
        获取查询对象，模仿 Flask-SQLAlchemy 的 query 属性
        """
        db = get_database()
        return db.query(cls)
    
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