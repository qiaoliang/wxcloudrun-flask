"""
测试社区工作人员角色管理重构功能
"""
import pytest
from database.flask_models import db, User, Community, CommunityStaff
from wxcloudrun.community_staff_service import CommunityStaffService
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from const_default import DEFAULT_COMMUNITY_ID

class TestRoleRecalculation:
    """测试用户角色重新计算功能"""

    def test_recalculate_role_from_solo_to_staff(self, test_session, test_app):
        """测试从普通用户到专员的role计算"""
        test_context = "test_solo_to_staff"
        with test_app.app_context():
            # 创建测试用户（普通用户）
            phone = f"138{test_context}0001"
            user = User(
                wechat_openid=f"openid_{test_context}_1",
                nickname=f"test_user_{test_context}_1",
                phone_number=phone,
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )
            test_session.add(user)
            test_session.commit()

            # 创建社区
            community = Community(
                name=f'{test_context}_测试社区',
                description='测试',
                creator_id=1
            )
            test_session.add(community)
            test_session.commit()

            # 添加为专员
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_STAFF
            )
            test_session.add(staff)
            test_session.commit()

            # 调用重新计算方法
            CommunityStaffService._recalculate_user_role(user.user_id)

            # 验证角色已更新为专员
            test_session.refresh(user)
            assert user.role == Role.STAFF

    def test_recalculate_role_from_staff_to_manager(self, test_session, test_app):
        """测试从专员到主管的role计算"""
        test_context = "test_staff_to_manager"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0002",
                role=Role.STAFF,
                status=1
            )
            test_session.add(user)

            community_a = Community(name=f'{test_context}_A', description='A', creator_id=1)
            community_b = Community(name=f'{test_context}_B', description='B', creator_id=1)
            test_session.add_all([community_a, community_b])
            test_session.commit()

            # 添加为两个社区的工作人员
            staff_a = CommunityStaff(
                community_id=community_a.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_STAFF
            )
            staff_b = CommunityStaff(
                community_id=community_b.community_id,
                user_id=user.user_id,
                role=STAFF_ROLE_MANAGER
            )
            test_session.add_all([staff_a, staff_b])
            test_session.commit()

            # 重新计算
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 应该是主管（取最高角色）
            assert new_role == Role.MANAGER
            test_session.refresh(user)
            assert user.role == Role.MANAGER

    def test_recalculate_role_preserve_super_admin(self, test_session, test_app):
        """测试超级管理员角色不会被降级"""
        test_context = "test_preserve_super_admin"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0003",
                role=Role.SUPER_ADMIN,
                status=1
            )
            test_session.add(user)

            community = Community(name=f'{test_context}', description='test', creator_id=1)
            test_session.add(community)
            test_session.commit()

            # 移除所有工作人员身份（假设有）
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 角色应该保持为超级管理员
            assert new_role == Role.SUPER_ADMIN
            test_session.refresh(user)
            assert user.role == Role.SUPER_ADMIN

    def test_recalculate_role_no_staff_records(self, test_session, test_app):
        """测试无工作人员记录时降级为普通用户"""
        test_context = "test_no_staff_records"
        with test_app.app_context():
            user = User(
                wechat_openid=f"openid_{test_context}",
                nickname=f"test_{test_context}",
                phone_number=f"138{test_context}0004",
                role=Role.STAFF,
                status=1
            )
            test_session.add(user)
            test_session.commit()

            # 重新计算（无工作人员记录）
            new_role = CommunityStaffService._recalculate_user_role(user.user_id)

            # 应该降级为普通用户
            assert new_role == Role.SOLO
            test_session.refresh(user)
            assert user.role == Role.SOLO

