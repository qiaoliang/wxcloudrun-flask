"""
测试生产兼容的数据库初始化
验证与生产环境的一致性
"""
import pytest
import sys
import os

# 添加src路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from database import initialize_for_test, get_database
from database.models import User, Community, CommunityStaff, CommunityMember, CheckinRule, CheckinRecord
from datetime import datetime


class TestProductionCompatible:
    """测试生产兼容的数据库功能"""

    def test_production_like_data_creation(self, test_session):
        """测试创建生产环境相似的数据"""
        # 创建默认社区
        default_community = Community(
            name="安卡大家庭",
            description="默认社区",
            is_default=True,
            status=1
        )
        test_session.add(default_community)
        test_session.flush()
        
        # 创建超级管理员
        super_admin = User(
            wechat_openid="super_admin",
            nickname="超级管理员",
            role=4,  # 超级管理员
            status=1
        )
        test_session.add(super_admin)
        test_session.commit()
        
        # 验证创建成功
        assert default_community.community_id is not None
        assert default_community.name == "安卡大家庭"
        assert default_community.is_default is True
        
        assert super_admin.user_id is not None
        assert super_admin.nickname == "超级管理员"
        assert super_admin.role == 4

    def test_complete_user_lifecycle(self, test_session):
        """测试完整的用户生命周期"""
        # 1. 用户注册
        user = User(
            wechat_openid="lifecycle_test_user",
            nickname="生命周期测试用户",
            role=1,  # 普通用户
            status=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 2. 用户加入社区
        community = Community(
            name="生命周期测试社区",
            description="用于测试生命周期",
            creator_user_id=1,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        member = CommunityMember(
            community_id=community.community_id,
            user_id=user.user_id
        )
        test_session.add(member)
        test_session.flush()
        
        # 3. 用户创建打卡规则
        rule = CheckinRule(
            solo_user_id=user.user_id,
            rule_name="日常打卡",
            status=1
        )
        test_session.add(rule)
        test_session.flush()
        
        # 4. 用户打卡
        record = CheckinRecord(
            rule_id=rule.rule_id,
            solo_user_id=user.user_id,
            status=1,
            planned_time=datetime.now()
        )
        test_session.add(record)
        test_session.commit()
        
        # 验证所有数据创建成功
        assert user.user_id is not None
        assert community.community_id is not None
        assert member.id is not None
        assert rule.rule_id is not None
        assert record.record_id is not None

    def test_community_management_structure(self, test_session):
        """测试社区管理结构"""
        # 创建社区
        community = Community(
            name="管理结构测试社区",
            description="测试管理结构",
            creator_user_id=1,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建主管
        manager = User(
            wechat_openid="test_manager",
            nickname="测试主管",
            role=1
        )
        test_session.add(manager)
        test_session.flush()
        
        # 创建专员
        staff1 = User(
            wechat_openid="test_staff_1",
            nickname="测试专员1",
            role=1
        )
        staff2 = User(
            wechat_openid="test_staff_2",
            nickname="测试专员2",
            role=1
        )
        test_session.add_all([staff1, staff2])
        test_session.flush()
        
        # 分配角色
        manager_role = CommunityStaff(
            community_id=community.community_id,
            user_id=manager.user_id,
            role="manager"
        )
        staff_role1 = CommunityStaff(
            community_id=community.community_id,
            user_id=staff1.user_id,
            role="staff"
        )
        staff_role2 = CommunityStaff(
            community_id=community.community_id,
            user_id=staff2.user_id,
            role="staff"
        )
        test_session.add_all([manager_role, staff_role1, staff_role2])
        test_session.commit()
        
        # 验证管理结构
        staff_count = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id
        ).count()
        assert staff_count == 3
        
        # 验证角色分配
        manager_record = test_session.query(CommunityStaff).filter_by(
            community_id=community.community_id,
            user_id=manager.user_id
        ).first()
        assert manager_record.role == "manager"

    def test_database_constraints_enforcement(self, test_session):
        """测试数据库约束强制执行"""
        # 测试OpenID唯一约束
        user1 = User(
            wechat_openid="constraint_test_user",
            nickname="用户1",
            role=1
        )
        test_session.add(user1)
        test_session.commit()
        
        # 尝试创建相同OpenID的用户
        user2 = User(
            wechat_openid="constraint_test_user",  # 相同OpenID
            nickname="用户2",
            role=1
        )
        test_session.add(user2)
        
        # 应该抛出异常
        with pytest.raises(Exception) as exc_info:
            test_session.commit()
        
        error_message = str(exc_info.value).lower()
        assert "unique" in error_message or "constraint" in error_message
        test_session.rollback()

    def test_complex_query_operations(self, test_session):
        """测试复杂查询操作"""
        # 创建测试数据
        users = []
        for i in range(5):
            user = User(
                wechat_openid=f"query_test_user_{i}",
                nickname=f"查询测试用户{i}",
                role=1 if i < 3 else 2,  # 前3个是普通用户，后2个是监护人
                status=1
            )
            test_session.add(user)
            users.append(user)
        test_session.flush()
        
        # 创建社区和成员关系
        community = Community(
            name="查询测试社区",
            description="用于复杂查询测试",
            creator_user_id=1,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 添加前3个用户为社区成员
        for i in range(3):
            member = CommunityMember(
                community_id=community.community_id,
                user_id=users[i].user_id
            )
            test_session.add(member)
        test_session.commit()
        
        # 复杂查询1：查询社区中的普通用户
        regular_users_in_community = test_session.query(User).join(CommunityMember).filter(
            CommunityMember.community_id == community.community_id,
            User.role == 1
        ).all()
        assert len(regular_users_in_community) == 3
        
        # 复杂查询2：查询非社区成员的监护人
        guardian_non_members = test_session.query(User).filter(
            User.role == 2,
            ~User.user_id.in_(
                test_session.query(CommunityMember.user_id).filter(
                    CommunityMember.community_id == community.community_id
                )
            )
        ).all()
        assert len(guardian_non_members) == 2

    def test_data_integrity_across_relations(self, test_session):
        """测试关系间的数据完整性"""
        # 创建用户
        user = User(
            wechat_openid="integrity_test_user",
            nickname="完整性测试用户",
            role=1
        )
        test_session.add(user)
        test_session.flush()
        
        # 创建社区
        community = Community(
            name="完整性测试社区",
            description="测试数据完整性",
            creator_user_id=1,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        
        # 创建打卡规则
        rule = CheckinRule(
            solo_user_id=user.user_id,
            rule_name="完整性测试规则",
            status=1
        )
        test_session.add(rule)
        test_session.flush()
        
        # 创建打卡记录
        record = CheckinRecord(
            rule_id=rule.rule_id,
            solo_user_id=user.user_id,
            status=1,
            planned_time=datetime.now()
        )
        test_session.add(record)
        test_session.commit()
        
        # 验证关系完整性
        # 1. 记录必须关联到有效的规则
        found_record = test_session.query(CheckinRecord).filter_by(record_id=record.record_id).first()
        assert found_record is not None
        assert found_record.rule_id == rule.rule_id
        
        # 2. 规则必须关联到有效的用户
        found_rule = test_session.query(CheckinRule).filter_by(rule_id=rule.rule_id).first()
        assert found_rule is not None
        assert found_rule.solo_user_id == user.user_id
        
        # 3. 删除用户应该级联删除相关数据（取决于外键约束设置）
        # 注意：实际行为取决于外键约束的设置