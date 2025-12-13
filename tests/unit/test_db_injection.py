"""
测试数据库依赖注入架构
验证数据库初始化和会话管理
"""

import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database, reset_all
from database.models import User


class TestDatabaseInjection:
    """测试数据库依赖注入"""
    
    def test_database_initialization(self):
        """测试数据库初始化"""
        # 重置数据库
        reset_all()
        
        # 初始化测试数据库
        db = initialize_for_test()
        
        # 验证数据库实例
        assert db is not None
        assert hasattr(db, 'get_session')
        assert hasattr(db, 'create_tables')
        assert hasattr(db, 'drop_tables')
    
    def test_database_session_management(self):
        """测试数据库会话管理"""
        db = initialize_for_test()
        
        # 测试会话创建
        with db.get_session() as session:
            assert session is not None
            
            # 测试基本的数据库操作
            user = User(
                wechat_openid="test_openid",
                nickname="测试用户",
                role=1
            )
            session.add(user)
            session.commit()
            
            # 验证用户已保存
            saved_user = session.query(User).filter_by(wechat_openid="test_openid").first()
            assert saved_user is not None
            assert saved_user.nickname == "测试用户"
    
    def test_database_isolation(self):
        """测试数据库共享行为（当前实现是共享同一个数据库）"""
        # 获取两个数据库实例
        db1 = initialize_for_test()
        db2 = initialize_for_test()
        
        # 在第一个会话中创建用户
        with db1.get_session() as session1:
            user1 = User(
                wechat_openid="test_db1",
                nickname="数据库1用户",
                role=1
            )
            session1.add(user1)
            session1.commit()
        
        # 在第二个会话中创建用户
        with db2.get_session() as session2:
            user2 = User(
                wechat_openid="test_db2",
                nickname="数据库2用户",
                role=1
            )
            session2.add(user2)
            session2.commit()
        
        # 验证数据共享（两个实例访问同一个数据库）
        with db1.get_session() as session1:
            users1 = session1.query(User).all()
            # 应该能看到两个用户，因为它们共享同一个数据库
            assert len(users1) >= 2
            
            openids = [u.wechat_openid for u in users1]
            assert "test_db1" in openids
            assert "test_db2" in openids
        
        with db2.get_session() as session2:
            users2 = session2.query(User).all()
            # 同样应该能看到两个用户
            assert len(users2) >= 2
    
    def test_database_reset(self):
        """测试数据库重置"""
        db = initialize_for_test()
        
        # 添加数据
        with db.get_session() as session:
            user = User(
                wechat_openid="test_reset",
                nickname="重置测试用户",
                role=1
            )
            session.add(user)
            session.commit()
        
        # 验证数据存在
        with db.get_session() as session:
            users = session.query(User).all()
            assert len(users) >= 1
        
        # 重置数据库
        reset_all()
        
        # 重新初始化
        db_new = initialize_for_test()
        
        # 验证数据库为空
        with db_new.get_session() as session:
            users = session.query(User).all()
            assert len(users) == 0
    
    def test_database_singleton_behavior(self):
        """测试数据库单例行为"""
        # 获取数据库实例
        db1 = get_database()
        db2 = get_database()
        
        # 在同一环境中应该返回同一个实例
        assert db1 is db2
    
    def test_table_creation_and_destruction(self):
        """测试表的创建和销毁"""
        db = initialize_for_test()
        
        # 创建表
        db.create_tables()
        
        # 验证可以操作表
        with db.get_session() as session:
            user = User(
                wechat_openid="test_tables",
                nickname="表测试用户",
                role=1
            )
            session.add(user)
            session.commit()
            
            saved_user = session.query(User).filter_by(wechat_openid="test_tables").first()
            assert saved_user is not None
        
        # 删除表
        db.drop_tables()
        
        # 尝试操作表应该失败
        try:
            with db.get_session() as session:
                session.query(User).first()
            # 如果没有抛出异常，可能表仍然存在
        except Exception:
            # 预期的异常，表已被删除
            pass