class TestCommunityIdUpdate:
    """测试社区ID变更逻辑"""

    def test_community_id_update_only_from_anka(self, test_session, test_app):
        """测试只有安卡大家庭的用户才会更新社区ID"""
        test_context = "test_anka_update"
        with test_app.app_context():
            # 创建一个非1的社区作为目标社区（避免与DEFAULT_COMMUNITY_ID=1冲突）
            community = Community(
                community_id=100,  # 显式设置一个非1的ID
                name=f'{test_context}_幸福社区',
                description='测试社区',
                creator_id=1
            )
            test_session.add(community)
            test_session.flush()  # 确保community被添加

            # 创建安卡大家庭用户
            anka_user = User(
                wechat_openid=f"openid_{test_context}_anka",
                nickname=f"anka_{test_context}",
                phone_number=f"138{test_context}1001",
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            # 创建其他社区用户
            other_user = User(
                wechat_openid=f"openid_{test_context}_other",
                nickname=f"other_{test_context}",
                phone_number=f"138{test_context}1002",
                role=Role.SOLO,
                status=1,
                community_id=999  # 其他社区
            )

            # 创建超级管理员
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}1003",
                role=Role.SUPER_ADMIN,
                status=1
            )

            test_session.add_all([anka_user, other_user, super_admin])
            test_session.commit()

            # 添加安卡大家庭用户为工作人员
            result1 = CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[anka_user.user_id],
                role=STAFF_ROLE_STAFF
            )

            assert result1['success_count'] == 1
            test_session.commit()  # 提交更改
            test_session.refresh(anka_user)
            assert anka_user.community_id == 100, f"Expected community_id=100, got {anka_user.community_id}"

            # 添加其他社区用户为工作人员
            result2 = CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[other_user.user_id],
                role=STAFF_ROLE_STAFF
            )

            assert result2['success_count'] == 1
            test_session.commit()  # 提交更改
            test_session.refresh(other_user)
            assert other_user.community_id == 999, f"Expected community_id=999, got {other_user.community_id}"  # 保持不变

class TestSameCommunityRoleHandling:
    """测试同社区角色处理逻辑"""

    def test_add_staff_promote_from_staff_to_manager(self, test_session, test_app):
        """测试专员升级为主管"""
        test_context = "test_promote_staff"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}2001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            community = Community(
                community_id=200,  # 显式设置ID避免冲突
                name=f'{test_context}_社区',
                description='测试',
                creator_id=1
            )

            user = User(
                wechat_openid=f"openid_{test_context}_user",
                nickname=f"user_{test_context}",
                phone_number=f"138{test_context}2002",
                role=Role.STAFF,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            test_session.add_all([super_admin, community, user])
            test_session.commit()

            # 先添加为专员
            CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[user.user_id],
                role=STAFF_ROLE_STAFF
            )

            # 再次添加为主管（升级）
            result = CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[user.user_id],
                role=STAFF_ROLE_MANAGER
            )

            assert result['success_count'] == 1
            test_session.refresh(user)
            assert user.role == Role.MANAGER

    def test_add_staff_skip_same_role(self, test_session, test_app):
        """测试添加相同角色时静默跳过"""
        test_context = "test_skip_same"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}3001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            community = Community(
                community_id=300,  # 显式设置ID避免冲突
                name=f'{test_context}_社区',
                description='测试',
                creator_id=1
            )

            user = User(
                wechat_openid=f"openid_{test_context}_user",
                nickname=f"user_{test_context}",
                phone_number=f"138{test_context}3002",
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            test_session.add_all([super_admin, community, user])
            test_session.commit()

            # 第一次添加为专员
            result1 = CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[user.user_id],
                role=STAFF_ROLE_STAFF
            )
            assert result1['success_count'] == 1

            # 第二次添加为专员（相同角色）
            result2 = CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[user.user_id],
                role=STAFF_ROLE_STAFF
            )

            # 应该静默跳过
            assert result2['success_count'] == 0
            assert result2.get('skipped_count', 0) >= 1

    def test_add_staff_demote_manager_requires_super_admin(self, test_session, test_app):
        """测试主管降级为专员需要超级管理员权限"""
        test_context = "test_demote_requires_admin"
        with test_app.app_context():
            # 创建超级管理员
            super_admin = User(
                wechat_openid=f"openid_{test_context}_super",
                nickname=f"super_{test_context}",
                phone_number=f"138{test_context}4000",
                role=Role.SUPER_ADMIN,
                status=1
            )

            # 创建普通主管
            regular_manager = User(
                wechat_openid=f"openid_{test_context}_manager",
                nickname=f"manager_{test_context}",
                phone_number=f"138{test_context}4001",
                role=Role.MANAGER,
                status=1
            )

            # 创建目标用户（已是主管）
            target_user = User(
                wechat_openid=f"openid_{test_context}_target",
                nickname=f"target_{test_context}",
                phone_number=f"138{test_context}4002",
                role=Role.MANAGER,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            # 创建两个社区（避免冲突）
            community1 = Community(
                community_id=401,
                name=f'{test_context}_社区1',
                description='测试',
                creator_id=1
            )

            community2 = Community(
                community_id=402,
                name=f'{test_context}_社区2',
                description='测试',
                creator_id=1
            )

            test_session.add_all([super_admin, regular_manager, target_user, community1, community2])
            test_session.commit()

            # 添加普通主管到社区1
            CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community1.community_id,
                user_ids=[regular_manager.user_id],
                role=STAFF_ROLE_MANAGER
            )

            # 添加目标用户为主管到社区2
            CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community2.community_id,
                user_ids=[target_user.user_id],
                role=STAFF_ROLE_MANAGER
            )

            # 普通主管尝试在社区2降级另一个主管
            try:
                CommunityStaffService.add_staff(
                    operator_user_id=regular_manager.user_id,
                    community_id=community2.community_id,
                    user_ids=[target_user.user_id],
                    role=STAFF_ROLE_STAFF
                )
                assert False, "Should have raised ValueError"
            except ValueError as e:
                # 应该抛出权限不足的错误
                assert '权限不足' in str(e) or len(e.args[0]) > 0

