"""
社区工作人员UseCase单元测试
"""
import pytest
from datetime import datetime
from sqlalchemy import select
from app.application.use_cases.community.get_community_staff_list_use_case import GetCommunityStaffListUseCase
from app.application.use_cases.community.add_community_staff_use_case import AddCommunityStaffUseCase
from app.application.use_cases.community.remove_community_staff_use_case import RemoveCommunityStaffUseCase
from app.application.use_cases.base import UseCaseStatus
from database.flask_models import db, User, Community, CommunityStaff
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from tests.test_data_generator import generate_unique_phone_number, generate_unique_nickname


class TestGetCommunityStaffListUseCase:
    """GetCommunityStaffListUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCommunityStaffListUseCase()

    @pytest.fixture
    def test_community(self, test_session):
        """创建测试社区"""
        community = Community(
            name="测试社区",
            manager_id=None,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        return community

    @pytest.fixture
    def test_staff_users(self, test_session, test_community):
        """创建测试工作人员用户"""
        users = []
        for i in range(3):
            user = User(
                phone_number=generate_unique_phone_number(f"test_staff_{i}"),
                nickname=generate_unique_nickname(f"test_staff_{i}"),
                wechat_openid=f"openid_{i}",
                community_id=test_community.community_id,
                role=Role.STAFF
            )
            test_session.add(user)
            test_session.flush()
            users.append(user)

            # 创建工作人员记录
            staff = CommunityStaff(
                community_id=test_community.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_STAFF if i < 2 else STAFF_ROLE_MANAGER,
                added_at=datetime.now()
            )
            test_session.add(staff)
            test_session.flush()

        return users

    def test_get_staff_list_success(self, use_case, test_community, test_staff_users):
        """
        测试获取工作人员列表成功
        Given: 社区有工作人员
        When: 调用 execute 方法
        Then: 返回工作人员列表
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            role='all',
            page=1,
            limit=10
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '获取工作人员列表成功'
        assert len(result.data['staff']) == 3
        assert result.data['pagination']['total'] == 3

    def test_get_staff_list_with_role_filter(self, use_case, test_community, test_staff_users):
        """
        测试按角色筛选工作人员
        Given: 社区有主管和专员
        When: 按角色筛选
        Then: 返回对应角色的工作人员
        """
        # Act - 只获取专员
        result = use_case.execute(
            community_id=test_community.community_id,
            role='staff',
            page=1,
            limit=10
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['staff']) == 2  # 2个专员
        for staff in result.data['staff']:
            assert staff['role'] == STAFF_ROLE_STAFF

        # Act - 只获取主管
        result = use_case.execute(
            community_id=test_community.community_id,
            role='manager',
            page=1,
            limit=10
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['staff']) == 1  # 1个主管
        assert result.data['staff'][0]['role'] == STAFF_ROLE_MANAGER

    def test_get_staff_list_pagination(self, use_case, test_community, test_staff_users):
        """
        测试分页功能
        Given: 社区有3个工作人员
        When: 每页显示2个
        Then: 正确返回分页信息
        """
        # Act - 第一页
        result = use_case.execute(
            community_id=test_community.community_id,
            page=1,
            limit=2
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['staff']) == 2
        assert result.data['pagination']['page'] == 1
        assert result.data['pagination']['limit'] == 2
        assert result.data['pagination']['total'] == 3
        assert result.data['pagination']['total_pages'] == 2
        assert result.data['pagination']['has_more'] is True

        # Act - 第二页
        result = use_case.execute(
            community_id=test_community.community_id,
            page=2,
            limit=2
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['staff']) == 1
        assert result.data['pagination']['has_more'] is False

    def test_get_staff_list_empty_community(self, use_case, test_community):
        """
        测试获取空社区的工作人员列表
        Given: 社区没有工作人员
        When: 调用 execute 方法
        Then: 返回空列表
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            page=1,
            limit=10
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['staff']) == 0
        assert result.data['pagination']['total'] == 0

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 没有提供社区ID
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(community_id=None)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '缺少社区ID' in result.message

    def test_validate_invalid_role(self, use_case, test_community):
        """
        测试验证失败 - 无效的角色参数
        Given: 提供了无效的角色参数
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            role='invalid_role'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '无效的角色参数' in result.message

    def test_validate_invalid_page(self, use_case, test_community):
        """
        测试验证失败 - 无效的页码
        Given: 提供了无效的页码
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            page=0
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '页码必须大于0' in result.message

    def test_validate_invalid_limit(self, use_case, test_community):
        """
        测试验证失败 - 无效的每页数量
        Given: 提供了无效的每页数量
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            limit=101
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '每页数量必须在1-100之间' in result.message


