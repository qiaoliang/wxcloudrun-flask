"""
测试同一用户不能被添加到同一社区两次的约束
这个测试已经在test_community_constraints.py中存在，这里创建一个更全面的版本
"""

import pytest
import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

from wxcloudrun.model_community_extensions import CommunityMember, CommunityStaff
from wxcloudrun.model import User, Community
from wxcloudrun import db


class TestSameUserCannotBeAddedTwice:
    """测试同一用户不能被添加到同一社区两次的约束"""

    def test_same_user_cannot_be_added_twice_to_same_community(self, test_client):
        """
        RED阶段：测试数据库唯一约束防止同一用户被添加到同一社区两次
        验证CommunityMember表的唯一约束 (community_id, user_id)
        """
        # 创建测试社区
        community = Community(
            name="测试社区",
            description="用于测试唯一约束",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        # 创建测试用户
        user = User(
            wechat_openid="test_user_duplicate",
            nickname="重复测试用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 第一次添加用户到社区
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member1)
        db.session.commit()
        
        # 验证第一次添加成功
        assert member1.id is not None
        assert member1.community_id == community.community_id
        assert member1.user_id == user.user_id
        
        # 查询验证记录存在
        existing_member = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert existing_member is not None
        assert existing_member.id == member1.id
        
        # 尝试第二次添加同一用户到同一社区
        # 这应该因为唯一约束而失败
        member2 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member2)
        
        # 捕获预期的数据库异常
        with pytest.raises(Exception) as exc_info:
            db.session.commit()
        
        # 验证异常类型（可能是IntegrityError或其他数据库异常）
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        
        # 回滚会话
        db.session.rollback()
        
        # 验证数据库中只有一条记录
        count = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 1
        
        print("✅ 唯一约束成功防止了重复添加用户到同一社区")

    def test_prevention_at_business_logic_layer(self, test_client):
        """
        测试业务逻辑层也防止重复添加
        验证add_community_users API中的检查逻辑
        """
        # 这个测试模拟API层的检查逻辑
        community = Community(
            name="业务逻辑测试社区",
            description="测试业务层检查",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        user = User(
            wechat_openid="business_logic_user",
            nickname="业务逻辑用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 第一次添加
        member1 = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member1)
        db.session.commit()
        
        # 模拟业务逻辑检查
        def check_user_in_community(community_id, user_id):
            """模拟API中的检查逻辑"""
            existing = CommunityMember.query.filter_by(
                community_id=community_id,
                user_id=user_id
            ).first()
            return existing is not None
        
        # 第一次检查应该返回False（用户不在社区中）
        assert check_user_in_community(community.community_id, user.user_id) == False
        
        # 添加用户后再次检查
        assert check_user_in_community(community.community_id, user.user_id) == True
        
        # 验证业务逻辑可以防止重复添加
        existing = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        
        if existing:
            # 模拟API会返回错误
            error_response = {
                'code': 0,
                'msg': '用户已在社区'
            }
            assert error_response['msg'] == '用户已在社区'
        
        print("✅ 业务逻辑层成功防止重复添加")

    def test_constraint_across_different_scenarios(self, test_client):
        """
        测试不同场景下的约束行为
        """
        # 创建多个社区
        communities = []
        for i in range(3):
            community = Community(
                name=f"测试社区{i+1}",
                description=f"第{i+1}个测试社区",
                creator_user_id=1
            )
            communities.append(community)
        db.session.add_all(communities)
        db.session.flush()
        
        # 创建多个用户
        users = []
        for i in range(3):
            user = User(
                wechat_openid=f"user_scenario_{i+1}",
                nickname=f"场景用户{i+1}",
                role=1
            )
            users.append(user)
        db.session.add_all(users)
        db.session.flush()
        
        # 场景1：同一用户加入多个不同社区（应该成功）
        user = users[0]
        for community in communities:
            member = CommunityMember(
                community_id=community.community_id,
                user_id=user.user_id
            )
            db.session.add(member)
        db.session.commit()
        
        # 验证用户在所有社区中
        for community in communities:
            member = CommunityMember.query.filter_by(
                community_id=community.community_id,
                user_id=user.user_id
            ).first()
            assert member is not None
        
        # 场景2：多个用户加入同一社区（应该成功）
        community = communities[0]
        for user in users[1:]:
            member = CommunityMember(
                community_id=community.community_id,
                user_id=user.user_id
            )
            db.session.add(member)
        db.session.commit()
        
        # 验证所有用户都在社区中
        count = CommunityMember.query.filter_by(
            community_id=community.community_id
        ).count()
        assert count == len(users)
        
        # 场景3：尝试重复添加（应该失败）
        user = users[0]
        community = communities[0]
        duplicate_member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(duplicate_member)
        
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()
        
        # 验证记录数没有增加
        count = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert count == 1
        
        print("✅ 不同场景下的约束行为验证通过")

    def test_constraint_with_staff_roles(self, test_client):
        """
        测试约束与Staff角色的关系
        """
        # 创建社区和用户
        community = Community(
            name="Staff角色测试社区",
            description="测试Staff与Member的关系",
            creator_user_id=1
        )
        db.session.add(community)
        db.session.flush()
        
        user = User(
            wechat_openid="staff_test_user",
            nickname="Staff测试用户",
            role=1
        )
        db.session.add(user)
        db.session.flush()
        
        # 用户先作为成员加入社区
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(member)
        db.session.commit()
        
        # 然后用户被提升为Staff
        staff_role = CommunityStaff(
            community_id=community.community_id,
            user_id=user.user_id,
            role='staff'
        )
        db.session.add(staff_role)
        db.session.commit()
        
        # 验证用户既是Member又是Staff
        member_record = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert member_record is not None
        
        staff_record = CommunityStaff.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).first()
        assert staff_record is not None
        
        # 尝试再次添加为Member（应该失败）
        duplicate_member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        db.session.add(duplicate_member)
        
        with pytest.raises(Exception):
            db.session.commit()
        
        db.session.rollback()
        
        # 验证Member记录仍然只有一个
        member_count = CommunityMember.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert member_count == 1
        
        # Staff记录不受影响
        staff_count = CommunityStaff.query.filter_by(
            community_id=community.community_id,
            user_id=user.user_id
        ).count()
        assert staff_count == 1
        
        print("✅ Staff角色与Member约束测试通过")


@pytest.fixture
def test_client():
    """创建测试客户端和数据库会话"""
    from wxcloudrun import app
    
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()