class TestRemoveStaffRoleRecalculation:
    """测试移除工作人员后角色重新计算"""

    def test_remove_staff_recalculates_role(self, test_session, test_app):
        """测试移除工作人员后重新计算角色"""
        test_context = "test_remove_recalculate"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}5001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            user = User(
                wechat_openid=f"openid_{test_context}_user",
                nickname=f"user_{test_context}",
                phone_number=f"138{test_context}5002",
                role=Role.SOLO,
                status=1,
                community_id=DEFAULT_COMMUNITY_ID
            )

            community = Community(
                community_id=500,
                name=f'{test_context}_社区',
                description='测试',
                creator_id=1
            )

            test_session.add_all([super_admin, user, community])
            test_session.commit()

            # 添加为专员
            CommunityStaffService.add_staff(
                operator_user_id=super_admin.user_id,
                community_id=community.community_id,
                user_ids=[user.user_id],
                role=STAFF_ROLE_STAFF
            )

            test_session.commit()
            test_session.refresh(user)
            assert user.role == Role.STAFF

            # 移除工作人员
            CommunityStaffService.remove_staff(
                community_id=community.community_id,
                user_id=user.user_id,
                operator_id=super_admin.user_id
            )

            test_session.commit()
            # 角色应该重新计算为普通用户
            test_session.refresh(user)
            assert user.role == Role.SOLO