class TestAddCommunityStaffUseCase:
    """AddCommunityStaffUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return AddCommunityStaffUseCase()

    @pytest.fixture
    def test_community(self, test_session):
        """创建测试社区"""
        community = Community(
            name="测试社区",
            manager_id=None,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        return community

    @pytest.fixture
    def test_manager(self, test_session, test_community):
        """创建测试主管用户"""
        user = User(
            phone_number=generate_unique_phone_number("test_manager"),
            nickname=generate_unique_nickname("test_manager"),
            wechat_openid="openid_manager",
            community_id=test_community.community_id,
            role=Role.MANAGER
        )
        test_session.add(user)
        test_session.flush()

        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=user.user_id,
            role=STAFF_ROLE_MANAGER,
            added_at=datetime.now()
        )
        test_session.add(staff)
        test_session.flush()

        return user

    @pytest.fixture
    def test_users(self, test_session):
        """创建测试用户"""
        users = []
        for i in range(3):
            user = User(
                phone_number=generate_unique_phone_number(f"test_user_{i}"),
                nickname=generate_unique_nickname(f"test_user_{i}"),
                wechat_openid=f"openid_{i}",
                role=Role.SOLO
            )
            test_session.add(user)
            test_session.flush()
            users.append(user)
        return users

    def test_add_staff_success(self, use_case, test_session, test_community, test_manager, test_users):
        """
        测试添加工作人员成功
        Given: 主管用户和普通用户
        When: 主管添加普通用户为专员
        Then: 成功添加工作人员
        """
        # Act
        result = use_case.execute(
            operator_user_id=test_manager.user_id,
            community_id=test_community.community_id,
            user_ids=[test_users[0].user_id],
            role='staff'
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['success_count'] == 1
        assert len(result.data['added_users']) == 1

        # 验证数据库中的记录
        stmt = select(CommunityStaff).where(
            CommunityStaff.user_id == test_users[0].user_id,
            CommunityStaff.community_id == test_community.community_id
        )
        staff = test_session.execute(stmt).scalar_one_or_none()
        assert staff is not None
        assert staff.role == STAFF_ROLE_STAFF

    def test_add_staff_batch(self, use_case, test_community, test_manager, test_users):
        """
        测试批量添加工作人员
        Given: 主管用户和多个普通用户
        When: 主管批量添加用户为专员
        Then: 成功添加多个工作人员
        """
        # Act
        result = use_case.execute(
            operator_user_id=test_manager.user_id,
            community_id=test_community.community_id,
            user_ids=[u.user_id for u in test_users],
            role='staff'
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['success_count'] == 3

    def test_add_manager_success(self, use_case, test_session, test_community, test_users):
        """
        测试添加主管成功
        Given: 社区没有主管，普通用户
        When: 超级管理员添加普通用户为主管
        Then: 成功添加主管并更新社区manager_id
        """
        # 创建一个超级管理员用户
        super_admin = User(
            phone_number=generate_unique_phone_number("test_super_admin"),
            nickname=generate_unique_nickname("test_super_admin"),
            wechat_openid="openid_super_admin",
            role=Role.SUPER_ADMIN
        )
        test_session.add(super_admin)
        test_session.flush()

        # Act
        result = use_case.execute(
            operator_user_id=super_admin.user_id,
            community_id=test_community.community_id,
            user_ids=[test_users[0].user_id],
            role='manager'
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['success_count'] == 1

        # 验证社区的manager_id已更新
        community = test_session.get(Community, test_community.community_id)
        assert community.manager_id == test_users[0].user_id

    def test_add_manager_only_one(self, use_case, test_community, test_manager, test_users):
        """
        测试只能添加一个主管
        Given: 主管用户和多个普通用户
        When: 尝试批量添加多个主管
        Then: 返回验证错误
        """
        # Act
        result = use_case.execute(
            operator_user_id=test_manager.user_id,
            community_id=test_community.community_id,
            user_ids=[u.user_id for u in test_users[:2]],
            role='manager'
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '主管只能添加一个' in result.message

    def test_add_staff_permission_denied(self, use_case, test_community, test_users):
        """
        测试权限不足
        Given: 普通用户
        When: 尝试添加工作人员
        Then: 返回 FORBIDDEN 状态
        """
        # Act
        result = use_case.execute(
            operator_user_id=test_users[0].user_id,
            community_id=test_community.community_id,
            user_ids=[test_users[1].user_id],
            role='staff'
        )

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert '权限不足' in result.message

    def test_add_staff_duplicate(self, use_case, test_community, test_manager, test_users):
        """
        测试添加已存在的工作人员
        Given: 用户已经是工作人员
        When: 再次添加相同角色
        Then: 静默跳过（不报错）
        """
        # 先添加一次
        use_case.execute(
            operator_user_id=test_manager.user_id,
            community_id=test_community.community_id,
            user_ids=[test_users[0].user_id],
            role='staff'
        )

        # 再次添加
        result = use_case.execute(
            operator_user_id=test_manager.user_id,
            community_id=test_community.community_id,
            user_ids=[test_users[0].user_id],
            role='staff'
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['skipped_count'] == 1


class TestRemoveCommunityStaffUseCase:
    """RemoveCommunityStaffUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return RemoveCommunityStaffUseCase()

    @pytest.fixture
    def test_community(self, test_session):
        """创建测试社区"""
        community = Community(
            name="测试社区",
            manager_id=None,
            status=1
        )
        test_session.add(community)
        test_session.flush()
        return community

    @pytest.fixture
    def test_staff_user(self, test_session, test_community):
        """创建测试工作人员用户"""
        user = User(
            phone_number=generate_unique_phone_number("test_staff"),
            nickname=generate_unique_nickname("test_staff"),
            wechat_openid="openid_staff",
            community_id=test_community.community_id,
            role=Role.STAFF
        )
        test_session.add(user)
        test_session.flush()

        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=user.user_id,
            role=STAFF_ROLE_STAFF,
            added_at=datetime.now()
        )
        test_session.add(staff)
        test_session.flush()

        return user

    @pytest.fixture
    def test_manager_user(self, test_session, test_community):
        """创建测试主管用户"""
        user = User(
            phone_number=generate_unique_phone_number("test_manager"),
            nickname=generate_unique_nickname("test_manager"),
            wechat_openid="openid_manager",
            community_id=test_community.community_id,
            role=Role.MANAGER
        )
        test_session.add(user)
        test_session.flush()

        # 创建工作人员记录
        staff = CommunityStaff(
            community_id=test_community.community_id,
            user_id=user.user_id,
            role=STAFF_ROLE_MANAGER,
            added_at=datetime.now()
        )
        test_session.add(staff)
        test_session.flush()

        # 更新社区的manager_id
        community = test_session.get(Community, test_community.community_id)
        community.manager_id = user.user_id
        test_session.flush()

        return user

    def test_remove_staff_success(self, use_case, test_session, test_community, test_staff_user):
        """
        测试移除工作人员成功
        Given: 用户是工作人员
        When: 移除工作人员
        Then: 成功移除并更新用户角色
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            target_user_id=test_staff_user.user_id,
            operator_user_id=test_staff_user.user_id
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '移除成功'

        # 验证工作人员记录已被软删除
        stmt = select(CommunityStaff).where(
            CommunityStaff.user_id == test_staff_user.user_id,
            CommunityStaff.community_id == test_community.community_id
        )
        staff = test_session.execute(stmt).scalar_one_or_none()
        assert staff is not None
        assert staff.removed_at is not None

        # 验证用户角色已更新
        user = test_session.get(User, test_staff_user.user_id)
        assert user.role == Role.SOLO

    def test_remove_manager_clears_manager_id(self, use_case, test_session, test_community, test_manager_user):
        """
        测试移除主管时清理manager_id
        Given: 用户是主管
        When: 移除主管
        Then: 清理社区的manager_id字段
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            target_user_id=test_manager_user.user_id,
            operator_user_id=test_manager_user.user_id
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS

        # 验证社区的manager_id已被清理
        community = test_session.get(Community, test_community.community_id)
        assert community.manager_id is None

    def test_remove_nonexistent_staff(self, use_case, test_community):
        """
        测试移除不存在的工作人员
        Given: 用户不是工作人员
        When: 尝试移除
        Then: 返回 NOT_FOUND 状态
        """
        # Act
        result = use_case.execute(
            community_id=test_community.community_id,
            target_user_id=99999,
            operator_user_id=1
        )

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert '用户不是该社区的工作人员' in result.message

    def test_validate_missing_community_id(self, use_case):
        """
        测试验证失败 - 缺少社区ID
        Given: 没有提供社区ID
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(
            community_id=None,
            target_user_id=1
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '缺少社区ID' in result.message

    def test_validate_missing_user_id(self, use_case):
        """
        测试验证失败 - 缺少用户ID
        Given: 没有提供用户ID
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Act
        result = use_case.execute(
            community_id=1,
            target_user_id=None
        )

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert '缺少用户ID' in result.message