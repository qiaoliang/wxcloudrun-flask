"""
用户批量转移功能集成测试
端到端测试整个转移流程
"""
import pytest
from datetime import datetime, time
from sqlalchemy import select
from database.flask_models import db, User, Community, CommunityStaff, CommunityEvent, CommunityCheckinRule, UserCommunityRule
from wxcloudrun.user_transfer_service import UserTransferService
from app.shared.constants.roles import Role, STAFF_ROLE_MANAGER, STAFF_ROLE_STAFF
from tests.integration.conftest import IntegrationTestBase
from test_constants import TEST_CONSTANTS


class TestUserTransferFlow(IntegrationTestBase):
    """用户批量转移功能集成测试类"""

    def test_batch_transfer_users_e2e(self):
        """端到端测试批量转移用户流程"""
        with self.app.app_context():
            # 1. 创建超级管理员
            admin = self.get_super_admin('test_batch_transfer_users_e2e')

            # 2. 创建两个社区，并设置为主管
            # 创建一个普通用户作为社区创建者
            creator = self.create_standard_test_user(role=Role.SOLO, test_context='test_batch_transfer_users_e2e_creator')
            source_community = self.create_test_community(name='源社区_e2e', creator=creator)
            target_community = self.create_test_community(name='目标社区_e2e', creator=creator)

            # 添加管理员为两个社区的主管
            self.add_community_staff(source_community.community_id, admin['user_id'], role='manager', operator_id=admin['user_id'])
            self.add_community_staff(target_community.community_id, admin['user_id'], role='manager', operator_id=admin['user_id'])

            # 3. 为源社区创建打卡规则
            rule1 = CommunityCheckinRule(
                community_id=source_community.community_id,
                rule_name='源社区规则1',
                custom_time=time(8, 0),
                status=1,
                created_by=admin['user_id']
            )
            rule2 = CommunityCheckinRule(
                community_id=source_community.community_id,
                rule_name='源社区规则2',
                custom_time=time(12, 0),
                status=1,
                created_by=admin['user_id']
            )
            self.db.session.add(rule1)
            self.db.session.add(rule2)

            # 4. 为目标社区创建不同的打卡规则
            rule3 = CommunityCheckinRule(
                community_id=target_community.community_id,
                rule_name='目标社区规则1',
                custom_time=time(9, 0),
                status=1,
                created_by=admin['user_id']
            )
            self.db.session.add(rule3)
            self.db.session.commit()

            # 5. 在源社区添加10个普通用户，并绑定打卡规则
            users = []
            for i in range(10):
                user = self.create_standard_test_user(
                    role=Role.SOLO,
                    test_context=f'test_batch_transfer_users_e2e_{i}'
                )
                user.community_id = source_community.community_id
                user.community_joined_at = datetime.now()
                self.db.session.commit()

                # 为用户绑定源社区的打卡规则
                user_rule1 = UserCommunityRule(
                    user_id=user.user_id,
                    community_rule_id=rule1.community_rule_id,
                    is_active=True
                )
                user_rule2 = UserCommunityRule(
                    user_id=user.user_id,
                    community_rule_id=rule2.community_rule_id,
                    is_active=True
                )
                self.db.session.add(user_rule1)
                self.db.session.add(user_rule2)
                users.append(user)

            # 6. 为部分用户创建未完成事件
            event1 = CommunityEvent(
                community_id=source_community.community_id,
                title='测试事件1',
                target_user_id=users[0].user_id,
                created_by=admin['user_id'],
                event_type='supporting',
                status=1  # 进行中
            )
            event2 = CommunityEvent(
                community_id=source_community.community_id,
                title='测试事件2',
                target_user_id=users[1].user_id,
                created_by=admin['user_id'],
                event_type='supporting',
                status=2  # 已完成
            )
            self.db.session.add(event1)
            self.db.session.add(event2)
            self.db.session.commit()

            # 7. 执行批量转移
            user_ids = [u.user_id for u in users]
            result = UserTransferService.transfer_users_batch(
                admin['user_id'], source_community.community_id, target_community.community_id, user_ids
            )

            # 8. 验证结果
            assert result['success_count'] == 10, f"期望成功转移10个用户，实际转移{result['success_count']}个"
            assert result['skipped_count'] == 0, f"期望跳过0个用户，实际跳过{result['skipped_count']}个"
            assert len(result['failed']) == 0, f"期望失败0个用户，实际失败{len(result['failed'])}个"
            assert len(result['transferred_users']) == 10, f"期望转移10个用户信息，实际{len(result['transferred_users'])}个"
            assert result['events_transferred'] == 1, f"期望转移1个事件，实际转移{result['events_transferred']}个"
            assert result['rules_updated'] == 10, f"期望更新10个规则，实际更新{result['rules_updated']}个"

            # 9. 验证用户社区归属
            for user in users:
                user = self.db.session.get(User, user.user_id)
                assert user.community_id == target_community.community_id, f"用户{user.user_id}应该在目标社区"
                assert user.community_joined_at is not None, f"用户{user.user_id}的加入时间不应为空"

            # 10. 验证打卡规则切换
            for user in users:
                # 旧规则应该停用
                stmt_old_rule1 = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == user.user_id,
                    UserCommunityRule.community_rule_id == rule1.community_rule_id
                )
                old_rule1 = self.db.session.execute(stmt_old_rule1).scalar_one_or_none()
                assert old_rule1 is not None, f"用户{user.user_id}应该有旧的规则1"
                assert old_rule1.is_active == False, f"用户{user.user_id}的旧规则1应该停用"

                stmt_old_rule2 = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == user.user_id,
                    UserCommunityRule.community_rule_id == rule2.community_rule_id
                )
                old_rule2 = self.db.session.execute(stmt_old_rule2).scalar_one_or_none()
                assert old_rule2 is not None, f"用户{user.user_id}应该有旧的规则2"
                assert old_rule2.is_active == False, f"用户{user.user_id}的旧规则2应该停用"

                # 新规则应该激活
                stmt_new_rule = select(UserCommunityRule).where(
                    UserCommunityRule.user_id == user.user_id,
                    UserCommunityRule.community_rule_id == rule3.community_rule_id
                )
                new_rule = self.db.session.execute(stmt_new_rule).scalar_one_or_none()
                assert new_rule is not None, f"用户{user.user_id}应该有新的规则"
                assert new_rule.is_active == True, f"用户{user.user_id}的新规则应该激活"

            # 11. 验证事件转移
            event1 = self.db.session.get(CommunityEvent, event1.event_id)
            assert event1.community_id == target_community.community_id, "未完成事件应该转移到目标社区"

            event2 = self.db.session.get(CommunityEvent, event2.event_id)
            assert event2.community_id == source_community.community_id, "已完成事件应该保留在源社区"

    def test_transfer_with_mixed_results(self):
        """测试混合结果的转移（部分成功、部分跳过、部分失败）"""
        with self.app.app_context():
            # 1. 创建管理员
            admin = self.get_super_admin('test_transfer_with_mixed_results')

            # 2. 创建社区
            # 创建一个普通用户作为社区创建者
            creator = self.create_standard_test_user(role=Role.SOLO, test_context='test_transfer_with_mixed_results_creator')
            source_community = self.create_test_community(name='源社区_mixed', creator=creator)
            target_community = self.create_test_community(name='目标社区_mixed', creator=creator)

            # 添加管理员为两个社区的主管
            self.add_community_staff(source_community.community_id, admin['user_id'], role='manager', operator_id=admin['user_id'])
            self.add_community_staff(target_community.community_id, admin['user_id'], role='manager', operator_id=admin['user_id'])

            # 3. 创建不同类型的用户
            normal_user = self.create_standard_test_user(role=Role.SOLO, test_context='test_transfer_with_mixed_results_normal')
            normal_user.community_id = source_community.community_id
            self.db.session.commit()

            staff_user = self.create_standard_test_user(role=Role.STAFF, test_context='test_transfer_with_mixed_results_staff')
            staff_user.community_id = source_community.community_id
            self.db.session.commit()

            left_user = self.create_standard_test_user(role=Role.SOLO, test_context='test_transfer_with_mixed_results_left')
            left_user.community_id = target_community.community_id  # 已离开源社区
            self.db.session.commit()

            # 4. 执行转移
            result = UserTransferService.transfer_users_batch(
                admin['user_id'], source_community.community_id, target_community.community_id,
                [normal_user.user_id, staff_user.user_id, left_user.user_id]
            )

            # 5. 验证结果
            assert result['success_count'] == 1, f"期望成功转移1个用户，实际转移{result['success_count']}个"
            assert result['skipped_count'] == 1, f"期望跳过1个用户，实际跳过{result['skipped_count']}个"
            assert len(result['failed']) == 1, f"期望失败1个用户，实际失败{len(result['failed'])}个"

            # 验证普通用户成功转移
            normal_user = self.db.session.get(User, normal_user.user_id)
            assert normal_user.community_id == target_community.community_id, "普通用户应该成功转移到目标社区"

            # 验证工作人员转移失败
            failed_user_ids = [f['user_id'] for f in result['failed']]
            assert staff_user.user_id in failed_user_ids, "工作人员用户应该在失败列表中"
            assert '只能转移普通用户' in result['failed'][0]['reason'], "失败原因应该是'只能转移普通用户'"

            # 验证已离开用户被跳过
            assert result['skipped_count'] == 1, "已离开用户应该被跳过"

    def test_transfer_with_manager_not_in_target_community(self):
        """测试主管不是目标社区的主管"""
        with self.app.app_context():
            # 1. 创建主管（非超级管理员）
            manager = self.create_standard_test_user(role=Role.MANAGER, test_context='test_transfer_with_manager_not_in_target')

            # 2. 创建社区
            # 创建一个普通用户作为社区创建者
            creator = self.create_standard_test_user(role=Role.SOLO, test_context='test_transfer_with_manager_not_in_target_creator')
            source_community = self.create_test_community(name='源社区_permission', creator=creator)
            target_community = self.create_test_community(name='目标社区_permission', creator=creator)

            # 3. 只设置为主管在源社区
            self.add_community_staff(source_community.community_id, manager.user_id, role='manager', operator_id=manager.user_id)

            # 4. 创建普通用户
            user = self.create_standard_test_user(role=Role.SOLO, test_context='test_transfer_with_manager_not_in_target_user')
            user.community_id = source_community.community_id
            self.db.session.commit()

            # 5. 执行转移（应该抛出异常）
            with pytest.raises(ValueError) as exc_info:
                UserTransferService.transfer_users_batch(
                    manager.user_id, source_community.community_id, target_community.community_id, [user.user_id]
                )

            assert '权限不足' in str(exc_info.value), "异常信息应该包含'权限不足'"
            assert '目标社区的主管' in str(exc_info.value), "异常信息应该包含'目标社区的主管'"