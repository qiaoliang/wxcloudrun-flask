"""
一键求助事件跟踪增强功能测试
"""
import pytest
import sys
import os
from datetime import datetime, timedelta

# 添加 src 目录到 Python 路径
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
sys.path.insert(0, src_path)

# 添加当前目录到路径以导入测试工具
sys.path.insert(0, os.path.dirname(__file__))

from database.flask_models import db, User, Community, CommunityEvent, EventMessage
from sqlalchemy import select
from integration.conftest import IntegrationTestBase


class TestEventModels(IntegrationTestBase):
    """事件模型测试"""

    def test_event_support_model_fields(self):
        """测试 EventMessage 模型字段"""
        with self.app.app_context():
            # 检查 EventMessage 模型是否有新增字段
            columns = [column.name for column in EventMessage.__table__.columns]
            
            assert 'message_type' in columns
            assert 'media_url' in columns
            assert 'media_duration' in columns
            assert 'message_tags' in columns

    def test_event_closure_fields_in_community_event(self):
        """测试 CommunityEvent 模型中的关闭字段"""
        with self.app.app_context():
            # 检查 CommunityEvent 模型中的关闭字段
            columns = [column.name for column in CommunityEvent.__table__.columns]
            
            assert 'closed_by' in columns
            assert 'closed_at' in columns
            assert 'closure_type' in columns
            assert 'closure_reason' in columns

    def test_event_message_to_dict(self):
        """测试 EventMessage to_dict 方法"""
        with self.app.app_context():
            # 使用测试数据生成器创建唯一数据
            from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
            
            phone_number = generate_unique_phone_number('test_event_message')
            open_id = generate_unique_openid(phone_number, 'test_event_message')
            nickname = generate_unique_nickname('test_event_message')
            
            # 创建测试数据
            community = Community(
                name=f'测试社区_{phone_number}',
                description='测试社区描述',
                creator_id=1,
                manager_id=1,
                status=1
            )
            db.session.add(community)
            db.session.flush()

            user = User(
                wechat_openid=open_id,
                phone_number=phone_number,
                phone_hash='test_hash_123',
                nickname=nickname,
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

    def test_event_closure_in_community_event_to_dict(self):
        """测试 CommunityEvent to_dict 方法中的关闭信息"""
        with self.app.app_context():
            # 使用测试数据生成器创建唯一数据
            from test_data_generator import generate_unique_phone_number, generate_unique_openid, generate_unique_nickname
            
            phone_number = generate_unique_phone_number('test_event_closure')
            open_id = generate_unique_openid(phone_number, 'test_event_closure')
            nickname = generate_unique_nickname('test_event_closure')
            
            # 创建测试数据
            community = Community(
                name=f'测试社区_{phone_number}',
                description='测试社区描述',
                creator_id=1,
                manager_id=1,
                status=1
            )
            db.session.add(community)
            db.session.flush()

            user = User(
                wechat_openid=open_id,
                phone_number=phone_number,
                phone_hash='test_hash_123',
                nickname=nickname,
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
                status=2,  # 已完成
                closed_by=user.user_id,
                closure_type=1,  # 用户关闭
                closure_reason='测试关闭原因'
            )
            db.session.add(event)
            db.session.commit()
            
            data = event.to_dict()
            
            assert data['closure_reason'] == '测试关闭原因'
            assert data['closure_type'] == 1
            assert data['closure_type_label'] == '用户关闭'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])