"""
验证数据库依赖注入概念的测试
展示数据库初始化和使用模式
"""

import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database, reset_all
from database.flask_models import User


class TestDatabaseInjectionConcept:
    """测试数据库依赖注入概念"""

    def test_database_first_then_use(self):
        """测试先创建数据库，后使用的概念"""
        # 1. 重置并初始化数据库
        reset_all()
        db = initialize_for_test()

        # 2. 验证数据库已准备好
        assert db is not None
        assert hasattr(db, 'get_session')

        # 3. 使用数据库进行操作
        import time
        timestamp = str(int(time.time() * 1000))

        with db.get_session() as session:
            user = User(
                wechat_openid=f"concept_test_{timestamp}",
                nickname="概念测试用户",
                role=1
            )
            session.add(user)
            session.commit()

            # 验证数据已保存
            saved_user = session.query(User).filter_by(wechat_openid=f"concept_test_{timestamp}").first()
            assert saved_user is not None
            assert saved_user.nickname == "概念测试用户"

    def test_database_singleton_across_operations(self):
        """测试数据库单例在多个操作中的行为"""
        # 获取数据库实例
        db1 = get_database()
        db2 = get_database()

        # 应该是同一个实例
        assert db1 is db2

        # 使用时间戳确保唯一性
        import time
        timestamp = str(int(time.time() * 1000))

        # 在不同会话中操作
        with db1.get_session() as session1:
            user1 = User(
                wechat_openid=f"singleton_test_1_{timestamp}",
                nickname="单例测试用户1",
                role=1
            )
            session1.add(user1)
            session1.commit()

        with db2.get_session() as session2:
            user2 = User(
                wechat_openid=f"singleton_test_2_{timestamp}",
                nickname="单例测试用户2",
                role=1
            )
            session2.add(user2)
            session2.commit()

        # 验证两个用户都存在（共享同一个数据库）
        with db1.get_session() as session:
            users = session.query(User).filter(
                User.wechat_openid.like(f'singleton_test_%_{timestamp}')
            ).all()
            assert len(users) == 2

    def test_database_independence_from_flask(self):
        """测试数据库独立于Flask的概念"""
        # 数据库可以在没有Flask的情况下初始化和使用
        db = initialize_for_test()

        # 验证数据库功能
        import time
        timestamp = str(int(time.time() * 1000))

        with db.get_session() as session:
            # 创建多个用户
            for i in range(3):
                user = User(
                    wechat_openid=f"independent_test_{timestamp}_{i}",
                    nickname=f"独立测试用户{i}",
                    role=1
                )
                session.add(user)
            session.commit()

            # 查询验证
            users = session.query(User).filter(
                User.wechat_openid.like(f'independent_test_{timestamp}_%')
            ).all()
            assert len(users) == 3

    def test_session_isolation_within_same_database(self):
        """测试同一数据库中的会话隔离"""
        db = initialize_for_test()

        # 使用时间戳确保唯一性
        import time
        timestamp = str(int(time.time() * 1000))

        # 在第一个会话中开始事务
        with db.get_session() as session1:
            user1 = User(
                wechat_openid=f"isolation_test_1_{timestamp}",
                nickname="隔离测试用户1",
                role=1
            )
            session1.add(user1)
            # 注意：这里不提交，测试隔离

            # 在第二个会话中查询
            with db.get_session() as session2:
                # 由于session1未提交，这里应该看不到user1
                found_user = session2.query(User).filter_by(
                    wechat_openid=f"isolation_test_1_{timestamp}"
                ).first()
                assert found_user is None

                # 在session2中添加另一个用户
                user2 = User(
                    wechat_openid=f"isolation_test_2_{timestamp}",
                    nickname="隔离测试用户2",
                    role=1
                )
                session2.add(user2)
                session2.commit()

            # 回到session1，现在提交
            session1.commit()

        # 在新会话中验证两个用户都存在
        with db.get_session() as session:
            users = session.query(User).filter(
                User.wechat_openid.like(f'isolation_test_%_{timestamp}')
            ).all()
            assert len(users) == 2

    def test_database_reset_and_reinitialize(self):
        """测试数据库重置和重新初始化"""
        # 初始化数据库并添加数据
        db1 = initialize_for_test()

        import time
        timestamp = str(int(time.time() * 1000))

        with db1.get_session() as session:
            user = User(
                wechat_openid=f"reset_test_{timestamp}",
                nickname="重置测试用户",
                role=1
            )
            session.add(user)
            session.commit()

        # 验证数据存在
        with db1.get_session() as session:
            users = session.query(User).all()
            assert len(users) >= 1

        # 重置数据库
        reset_all()

        # 重新初始化
        db2 = initialize_for_test()

        # 验证数据库为空
        with db2.get_session() as session:
            users = session.query(User).all()
            assert len(users) == 0

    def test_multiple_database_operations(self):
        """测试多个数据库操作的组合"""
        db = initialize_for_test()

        import time
        timestamp = str(int(time.time() * 1000))

        # 批量操作1：创建用户
        with db.get_session() as session:
            users = []
            for i in range(5):
                user = User(
                    wechat_openid=f"multi_op_{timestamp}_{i}",
                    nickname=f"多操作用户{i}",
                    role=1
                )
                session.add(user)
                users.append(user)
            session.commit()

        # 批量操作2：查询和更新
        with db.get_session() as session:
            # 查询所有用户
            all_users = session.query(User).filter(
                User.wechat_openid.like(f'multi_op_{timestamp}_%')
            ).all()
            assert len(all_users) == 5

            # 更新前3个用户的角色
            for i, user in enumerate(all_users[:3]):
                user.role = 2
            session.commit()

        # 批量操作3：验证更新
        with db.get_session() as session:
            role1_users = session.query(User).filter_by(role=1).filter(
                User.wechat_openid.like(f'multi_op_{timestamp}_%')
            ).all()
            role2_users = session.query(User).filter_by(role=2).filter(
                User.wechat_openid.like(f'multi_op_{timestamp}_%')
            ).all()

            assert len(role1_users) == 2
            assert len(role2_users) == 3