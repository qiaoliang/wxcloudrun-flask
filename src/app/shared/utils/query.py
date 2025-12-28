"""
查询工具模块
提供 Flask-SQLAlchemy 2.0 查询的最佳实践
"""

import logging
from typing import List, Optional, Type, Any, Tuple
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, joinedload, subqueryload
from app.extensions import db

logger = logging.getLogger(__name__)


class QueryHelper:
    """
    查询工具类

    提供统一的查询接口，封装 SQLAlchemy 2.0 API
    """

    @staticmethod
    def get_by_id(model: Type, id: Any) -> Optional[Any]:
        """
        根据主键ID获取对象

        Args:
            model: 模型类
            id: 主键值

        Returns:
            模型实例，不存在时返回 None
        """
        try:
            return db.session.get(model, id)
        except Exception as e:
            logger.error(f"查询失败 - 模型: {model.__name__}, ID: {id}, 错误: {str(e)}")
            return None

    @staticmethod
    def get_one(model: Type, filters: Optional[List] = None,
                options: Optional[List] = None) -> Optional[Any]:
        """
        获取单个对象

        Args:
            model: 模型类
            filters: 过滤条件列表，如 [Model.status == 1, Model.name == 'test']
            options: 预加载选项，如 [selectinload(Model.community)]

        Returns:
            模型实例，不存在时返回 None
        """
        try:
            stmt = select(model)
            if filters:
                stmt = stmt.where(*filters)
            if options:
                stmt = stmt.options(*options)
            return db.session.execute(stmt).scalar_one_or_none()
        except Exception as e:
            logger.error(f"查询单个对象失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return None

    @staticmethod
    def get_all(model: Type, filters: Optional[List] = None,
                order_by: Optional[Any] = None,
                limit: Optional[int] = None,
                offset: Optional[int] = None,
                options: Optional[List] = None) -> List[Any]:
        """
        获取所有对象

        Args:
            model: 模型类
            filters: 过滤条件列表
            order_by: 排序条件，如 Model.created_at.desc()
            limit: 返回数量限制
            offset: 偏移量
            options: 预加载选项

        Returns:
            模型实例列表
        """
        try:
            stmt = select(model)
            if filters:
                stmt = stmt.where(*filters)
            if order_by:
                stmt = stmt.order_by(order_by)
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            if options:
                stmt = stmt.options(*options)
            return db.session.execute(stmt).scalars().all()
        except Exception as e:
            logger.error(f"查询列表失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return []

    @staticmethod
    def count(model: Type, filters: Optional[List] = None) -> int:
        """
        统计对象数量

        Args:
            model: 模型类
            filters: 过滤条件列表

        Returns:
            对象数量
        """
        try:
            stmt = select(func.count()).select_from(model)
            if filters:
                stmt = stmt.where(*filters)
            return db.session.execute(stmt).scalar() or 0
        except Exception as e:
            logger.error(f"统计失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return 0

    @staticmethod
    def exists(model: Type, filters: Optional[List] = None) -> bool:
        """
        检查对象是否存在

        Args:
            model: 模型类
            filters: 过滤条件列表

        Returns:
            是否存在
        """
        try:
            stmt = select(func.count()).select_from(model)
            if filters:
                stmt = stmt.where(*filters)
            count = db.session.execute(stmt).scalar()
            return count > 0
        except Exception as e:
            logger.error(f"检查存在性失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return False

    @staticmethod
    def paginate(model: Type, filters: Optional[List] = None,
                 order_by: Optional[Any] = None,
                 page: int = 1, per_page: int = 20,
                 options: Optional[List] = None) -> Tuple[List[Any], int]:
        """
        分页查询

        Args:
            model: 模型类
            filters: 过滤条件列表
            order_by: 排序条件
            page: 页码（从1开始）
            per_page: 每页数量
            options: 预加载选项

        Returns:
            (对象列表, 总数)
        """
        try:
            # 获取总数
            total = QueryHelper.count(model, filters)

            # 获取分页数据
            offset = (page - 1) * per_page
            items = QueryHelper.get_all(
                model, filters, order_by, per_page, offset, options
            )

            return items, total
        except Exception as e:
            logger.error(f"分页查询失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return [], 0

    @staticmethod
    def bulk_insert(model: Type, data_list: List[dict]) -> bool:
        """
        批量插入

        Args:
            model: 模型类
            data_list: 数据字典列表

        Returns:
            是否成功
        """
        try:
            db.session.bulk_insert_mappings(model, data_list)
            return True
        except Exception as e:
            logger.error(f"批量插入失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return False

    @staticmethod
    def bulk_update(model: Type, data_list: List[dict]) -> bool:
        """
        批量更新

        Args:
            model: 模型类
            data_list: 数据字典列表（必须包含主键）

        Returns:
            是否成功
        """
        try:
            db.session.bulk_update_mappings(model, data_list)
            return True
        except Exception as e:
            logger.error(f"批量更新失败 - 模型: {model.__name__}, 错误: {str(e)}")
            return False


class QueryBuilder:
    """
    查询构建器

    提供链式查询接口，简化复杂查询的构建
    """

    def __init__(self, model: Type):
        """
        初始化查询构建器

        Args:
            model: 模型类
        """
        self.model = model
        self._filters = []
        self._orders = []
        self._options = []
        self._limit = None
        self._offset = None

    def filter(self, *filters) -> 'QueryBuilder':
        """
        添加过滤条件

        Args:
            *filters: 过滤条件列表

        Returns:
            查询构建器实例
        """
        self._filters.extend(filters)
        return self

    def order_by(self, *orders) -> 'QueryBuilder':
        """
        添加排序条件

        Args:
            *orders: 排序条件列表

        Returns:
            查询构建器实例
        """
        self._orders.extend(orders)
        return self

    def options(self, *options) -> 'QueryBuilder':
        """
        添加预加载选项

        Args:
            *options: 预加载选项列表

        Returns:
            查询构建器实例
        """
        self._options.extend(options)
        return self

    def limit(self, limit: int) -> 'QueryBuilder':
        """
        设置返回数量限制

        Args:
            limit: 返回数量

        Returns:
            查询构建器实例
        """
        self._limit = limit
        return self

    def offset(self, offset: int) -> 'QueryBuilder':
        """
        设置偏移量

        Args:
            offset: 偏移量

        Returns:
            查询构建器实例
        """
        self._offset = offset
        return self

    def first(self) -> Optional[Any]:
        """
        获取第一个结果

        Returns:
            模型实例，不存在时返回 None
        """
        return QueryHelper.get_one(
            self.model, self._filters, self._options
        )

    def all(self) -> List[Any]:
        """
        获取所有结果

        Returns:
            模型实例列表
        """
        order_by = self._orders[0] if self._orders else None
        return QueryHelper.get_all(
            self.model, self._filters, order_by,
            self._limit, self._offset, self._options
        )

    def count(self) -> int:
        """
        统计结果数量

        Returns:
            结果数量
        """
        return QueryHelper.count(self.model, self._filters)

    def exists(self) -> bool:
        """
        检查结果是否存在

        Returns:
            是否存在
        """
        return QueryHelper.exists(self.model, self._filters)

    def paginate(self, page: int = 1, per_page: int = 20) -> Tuple[List[Any], int]:
        """
        分页查询

        Args:
            page: 页码
            per_page: 每页数量

        Returns:
            (对象列表, 总数)
        """
        order_by = self._orders[0] if self._orders else None
        return QueryHelper.paginate(
            self.model, self._filters, order_by,
            page, per_page, self._options
        )