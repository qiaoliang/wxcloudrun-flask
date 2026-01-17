"""
测试创建社区时主管是否能访问社区
"""
import pytest
from database.flask_models import db, User, Community, CommunityStaff
from app.shared.constants.roles import Role
from flask import Flask


def test_manager_can_access_community_after_creation():
    """测试创建社区时主管是否能访问社区"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        
        # 创建超级管理员
        super_admin = User(
            nickname='超级管理员',
            phone_number='13800000001',
            role=Role.SUPER_ADMIN
        )
        db.session.add(super_admin)
        db.session.flush()
        
        # 创建主管用户
        manager_user = User(
            nickname='主管用户',
            phone_number='13800000002',
            role=Role.SOLO  # 初始角色为普通用户
        )
        db.session.add(manager_user)
        db.session.flush()
        
        # 创建社区并指定主管
        community = CommunityService.create_community(
            name='测试社区',
            description='测试社区描述',
            creator_id=super_admin.user_id,
            manager_id=manager_user.user_id
        )
        db.session.flush()
        
        # 模拟 API 中的操作：将主管添加到 CommunityStaff 表
        CommunityStaffService.add_staff_single(
            community_id=community.community_id,
            user_id=manager_user.user_id,
            role='manager',
            operator_id=super_admin.user_id
        )
        
        # 验证主管是否在 CommunityStaff 表中
        staff_record = db.session.query(CommunityStaff).filter(
            CommunityStaff.community_id == community.community_id,
            CommunityStaff.user_id == manager_user.user_id,
            CommunityStaff.removed_at.is_(None)
        ).first()
        
        assert staff_record is not None, "主管应该在 CommunityStaff 表中"
        assert staff_record.role == 'manager', "主管角色应该是 manager"
        
        # 验证主管的角色是否被更新
        db.session.refresh(manager_user)
        assert manager_user.role == Role.MANAGER, "主管用户的角色应该被更新为 MANAGER"
        
        # 验证 _get_user_community_ids 能找到主管的社区
        community_ids = CommunityService._get_user_community_ids(manager_user)
        assert community_ids is not None, "主管应该有社区权限"
        assert community.community_id in community_ids, "主管应该能访问创建的社区"
        
        # 验证 get_manageable_communities 能返回主管的社区
        communities, total = CommunityService.get_manageable_communities(manager_user)
        assert len(communities) > 0, "主管应该能管理至少一个社区"
        assert communities[0].community_id == community.community_id, "主管应该能管理创建的社区"
        
        print("✅ 测试通过：主管可以访问创建的社区")


if __name__ == '__main__':
    test_manager_can_access_community_after_creation()
