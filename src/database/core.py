"""
数据库核心模块 - 完全独立于Flask
提供统一的数据库接口，支持三种使用模式
"""
import os
from typing import Optional, Union
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager


class DatabaseCore:
    """
    数据库核心类
    完全独立于Flask，支持多种使用模式
    """

    def __init__(self, mode: str = 'standalone'):
        """
        初始化数据库核心
        :param mode: 使用模式
                  - 'test': 测试模式，内存数据库
                  - 'standalone': 独立模式，文件数据库
                  - 'flask': Flask模式，等待注入
        """
        self.mode = mode
        self.engine = None
        self.session_factory = None
        self.metadata = MetaData()
        self._is_initialized = False

    def initialize(self, db_uri: Optional[str] = None):
        """
        初始化数据库
        :param db_uri: 数据库连接URI
        """
        if self._is_initialized:
            return

        # 根据模式确定数据库URI
        if db_uri is None:
            if self.mode == 'test':
                db_uri = 'sqlite:///:memory:'
            elif self.mode == 'standalone':
                # 使用环境配置中的数据库路径
                from config_manager import get_database_config
                db_config = get_database_config()
                db_uri = db_config['SQLALCHEMY_DATABASE_URI']
            elif self.mode == 'flask':
                # Flask模式下等待外部注入
                return
            else:
                raise ValueError(f"未知的数据库模式: {self.mode}")

        # 创建引擎
        if 'sqlite:///:memory:' in db_uri:
            # 内存数据库特殊配置
            self.engine = create_engine(
                db_uri,
                poolclass=StaticPool,
                connect_args={'check_same_thread': False},
                echo=False
            )
        elif 'sqlite:///' in db_uri:
            # SQLite文件数据库使用NullPool避免连接池问题
            from sqlalchemy.pool import NullPool
            self.engine = create_engine(
                db_uri,
                poolclass=NullPool,
                echo=False
            )
        else:
            self.engine = create_engine(db_uri, echo=False)

        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        self._is_initialized = True

        # 自动创建表（除了Flask模式）
        if self.mode != 'flask':
            self.create_tables()

    def bind_to_flask(self, flask_db, app):
        """
        仅在flask模式下使用
        """
        if self.mode != 'flask':
            raise ValueError("只有在flask模式下才能绑定到Flask")

        # 直接使用Flask应用的引擎
        with app.app_context():
            self.engine = flask_db.engine
            self.session_factory = flask_db.session
            self._is_initialized = True

            # 创建表
            self.create_tables()

    @contextmanager
    def get_session(self) -> Session:
        """
        获取数据库会话
        """
        if not self._is_initialized:
            raise RuntimeError("数据库未初始化")

        if self.mode == 'flask':
            # Flask模式下直接返回session
            yield self.session_factory
        else:
            # 其他模式创建新会话
            session = self.session_factory()
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise
            finally:
                session.close()

    def query(self, *entities, **kwargs):
        """
        提供 query 方法
        """
        if not self._is_initialized:
            raise RuntimeError("数据库未初始化")

        # 直接使用 session_factory 创建查询
        if self.session_factory:
            return self.session_factory().query(*entities, **kwargs)
        else:
            # 如果没有 session_factory（如 Flask 模式），尝试从应用获取
            try:
                from flask import current_app
                if hasattr(current_app, 'db_core'):
                    return current_app.db_core.session_factory().query(*entities, **kwargs)
            except (RuntimeError, AttributeError):
                pass

            raise RuntimeError("无法获取数据库会话")

    def create_tables(self):
        """创建所有表"""
        if not self._is_initialized:
            raise RuntimeError("数据库未初始化")

        # 导入模型定义
        from .models import Base
        Base.metadata.create_all(self.engine)

    def drop_tables(self):
        """删除所有表"""
        if not self._is_initialized:
            raise RuntimeError("数据库未初始化")

        from .models import Base
        Base.metadata.drop_all(self.engine)

    def reset_database(self):
        """重置数据库（仅测试模式）"""
        if self.mode != 'test':
            raise ValueError("只有测试模式支持重置数据库")

        self.drop_tables()
        self.create_tables()


# 全局数据库实例
_db_core: Optional[DatabaseCore] = None


def get_database(mode: str = 'standalone') -> DatabaseCore:
    """
    获取数据库核心实例
    :param mode: 使用模式
    :return: 数据库核心实例
    """
    global _db_core

    if _db_core is None or _db_core.mode != mode:
        _db_core = DatabaseCore(mode)

        # 自动初始化（除了flask模式）
        if mode != 'flask':
            _db_core.initialize()

    return _db_core


def initialize_for_test():
    """初始化测试数据库"""
    db = get_database('test')
    db.create_tables()
    return db


def initialize_for_standalone(db_uri: str = None):
    """初始化独立数据库"""
    db = get_database('standalone')
    db.initialize(db_uri)
    db.create_tables()
    return db


def bind_flask_db(flask_db, app=None):
    """绑定Flask数据库"""
    db = get_database('flask')
    db.bind_to_flask(flask_db, app)
    return db


# 便捷函数
def get_session(mode: str = 'standalone'):
    """获取数据库会话"""
    db = get_database(mode)
    return db.get_session()


def reset_all():
    """重置所有数据库实例（主要用于测试）"""
    global _db_core
    _db_core = None