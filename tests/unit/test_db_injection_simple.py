"""
简化的数据库依赖注入测试
验证核心概念可行性
"""

import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database
from database.flask_models import User


class TestDatabaseInjectionSimple:
    """简化的数据库依赖注入测试"""

    def test_database_creation_before_flask(self):
        """测试数据库先创建，后注入Flask的概念"""
        # 1. 先创建数据库实例
        db = initialize_for_test()
        assert db is not None

        # 2. 验证数据库可以独立使用
        with db.get_session() as session:
            user = User(
                wechat_openid="test_simple",
                nickname="简化测试用户",
                role=1
            )
            session.add(user)
            session.commit()

            # 验证用户已保存
            saved_user = session.query(User).filter_by(wechat_openid="test_simple").first()
            assert saved_user is not None
            assert saved_user.nickname == "简化测试用户"

    def test_database_singleton_pattern(self):
        """测试数据库单例模式"""
        # 获取数据库实例
        db1 = get_database()
        db2 = get_database()

        # 应该返回同一个实例
        assert db1 is db2

    def test_session_context_manager(self):
        """测试会话上下文管理器"""
        db = initialize_for_test()

        # 测试自动提交和关闭
        with db.get_session() as session:
            user = User(
                wechat_openid="test_context",
                nickname="上下文测试用户",
                role=1
            )
            session.add(user)
            # 会话会在退出时自动提交

        # 验证数据已提交
        with db.get_session() as session:
            saved_user = session.query(User).filter_by(wechat_openid="test_context").first()
            assert saved_user is not None

    def test_multiple_operations_in_one_session(self):
        """测试一个会话中的多个操作"""
        db = initialize_for_test()

        with db.get_session() as session:
            # 创建多个用户
            users = []
            for i in range(3):
                user = User(
                    wechat_openid=f"test_multi_{i}",
                    nickname=f"多操作用户{i}",
                    role=1
                )
                session.add(user)
                users.append(user)

            # 在同一会话中查询
            all_users = session.query(User).filter(
                User.wechat_openid.like('test_multi_%')
            ).all()

            assert len(all_users) == 3

            # 在同一会话中更新
            users[0].nickname = "已更新的用户"
            session.commit()

            # 立即验证更新
            updated_user = session.query(User).filter_by(wechat_openid="test_multi_0").first()
            assert updated_user.nickname == "已更新的用户"

    def test_session_rollback(self):
        """测试会话回滚"""
        db = initialize_for_test()

        # 创建初始数据
        with db.get_session() as session:
            user = User(
                wechat_openid="test_rollback",
                nickname="回滚测试用户",
                role=1
            )
            session.add(user)
            session.commit()

        # 尝试添加数据但回滚
        try:
            with db.get_session() as session:
                # 添加新用户
                new_user = User(
                    wechat_openid="test_rollback_new",
                    nickname="新用户（将被回滚）",
                    role=1
                )
                session.add(new_user)

                # 模拟错误
                raise ValueError("模拟错误")
        except ValueError:
            # 异常被捕获，会话应该回滚
            pass

        # 验证新用户没有被保存
        with db.get_session() as session:
            original_user = session.query(User).filter_by(wechat_openid="test_rollback").first()
            assert original_user is not None

            new_user = session.query(User).filter_by(wechat_openid="test_rollback_new").first()
            assert new_user is None

    def test_database_configuration(self):
        """测试数据库配置"""
        db = initialize_for_test()

        # 验证数据库配置
        assert db.engine is not None

        # 检查是否是内存数据库
        db_url = str(db.engine.url)
        assert 'sqlite' in db_url or 'memory' in db_url