"""
一键求助事件跟踪增强功能测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 设置环境变量
os.environ['ENV_TYPE'] = 'unit'
os.environ['TOKEN_SECRET'] = 'test_secret_key_for_testing'

# 添加 src 目录到 Python 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from app import create_app
from database.flask_models import db, User, Community, CommunityEvent, EventMessage, EventClosure
from sqlalchemy import select


class TestEventModels:
    """事件模型测试"""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """设置测试应用"""
        app = create_app()
        app.config['TESTING'] = True
        
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    def test_event_support_model_fields(self, setup_app):
        """测试 EventMessage 模型字段"""
        with setup_app.app_context():
            # 检查 EventMessage 模型是否有新增字段
            columns = [column.name for column in EventMessage.__table__.columns]
            
            assert 'message_type' in columns
            assert 'media_url' in columns
            assert 'media_duration' in columns
            assert 'message_tags' in columns

    def test_event_closure_model_fields(self, setup_app):
        """测试 EventClosure 模型字段"""
        with setup_app.app_context():
            # 检查 EventClosure 模型字段
            columns = [column.name for column in EventClosure.__table__.columns]
            
            assert 'closure_id' in columns
            assert 'event_id' in columns
            assert 'closed_by' in columns
            assert 'closed_at' in columns
            assert 'closure_reason' in columns
            assert 'closure_status' in columns

    def test_event_message_to_dict(self, setup_app):
        """测试 EventMessage to_dict 方法"""
        with setup_app.app_context():
            # 创建测试数据
            community = Community(
                name='测试社区',
                description='测试社区描述',
                creator_id=1,
                manager_id=1,
                status=1
            )
            db.session.add(community)
            db.session.flush()

            user = User(
                wechat_openid='test_openid_123',
                phone_number='13900000001',
                phone_hash='test_hash_123',
                nickname='测试用户',
                role=1,
                status=1,
                community_id=community.community_id
            )
            db.session.add(user)
            db.session.flush()

            event = CommunityEvent(
                community_id=community.community_id,
                title='测试求助事件',
                description='测试求助事件描述',
                event_type='call_for_help',
                location='测试地点',
                target_user_id=user.user_id,
                created_by=user.user_id,
                status=1
            )
            db.session.add(event)
            db.session.flush()

            message = EventMessage(
                event_id=event.event_id,
                sender_id=user.user_id,
                message_content='测试内容',
                message_type='text',
                media_url='http://example.com/media.mp3',
                media_duration=30,
                message_tags=['标签1', '标签2']
            )
            db.session.add(message)
            db.session.commit()

            data = message.to_dict()

            assert data['message_type'] == 'text'
            assert data['media_url'] == 'http://example.com/media.mp3'
            assert data['media_duration'] == 30
            assert data['message_tags'] == ['标签1', '标签2']

    def test_event_closure_to_dict(self, setup_app):
        """测试 EventClosure to_dict 方法"""
        with setup_app.app_context():
            # 创建测试数据
            community = Community(
                name='测试社区',
                description='测试社区描述',
                creator_id=1,
                manager_id=1,
                status=1
            )
            db.session.add(community)
            db.session.flush()

            user = User(
                wechat_openid='test_openid_123',
                phone_number='13900000001',
                phone_hash='test_hash_123',
                nickname='测试用户',
                role=1,
                status=1,
                community_id=community.community_id
            )
            db.session.add(user)
            db.session.flush()

            event = CommunityEvent(
                community_id=community.community_id,
                title='测试求助事件',
                description='测试求助事件描述',
                event_type='call_for_help',
                location='测试地点',
                target_user_id=user.user_id,
                created_by=user.user_id,
                status=1
            )
            db.session.add(event)
            db.session.flush()

            closure = EventClosure(
                event_id=event.event_id,
                closed_by=user.user_id,
                closure_reason='测试关闭原因',
                closure_status='user_closed'
            )
            db.session.add(closure)
            db.session.commit()
            
            data = closure.to_dict()
            
            assert data['closure_reason'] == '测试关闭原因'
            assert data['closure_status'] == 'user_closed'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])