"""
测试 get_sent_invitations 返回正确的数据结构

验证返回的邀请列表包含正确的字段：
- invitee_info (被邀请人信息)
- rule_info (规则信息)
"""
import pytest
from datetime import datetime
from app.application.use_cases.supervision.invitation_management_use_case import InvitationManagementUseCase
from app.domain.repositories.supervision_relation_repository import SupervisionRelationRepository
from database.flask_models import SupervisionRuleRelation, User, CheckinRule, Community


class TestSentInvitationsResponseStructure:
    """测试发起的邀请列表返回的数据结构"""

    def test_sent_invitations_contains_correct_fields(self, test_session):
        """测试返回的邀请包含正确的字段名"""
        # 1. 准备测试数据
        # 创建用户
        solo_user = User(
            phone_number='13800000001',
            phone_hash='hash1',
            nickname='被监督人张三',
            avatar_url='http://example.com/avatar1.jpg',
            role=0  # 普通用户
        )
        test_session.add(solo_user)
        test_session.flush()

        supervisor_user = User(
            phone_number='13800000002',
            phone_hash='hash2',
            nickname='监督人李四',
            avatar_url='http://example.com/avatar2.jpg',
            role=0  # 普通用户
        )
        test_session.add(supervisor_user)
        test_session.flush()

        # 创建规则
        from datetime import time
        rule = CheckinRule(
            user_id=solo_user.user_id,
            rule_name='晨间打卡规则',
            custom_time=time(7, 0),  # 07:00
            frequency_type=0  # 每天
        )
        test_session.add(rule)
        test_session.flush()

        # 创建监督关系
        relation = SupervisionRuleRelation(
            solo_user_id=solo_user.user_id,
            supervisor_user_id=supervisor_user.user_id,
            rule_id=rule.rule_id,
            status=1,
            invitation_type='internal',
            message='请监督我打卡'
        )
        test_session.add(relation)
        test_session.commit()

        # 2. 执行查询
        use_case = InvitationManagementUseCase()
        result = use_case.get_sent_invitations(
            user_id=solo_user.user_id,
            page=1,
            limit=10
        )

        # 3. 验证结果
        assert result.is_success, f"查询失败: {result.message}"
        assert 'invitations' in result.data
        invitations = result.data['invitations']
        assert len(invitations) == 1, f"期望1个邀请，实际得到{len(invitations)}个"

        # 4. 验证数据结构 - 必须包含正确的字段
        invitation = invitations[0]

        # 关键验证：必须包含 invitee_info 和 rule_info
        assert 'invitee_info' in invitation, "缺少 invitee_info 字段"
        assert 'rule_info' in invitation, "缺少 rule_info 字段"

        # 验证被邀请人信息
        invitee_info = invitation['invitee_info']
        assert invitee_info['nickname'] == '监督人李四', \
            f"被邀请人昵称错误: {invitee_info.get('nickname')}"
        assert invitee_info['avatar_url'] == 'http://example.com/avatar2.jpg', \
            f"被邀请人头像错误: {invitee_info.get('avatar_url')}"

        # 验证规则信息
        rule_info = invitation['rule_info']
        assert rule_info['rule_name'] == '晨间打卡规则', \
            f"规则名称错误: {rule_info.get('rule_name')}"
        assert rule_info['rule_id'] == rule.rule_id

        print("✅ 测试通过：返回的数据结构包含正确的字段")

    def test_sent_invitations_missing_user_or_rule(self, test_session):
        """测试当用户或规则不存在时的处理"""
        # 创建用户但不创建规则和关系
        solo_user = User(
            phone_number='13800000003',
            phone_hash='hash3',
            nickname='测试用户',
            role=0  # 普通用户
        )
        test_session.add(solo_user)
        test_session.commit()

        use_case = InvitationManagementUseCase()
        result = use_case.get_sent_invitations(
            user_id=solo_user.user_id,
            page=1,
            limit=10
        )

        # 应该返回空列表而不是错误
        assert result.is_success
        assert result.data['invitations'] == []
        print("✅ 测试通过：无邀请时返回空列表")
