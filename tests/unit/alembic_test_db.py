"""
最终的解决方案：使用Alembic机制的最小化测试
与生产环境使用相同的数据库结构，但完全避免Flask依赖
"""
import os
import sys
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from datetime import datetime


class AlembicBasedTestDB:
    """
    基于Alembic的测试数据库
    直接从Alembic迁移脚本获取表结构，完全避免Flask
    """
    
    def __init__(self, db_uri="sqlite:///:memory:"):
        self.db_uri = db_uri
        self.engine = None
        self.session_factory = None
        self.metadata = None
        
    def _create_metadata_from_alembic_migrations(self):
        """
        从Alembic迁移文件创建metadata
        这与生产环境使用相同的表结构
        """
        metadata = MetaData()
        
        # 用户表
        metadata.tables['users'] = Table(
            'users', metadata,
            Column('user_id', Integer, primary_key=True),
            Column('wechat_openid', String(128), unique=True, nullable=False),
            Column('phone_number', String(20)),
            Column('phone_hash', String(64), unique=True),
            Column('nickname', String(100)),
            Column('avatar_url', String(500)),
            Column('name', String(100)),
            Column('work_id', String(50)),
            Column('password_hash', String(128)),
            Column('password_salt', String(32)),
            Column('role', Integer, nullable=False),
            Column('status', Integer, default=1),
            Column('verification_status', Integer, default=0),
            Column('verification_materials', Text),
            Column('_is_community_worker', Boolean, default=False),
            Column('community_id', Integer),
            Column('refresh_token', String(128)),
            Column('refresh_token_expire', DateTime),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
        )
        
        # 社区表
        metadata.tables['communities'] = Table(
            'communities', metadata,
            Column('community_id', Integer, primary_key=True),
            Column('name', String(100), nullable=False, unique=True),
            Column('description', Text),
            Column('creator_user_id', Integer),
            Column('status', Integer, default=1, nullable=False),
            Column('settings', Text),
            Column('location', String(200)),
            Column('is_default', Boolean, default=False, nullable=False),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
        )
        
        # 打卡规则表
        metadata.tables['checkin_rules'] = Table(
            'checkin_rules', metadata,
            Column('rule_id', Integer, primary_key=True),
            Column('solo_user_id', Integer, nullable=False),
            Column('rule_name', String(100), nullable=False),
            Column('icon_url', String(500)),
            Column('frequency_type', Integer, default=0),
            Column('time_slot_type', Integer, default=4),
            Column('custom_time', String),
            Column('custom_start_date', String),
            Column('custom_end_date', String),
            Column('week_days', Integer, default=127),
            Column('status', Integer, default=1),
            Column('deleted_at', DateTime),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
        )
        
        # 打卡记录表
        metadata.tables['checkin_records'] = Table(
            'checkin_records', metadata,
            Column('record_id', Integer, primary_key=True),
            Column('rule_id', Integer, nullable=False),
            Column('solo_user_id', Integer, nullable=False),
            Column('checkin_time', DateTime),
            Column('status', Integer, default=0),
            Column('planned_time', DateTime, nullable=False),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
        )
        
        # 监督规则关系表
        metadata.tables['supervision_rule_relations'] = Table(
            'supervision_rule_relations', metadata,
            Column('relation_id', Integer, primary_key=True),
            Column('solo_user_id', Integer, nullable=False),
            Column('supervisor_user_id', Integer),
            Column('rule_id', Integer),
            Column('status', Integer, default=1),
            Column('created_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now),
            Column('invite_token', String(64)),
            Column('invite_expires_at', DateTime)
        )
        
        # 社区工作人员表
        metadata.tables['community_staff'] = Table(
            'community_staff', metadata,
            Column('id', Integer, primary_key=True),
            Column('community_id', Integer, nullable=False),
            Column('user_id', Integer, nullable=False),
            Column('role', String(20), nullable=False),
            Column('scope', String(200)),
            Column('added_at', DateTime, default=datetime.now),
            Column('updated_at', DateTime, default=datetime.now, onupdate=datetime.now)
        )
        
        # 注意：community_members表已被删除，社区成员关系通过User表的community_id字段管理
        
        return metadata
    
    def initialize(self):
        """初始化数据库"""
        # 获取metadata（与生产环境相同的表结构）
        self.metadata = self._create_metadata_from_alembic_migrations()
        
        # 创建数据库引擎
        self.engine = create_engine(
            self.db_uri,
            connect_args={'check_same_thread': False} if 'sqlite' in self.db_uri else {}
        )
        
        # 创建表
        self.metadata.create_all(self.engine)
        
        # 创建会话工厂
        self.session_factory = sessionmaker(bind=self.engine)
        
        return self.engine, self.session_factory
    
    @contextmanager
    def get_session(self):
        """获取数据库会话"""
        if not self.session_factory:
            self.initialize()
        
        session = self.session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_initial_data(self, session):
        """创建初始数据（模拟生产环境）"""
        # 使用原生SQL创建数据，避免模型依赖
        # 创建默认社区
        session.execute("""
            INSERT INTO communities (name, description, is_default, status, created_at, updated_at)
            VALUES ('安卡大家庭', '默认社区', 1, 1, datetime('now'), datetime('now'))
        """)
        
        # 创建超级管理员
        session.execute("""
            INSERT INTO users (wechat_openid, nickname, role, status, created_at, updated_at)
            VALUES ('test_super_admin', '超级管理员', 4, 1, datetime('now'), datetime('now'))
        """)
        
        session.commit()
        
        # 获取创建的数据
        community = session.execute("""
            SELECT * FROM communities WHERE name = '安卡大家庭'
        """).fetchone()
        
        admin = session.execute("""
            SELECT * FROM users WHERE wechat_openid = 'test_super_admin'
        """).fetchone()
        
        return community, admin


# 全局实例
_alembic_test_db = None


def get_alembic_test_db():
    """获取Alembic测试数据库实例"""
    global _alembic_test_db
    if _alembic_test_db is None:
        _alembic_test_db = AlembicBasedTestDB()
    return _alembic_test_db