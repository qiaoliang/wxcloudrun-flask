"""
用户批量转移服务单元测试
"""
import pytest
import sys
import os
from datetime import datetime, time
from sqlalchemy import select

# 确保src目录在Python路径中
src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
sys.path.insert(0, src_path)

from database.flask_models import db, User, Community, CommunityStaff, CommunityEvent, CommunityCheckinRule, UserCommunityRule
from app.application.use_cases.community.transfer_users_batch_use_case import TransferUsersBatchUseCase
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER
from test_constants import TEST_CONSTANTS
from test_data_generator import (
    generate_unique_phone_number,
    generate_unique_openid,
    generate_unique_nickname
)
from hashlib import sha256


def create_test_user_with_session(session, role=Role.SOLO, nickname=None, community_id=None, test_context="test_user"):
    """创建测试用户"""
    phone_number = generate_unique_phone_number(test_context)
    openid = generate_unique_openid(phone_number, test_context)
    user = User(
        wechat_openid=openid,
        nickname=nickname or generate_unique_nickname(test_context),
        phone_number=phone_number,
        phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest(),
        role=role,
        status=1,
        community_id=community_id,
        avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number)
    )
    session.add(user)
    session.commit()
    return user


def create_test_community_with_session(session, name=None):
    """创建测试社区"""
    community = Community(
        name=name or f"测试社区_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        description="测试社区",
        status=1
    )
    session.add(community)
    session.commit()
    return community


def add_staff_to_community(session, user_id, community_id, role='manager'):
    """将用户添加为社区工作人员"""
    staff = CommunityStaff(
        community_id=community_id,
        user_id=user_id,
        role=role
    )
    session.add(staff)
    session.commit()
    return staff


@pytest.fixture
def transfer_setup(test_session, test_app):
    """设置测试环境"""
    test_context = f"transfer_setup_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

    # 创建超级管理员
    admin = create_test_user_with_session(
        test_session,
        role=Role.SUPER_ADMIN,
        nickname='管理员',
        test_context=f'{test_context}_admin'
    )

    # 创建两个社区
    source_community = create_test_community_with_session(
        test_session,
        name=f'{test_context}_源社区'
    )
    target_community = create_test_community_with_session(
        test_session,
        name=f'{test_context}_目标社区'
    )

    # 设置管理员为两个社区的主管
    add_staff_to_community(test_session, admin.user_id, source_community.community_id, role='manager')
    add_staff_to_community(test_session, admin.user_id, target_community.community_id, role='manager')

    # 在源社区创建10个普通用户
    users = []
    for i in range(10):
        user = create_test_user_with_session(
            test_session,
            role=Role.SOLO,
            nickname=f'用户{i}',
            community_id=source_community.community_id,
            test_context=f'user_{i}'
        )
        users.append(user)

    # 为源社区创建打卡规则
    rule1 = CommunityCheckinRule(
        community_id=source_community.community_id,
        rule_name='源社区规则1',
        custom_time=time(8, 0, 0),
        status=1,
        created_by=admin.user_id
    )
    test_session.add(rule1)

    # 为目标社区创建打卡规则
    rule2 = CommunityCheckinRule(
        community_id=target_community.community_id,
        rule_name='目标社区规则1',
        custom_time=time(9, 0, 0),
        status=1,
        created_by=admin.user_id
    )
    test_session.add(rule2)

    test_session.commit()

    return {
        'admin': admin,
        'source_community': source_community,
        'target_community': target_community,
        'users': users,
        'source_rule': rule1,
        'target_rule': rule2
    }