class TestSetSuperAdmin:
    """测试超级管理员设置功能"""

    def test_set_super_admin(self, test_session, test_app):
        """测试设置超级管理员"""
        test_context = "test_set_super_admin"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}6001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            manager = User(
                wechat_openid=f"openid_{test_context}_manager",
                nickname=f"manager_{test_context}",
                phone_number=f"138{test_context}6002",
                role=Role.MANAGER,
                status=1
            )

            test_session.add_all([super_admin, manager])
            test_session.commit()

            result = CommunityStaffService.set_super_admin(
                operator_user_id=super_admin.user_id,
                target_user_id=manager.user_id,
                is_super_admin=True
            )

            assert result['success'] == True
            test_session.refresh(manager)
            assert manager.role == Role.SUPER_ADMIN

    def test_remove_super_admin(self, test_session, test_app):
        """测试取消超级管理员"""
        test_context = "test_remove_super_admin"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}7001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            other_super = User(
                wechat_openid=f"openid_{test_context}_other",
                nickname=f"other_{test_context}",
                phone_number=f"138{test_context}7002",
                role=Role.SUPER_ADMIN,
                status=1
            )

            community = Community(
                community_id=700,
                name=f'{test_context}_社区',
                description='测试',
                creator_id=1
            )

            test_session.add_all([super_admin, other_super, community])
            test_session.commit()

            # 添加另一个超级管理员为主管
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=other_super.user_id,
                role=STAFF_ROLE_MANAGER
            )
            test_session.add(staff)
            test_session.commit()

            result = CommunityStaffService.set_super_admin(
                operator_user_id=super_admin.user_id,
                target_user_id=other_super.user_id,
                is_super_admin=False
            )

            assert result['success'] == True
            test_session.refresh(other_super)
            assert other_super.role == Role.MANAGER  # 降级为主管

    def test_cannot_modify_own_super_admin_role(self, test_session, test_app):
        """测试不能修改自己的超级管理员身份"""
        test_context = "test_own_role"
        with test_app.app_context():
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}8001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            test_session.add(super_admin)
            test_session.commit()

            with pytest.raises(ValueError) as exc_info:
                CommunityStaffService.set_super_admin(
                    operator_user_id=super_admin.user_id,
                    target_user_id=super_admin.user_id,
                    is_super_admin=False
                )

            assert '不能修改自己' in str(exc_info.value)

    def test_only_super_admin_can_set_super_admin(self, test_session, test_app):
        """测试只有超级管理员可以设置其他超级管理员"""
        test_context = "test_permission"
        with test_app.app_context():
            regular_manager = User(
                wechat_openid=f"openid_{test_context}_manager",
                nickname=f"manager_{test_context}",
                phone_number=f"138{test_context}9001",
                role=Role.MANAGER,
                status=1
            )

            target_user = User(
                wechat_openid=f"openid_{test_context}_target",
                nickname=f"target_{test_context}",
                phone_number=f"138{test_context}9002",
                role=Role.SOLO,
                status=1
            )

            test_session.add_all([regular_manager, target_user])
            test_session.commit()

            with pytest.raises(ValueError) as exc_info:
                CommunityStaffService.set_super_admin(
                    operator_user_id=regular_manager.user_id,
                    target_user_id=target_user.user_id,
                    is_super_admin=True
                )

            assert '只有超级管理员' in str(exc_info.value)

class TestGetAdminList:
    """测试获取管理员列表功能"""

    def test_get_admin_list(self, test_session, test_app):
        """测试获取管理员列表"""
        test_context = "test_get_admin_list_final"  # Unique name to avoid conflicts
        with test_app.app_context():
            # 创建超级管理员
            super_admin = User(
                wechat_openid=f"openid_{test_context}_admin",
                nickname=f"admin_{test_context}",
                phone_number=f"138{test_context}0001",
                role=Role.SUPER_ADMIN,
                status=1
            )

            # 创建社区和主管（使用唯一ID）
            import time
            unique_id = int(time.time() * 1000) % 10000  # Get unique ID
            community = Community(
                community_id=unique_id,
                name=f'{test_context}_社区',
                description='测试',
                creator_id=1
            )

            manager = User(
                wechat_openid=f"openid_{test_context}_manager",
                nickname=f"manager_{test_context}",
                phone_number=f"138{test_context}0002",
                role=Role.MANAGER,
                status=1
            )

            test_session.add_all([super_admin, community, manager])
            test_session.commit()

            # 添加主管到社区
            staff = CommunityStaff(
                community_id=community.community_id,
                user_id=manager.user_id,
                role=STAFF_ROLE_MANAGER
            )
            test_session.add(staff)
            test_session.commit()

            # 获取管理员列表
            admin_list = CommunityStaffService.get_admin_list()

            # 验证结果 - 查找我们创建的管理员
            super_admin_record = next((a for a in admin_list if a['user_id'] == super_admin.user_id), None)
            manager_record = next((a for a in admin_list if a['user_id'] == manager.user_id), None)

            assert super_admin_record is not None, "Super admin not found in list"
            assert super_admin_record['role'] == '超级管理员'
            assert manager_record is not None, "Manager not found in list"
            assert manager_record['role'] == f'{community.name}主管'
            assert manager_record['community_name'] == community.name
