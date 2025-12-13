"""
验证全新的无耦合数据库架构
测试三种使用模式：测试、独立、Flask
"""
import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database, reset_all
from database.models import User, Community


class TestNewArchitecture:
    """测试新的数据库架构"""

    def test_test_mode_initialization(self):
        """测试模式：单元测试和集成测试使用"""
        # 1. 初始化测试数据库
        reset_all()
        db = initialize_for_test()
        
        # 验证数据库已初始化
        assert db is not None
        assert hasattr(db, 'get_session')
        
        # 2. 使用数据库
        with db.get_session() as session:
            # 创建用户
            user = User(
                wechat_openid="test_user_1",
                nickname="测试用户1",
                role=1,
                status=1
            )
            session.add(user)
            session.flush()
            
            # 创建社区
            community = Community(
                name="测试社区",
                location="测试地址",
                status=1
            )
            session.add(community)
            session.commit()
            
            # 验证创建成功
            assert user.user_id is not None
            assert community.community_id is not None
            
        # 3. 验证数据存在
        with db.get_session() as session:
            users = session.query(User).all()
            assert len(users) >= 1
            assert users[0].nickname == "测试用户1"
            
            communities = session.query(Community).all()
            assert len(communities) >= 1
            assert communities[0].name == "测试社区"

    def test_database_singleton_behavior(self):
        """测试数据库单例行为"""
        # 获取数据库实例
        db1 = get_database()
        db2 = get_database()
        
        # 应该是同一个实例
        assert db1 is db2
        
        # 使用时间戳确保唯一性
        import time
        timestamp = str(int(time.time() * 1000))
        
        # 验证共享状态
        with db1.get_session() as session1:
            user = User(
                wechat_openid=f"singleton_test_{timestamp}",
                nickname="单例测试",
                role=1
            )
            session1.add(user)
            session1.commit()
        
        # 在另一个实例中应该能看到数据
        with db2.get_session() as session2:
            found_user = session2.query(User).filter_by(wechat_openid=f"singleton_test_{timestamp}").first()
            assert found_user is not None
            assert found_user.nickname == "单例测试"

    def test_session_isolation(self):
        """测试会话隔离"""
        db = initialize_for_test()
        
        # 在第一个会话中开始事务
        with db.get_session() as session1:
            user = User(
                wechat_openid="isolation_test",
                nickname="隔离测试",
                role=1
            )
            session1.add(user)
            # 不提交，测试隔离
            
            # 在第二个会话中查询
            with db.get_session() as session2:
                # 由于session1未提交，这里应该看不到user
                found_user = session2.query(User).filter_by(wechat_openid="isolation_test").first()
                assert found_user is None
            
            # 回到session1，提交
            session1.commit()
        
        # 在新会话中验证数据
        with db.get_session() as session:
            found_user = session.query(User).filter_by(wechat_openid="isolation_test").first()
            assert found_user is not None

    def test_database_reset_functionality(self):
        """测试数据库重置功能"""
        # 初始化并添加数据
        db = initialize_for_test()
        
        with db.get_session() as session:
            user = User(
                wechat_openid="reset_test",
                nickname="重置测试",
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

    def test_multiple_concurrent_sessions(self):
        """测试多个并发会话"""
        db = initialize_for_test()
        
        # 创建多个会话并操作
        sessions_data = []
        
        for i in range(3):
            with db.get_session() as session:
                user = User(
                    wechat_openid=f"concurrent_user_{i}",
                    nickname=f"并发用户{i}",
                    role=1
                )
                session.add(user)
                session.flush()
                sessions_data.append((user.user_id, f"并发用户{i}"))
        
        # 验证所有数据都存在
        with db.get_session() as session:
            for user_id, nickname in sessions_data:
                user = session.query(User).filter_by(user_id=user_id).first()
                assert user is not None
                assert user.nickname == nickname

    def test_error_handling_and_rollback(self):
        """测试错误处理和回滚"""
        db = initialize_for_test()
        
        # 使用时间戳确保唯一性
        import time
        timestamp = str(int(time.time() * 1000))
        
        # 先添加一个用户
        with db.get_session() as session:
            user1 = User(
                wechat_openid=f"error_test_{timestamp}",
                nickname="错误测试1",
                role=1
            )
            session.add(user1)
            session.commit()
        
        # 验证用户存在
        with db.get_session() as session:
            users = session.query(User).filter_by(wechat_openid=f"error_test_{timestamp}").all()
            assert len(users) == 1
        
        # 尝试添加重复的OpenID
        try:
            with db.get_session() as session:
                user2 = User(
                    wechat_openid=f"error_test_{timestamp}",  # 相同的OpenID
                    nickname="错误测试2",
                    role=1
                )
                session.add(user2)
                session.commit()
        except Exception:
            # 预期的错误
            pass
        
        # 验证仍然只有一个用户存在
        with db.get_session() as session:
            users = session.query(User).filter_by(wechat_openid=f"error_test_{timestamp}").all()
            assert len(users) == 1

    def test_complex_relationship_operations(self):
        """测试复杂的关系操作"""
        db = initialize_for_test()
        
        with db.get_session() as session:
            # 创建用户
            user = User(
                wechat_openid="complex_test_user",
                nickname="复杂测试用户",
                role=1
            )
            session.add(user)
            session.flush()
            
            # 创建社区
            community = Community(
                name="复杂测试社区",
                location="测试地址",
                creator_user_id=user.user_id
            )
            session.add(community)
            session.flush()
            
            # 创建用户和社区的关系
            from database.models import CommunityMember
            member = CommunityMember(
                community_id=community.community_id,
                user_id=user.user_id
            )
            session.add(member)
            session.commit()
            
            # 验证关系
            found_member = session.query(CommunityMember).filter_by(
                community_id=community.community_id,
                user_id=user.user_id
            ).first()
            assert found_member is not None
            
            # 验证反向查询
            user_with_communities = session.query(User).filter_by(
                wechat_openid="complex_test_user"
            ).first()
            # 注意：根据模型定义，可能需要手动加载关系