class TestUserTransferService:
    """测试 UserTransferService 类"""

    def test_transfer_single_user(self, transfer_setup, test_session, test_app):
        """测试成功转移单个用户"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 执行转移
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, [users[0].user_id]
            )

            # 验证结果
            assert result.is_success
            assert result.data['success_count'] == 1
            assert result.data['skipped_count'] == 0
            assert len(result.data['failed']) == 0
            assert len(result.data['transferred_users']) == 1

            # 验证用户社区归属
            user = test_session.get(User, users[0].user_id)
            assert user.community_id == target_community.community_id
            assert user.community_joined_at is not None

    def test_transfer_multiple_users(self, transfer_setup, test_session, test_app):
        """测试成功转移多个用户（10个）"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            user_ids = [u.user_id for u in users]

            # 执行转移
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, user_ids
            )

            # 验证结果
            assert result.data['success_count'] == 10
            assert result.data['skipped_count'] == 0
            assert len(result.data['failed']) == 0
            assert len(result.data['transferred_users']) == 10

            # 验证所有用户社区归属
            for user in users:
                user = test_session.get(User, user.user_id)
                assert user.community_id == target_community.community_id

    def test_transfer_exceeds_limit(self, transfer_setup, test_session, test_app):
        """测试超过10个用户限制"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 创建额外的用户
            extra_user = create_test_user_with_session(
                test_session,
                role=Role.SOLO,
                community_id=source_community.community_id,
                test_context='extra_user'
            )
            user_ids = [u.user_id for u in users] + [extra_user.user_id]

            # 执行转移（应该返回验证错误）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, user_ids
            )

            assert result.is_failure
            assert result.status.value == 'validation_error'
            assert '一次最多转移10个用户' in result.message

    def test_transfer_non_manager_user(self, transfer_setup, test_session, test_app):
        """测试非主管用户尝试转移"""
        setup = transfer_setup
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 创建一个普通用户作为操作者
            normal_user = create_test_user_with_session(
                test_session,
                role=Role.SOLO,
                nickname='普通用户',
                test_context='normal_user'
            )

            # 执行转移（应该返回权限错误）
            result = TransferUsersBatchUseCase().execute(
                normal_user.user_id, source_community.community_id, target_community.community_id, [users[0].user_id]
            )

            assert result.is_failure
            assert result.status.value == 'forbidden'
            assert '权限不足' in result.message

    def test_transfer_staff_user(self, transfer_setup, test_session, test_app):
        """测试尝试转移工作人员用户（混合成功和失败）"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 创建一个工作人员用户
            staff_user = create_test_user_with_session(
                test_session,
                role=Role.STAFF,
                nickname='工作人员',
                community_id=source_community.community_id,
                test_context='staff_user'
            )

            # 执行转移（包含普通用户和工作人员用户）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id,
                [users[0].user_id, staff_user.user_id]
            )

            # 验证结果
            assert result.data['success_count'] == 1
            assert len(result.data['failed']) == 1
            assert '只能转移普通用户' in result.data['failed'][0]['reason']

    def test_transfer_user_not_in_source_community(self, transfer_setup, test_session, test_app):
        """测试用户已离开源社区"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 将第一个用户移出源社区
            users[0].community_id = target_community.community_id
            test_session.commit()

            # 执行转移
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, [users[0].user_id]
            )

            # 验证结果
            assert result.data['success_count'] == 0
            assert result.data['skipped_count'] == 1
            assert len(result.data['failed']) == 0

    def test_transfer_with_pending_events(self, transfer_setup, test_session, test_app):
        """测试转移未完成事件"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 创建未完成事件
            event = CommunityEvent(
                community_id=source_community.community_id,
                title='未完成事件',
                target_user_id=users[0].user_id,
                created_by=admin.user_id,
                event_type='call_for_help',
                status=1  # 进行中
            )
            test_session.add(event)

            # 创建已完成事件
            completed_event = CommunityEvent(
                community_id=source_community.community_id,
                title='已完成事件',
                target_user_id=users[1].user_id,
                created_by=admin.user_id,
                event_type='call_for_help',
                status=2  # 已完成
            )
            test_session.add(completed_event)

            test_session.commit()

            # 执行转移
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, [users[0].user_id, users[1].user_id]
            )

            # 验证事件转移
            assert result.data['events_transferred'] == 1

            # 验证未完成事件已转移
            event = test_session.get(CommunityEvent, event.event_id)
            assert event.community_id == target_community.community_id

            # 验证已完成事件保留在源社区
            completed_event = test_session.get(CommunityEvent, completed_event.event_id)
            assert completed_event.community_id == source_community.community_id

    def test_transfer_same_source_and_target(self, transfer_setup, test_app):
        """测试源社区和目标社区相同"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        users = setup['users']

        with test_app.app_context():
            # 执行转移（应该返回验证错误）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, source_community.community_id, [users[0].user_id]
            )

            assert result.is_failure
            assert '源社区和目标社区不能相同' in result.message

    def test_transfer_duplicate_user_ids(self, transfer_setup, test_session, test_app):
        """测试重复的用户ID"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 执行转移（包含重复的用户ID）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, [users[0].user_id, users[0].user_id]
            )

            # 验证结果（应该只转移一次）
            assert result.data['success_count'] == 1
            assert len(result.data['transferred_users']) == 1

    def test_transfer_invalid_user_id_format(self, test_app):
        """测试无效的用户ID格式"""
        with test_app.app_context():
            # 执行转移（应该返回验证错误）
            result = TransferUsersBatchUseCase().execute(
                1, 1, 2, [0, -1, 'invalid']
            )

            assert result.is_failure
            assert '无效的用户ID' in result.message

    def test_transfer_empty_user_ids(self, test_app):
        """测试空的用户ID列表"""
        with test_app.app_context():
            # 执行转移（应该返回验证错误）
            result = TransferUsersBatchUseCase().execute(
                1, 1, 2, []
            )

            assert result.is_failure
            assert '用户ID列表不能为空' in result.message

    def test_transfer_nonexistent_user(self, transfer_setup, test_session, test_app):
        """测试包含不存在用户的转移（混合成功和失败）"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 执行转移（包含一个存在的用户和一个不存在的用户）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id,
                [users[0].user_id, 999999]
            )

            # 验证结果（部分成功）
            assert result.data['success_count'] == 1
            assert len(result.data['failed']) == 1
            assert '用户不存在' in result.data['failed'][0]['reason']

    def test_transfer_all_users_failed(self, transfer_setup, test_session, test_app):
        """测试所有用户转移失败"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']

        with test_app.app_context():
            # 创建工作人员用户
            staff_user = create_test_user_with_session(
                test_session,
                role=Role.STAFF,
                nickname='工作人员',
                community_id=source_community.community_id,
                test_context='staff_user'
            )

            # 执行转移（应该返回失败）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id, [staff_user.user_id, 999999]
            )

            assert result.is_failure
            assert '所有用户转移失败' in result.message

    def test_transfer_partial_success(self, transfer_setup, test_session, test_app):
        """测试部分成功转移"""
        setup = transfer_setup
        admin = setup['admin']
        source_community = setup['source_community']
        target_community = setup['target_community']
        users = setup['users']

        with test_app.app_context():
            # 创建工作人员用户
            staff_user = create_test_user_with_session(
                test_session,
                role=Role.STAFF,
                nickname='工作人员',
                community_id=source_community.community_id,
                test_context='staff_user'
            )

            # 执行转移（包含成功和失败的用户）
            result = TransferUsersBatchUseCase().execute(
                admin.user_id, source_community.community_id, target_community.community_id,
                [users[0].user_id, staff_user.user_id]
            )

            # 验证结果
            assert result.data['success_count'] == 1
            assert len(result.data['failed']) == 1
            assert '只能转移普通用户' in result.data['failed'][0]['reason']