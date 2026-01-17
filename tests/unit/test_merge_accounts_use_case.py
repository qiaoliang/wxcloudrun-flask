"""
合并账号用例单元测试

测试 MergeAccountsUseCase：
1. 验证失败场景（账号为空、同一账号）
2. 执行成功场景（合并两个账号）
3. 迁移用户信息（wechat_openid, phone_number, nickname, avatar_url, name）
4. 迁移监督关系
5. 删除次要账号

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
"""
import pytest
from datetime import datetime, timedelta
from database.flask_models import User, SupervisionRuleRelation, CheckinRule
from app.application.use_cases.user.merge_accounts_use_case import MergeAccountsUseCase
from app.application.use_cases.base import UseCaseStatus


class TestMergeAccountsUseCase:
    """MergeAccountsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return MergeAccountsUseCase()

    @pytest.fixture
    def test_user_with_wechat(self, test_session):
        """创建带微信OpenID的测试用户（较早创建）"""
        user = User(
            wechat_openid="test_openid_1",
            phone_number=None,
            phone_hash=None,
            nickname="微信用户",
            name=None,
            avatar_url=None,
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        test_session.add(user)
        test_session.commit()
        return user

    @pytest.fixture
    def test_user_with_phone(self, test_session):
        """创建带手机号的测试用户（较晚创建）"""
        user = User(
            wechat_openid=None,
            phone_number="13900001111",
            phone_hash="test_hash_1",
            nickname=None,
            name="张三",
            avatar_url="https://example.com/avatar1.jpg",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        test_session.add(user)
        test_session.commit()
        return user

    @pytest.fixture
    def test_checkin_rule(self, test_session):
        """创建测试打卡规则"""
        from datetime import time
        # 创建一个临时用户作为规则所有者
        temp_user = User(
            wechat_openid="temp_rule_user",
            phone_number="13900009999",
            phone_hash="temp_rule_hash",
            nickname="临时用户",
            role=1,
            status=1
        )
        test_session.add(temp_user)
        test_session.flush()

        rule = CheckinRule(
            rule_name="测试规则",
            user_id=temp_user.user_id,
            rule_type='personal',
            custom_time=time(8, 0),
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    @pytest.fixture
    def test_supervision_relations(self, test_session, test_user_with_phone, test_checkin_rule):
        """创建测试监督关系"""
        # 创建3个不同的监督者
        supervisors = []
        for i in range(3):
            supervisor = User(
                wechat_openid=f"supervisor_openid_{i}",
                phone_number=f"1390000222{i}",
                phone_hash=f"supervisor_hash_{i}",
                nickname=f"监督者{i}",
                role=1,
                status=1
            )
            test_session.add(supervisor)
            supervisors.append(supervisor)
        test_session.flush()

        # 创建3条不同的监督关系
        relations = []
        for i, supervisor in enumerate(supervisors):
            relation = SupervisionRuleRelation(
                solo_user_id=test_user_with_phone.user_id,
                supervisor_user_id=supervisor.user_id,
                rule_id=test_checkin_rule.rule_id,
                status=2,
                invitation_type="link"
            )
            test_session.add(relation)
            relations.append(relation)

        test_session.commit()
        return relations

    def test_validate_missing_account1(self, use_case, test_user_with_phone):
        """
        测试验证失败 - 缺少第一个账号
        Given: 第一个账号为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        account1 = None
        account2 = test_user_with_phone

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "账号不能为空" in result.message

    def test_validate_missing_account2(self, use_case, test_user_with_wechat):
        """
        测试验证失败 - 缺少第二个账号
        Given: 第二个账号为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        account1 = test_user_with_wechat
        account2 = None

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "账号不能为空" in result.message

    def test_validate_same_account(self, use_case, test_user_with_wechat):
        """
        测试验证失败 - 同一账号
        Given: 两个账号是同一个
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        account1 = test_user_with_wechat
        account2 = test_user_with_wechat

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "不能合并同一个账号" in result.message

    def test_execute_success_basic_merge(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 基本合并
        Given: 两个不同的账号（一个有微信，一个有手机号）
        When: 调用 execute 方法
        Then: 成功合并账号，保留较早创建的账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建
        account2 = test_user_with_phone  # 较晚创建
        primary_user_id = account1.user_id
        secondary_user_id = account2.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "账号合并成功" in result.message
        assert result.data['primary_user_id'] == primary_user_id
        assert result.data['secondary_user_id'] == secondary_user_id

    def test_execute_migrates_wechat_openid(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 迁移微信OpenID
        Given: 主账号没有微信OpenID，次要账号有
        When: 调用 execute 方法
        Then: 成功迁移微信OpenID到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建，有微信
        account2 = test_user_with_phone  # 较晚创建，有手机号
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号应该保留自己的微信OpenID
        assert account1.wechat_openid == "test_openid_1"

    def test_execute_migrates_phone_number(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 迁移手机号
        Given: 主账号没有手机号，次要账号有
        When: 调用 execute 方法
        Then: 成功迁移手机号到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建，没有手机号
        account2 = test_user_with_phone  # 较晚创建，有手机号
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号应该获得手机号
        assert account1.phone_number == "13900001111"

    def test_execute_migrates_nickname(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 迁移昵称
        Given: 主账号没有昵称，次要账号有
        When: 调用 execute 方法
        Then: 成功迁移昵称到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建，有昵称
        account2 = test_user_with_phone  # 较晚创建，没有昵称
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号应该保留自己的昵称
        assert account1.nickname == "微信用户"

    def test_execute_migrates_name(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 迁移姓名
        Given: 主账号没有姓名，次要账号有
        When: 调用 execute 方法
        Then: 成功迁移姓名到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建，没有姓名
        account2 = test_user_with_phone  # 较晚创建，有姓名
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号应该获得姓名
        assert account1.name == "张三"

    def test_execute_migrates_avatar_url(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 迁移头像URL
        Given: 主账号没有头像，次要账号有
        When: 调用 execute 方法
        Then: 成功迁移头像URL到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建，没有头像
        account2 = test_user_with_phone  # 较晚创建，有头像
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号应该获得头像URL
        assert account1.avatar_url == "https://example.com/avatar1.jpg"

    def test_execute_migrates_supervision_relations(self, use_case, test_user_with_wechat, test_user_with_phone, test_supervision_relations):
        """
        测试执行成功 - 迁移监督关系
        Given: 次要账号有监督关系
        When: 调用 execute 方法
        Then: 成功迁移监督关系到主账号
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建
        account2 = test_user_with_phone  # 较晚创建，有监督关系
        primary_user_id = account1.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 应该迁移了3条监督关系
        assert result.data['migrated_supervision_count'] == 3

        # 验证监督关系已迁移到主账号
        migrated_relations = use_case.supervision_relation_repository.find_by_solo_user_id(primary_user_id)
        assert len(migrated_relations) == 3
        for relation in migrated_relations:
            assert relation.solo_user_id == primary_user_id

    def test_execute_deletes_secondary_account(self, use_case, test_user_with_wechat, test_user_with_phone):
        """
        测试执行成功 - 删除次要账号
        Given: 两个不同的账号
        When: 调用 execute 方法
        Then: 次要账号被删除
        """
        # Arrange
        account1 = test_user_with_wechat  # 较早创建
        account2 = test_user_with_phone  # 较晚创建
        secondary_user_id = account2.user_id

        # Act
        result = use_case.execute(account1, account2)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 次要账号应该被删除
        deleted_user = use_case.user_repository.find_by_id(secondary_user_id)
        assert deleted_user is None

    def test_execute_chooses_earlier_account_as_primary(self, use_case, test_session):
        """
        测试执行成功 - 选择较早创建的账号作为主账号
        Given: 两个账号，第二个较早创建
        When: 调用 execute 方法
        Then: 选择较早创建的账号作为主账号
        """
        # Arrange
        from datetime import datetime, timedelta
        import uuid

        # 创建较晚的账号
        later_account = User(
            wechat_openid=f"later_openid_{uuid.uuid4().hex[:8]}",
            phone_number=None,
            phone_hash=None,
            nickname="较晚账号",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        test_session.add(later_account)
        test_session.flush()

        # 创建较早的账号
        earlier_account = User(
            wechat_openid=None,
            phone_number=f"1390000{uuid.uuid4().hex[:4]}",
            phone_hash=f"earlier_hash_{uuid.uuid4().hex[:8]}",
            nickname=None,
            name="较早账号",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        test_session.add(earlier_account)
        test_session.commit()

        # Act
        result = use_case.execute(later_account, earlier_account)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 较早的账号应该成为主账号
        assert result.data['primary_user_id'] == earlier_account.user_id
        assert result.data['secondary_user_id'] == later_account.user_id

    def test_execute_does_not_overwrite_existing_fields(self, use_case, test_session):
        """
        测试执行成功 - 不覆盖已有字段
        Given: 主账号已有某些字段，次要账号也有相同字段
        When: 调用 execute 方法
        Then: 主账号的已有字段不被覆盖
        """
        # Arrange
        from datetime import datetime, timedelta

        # 主账号（较早创建，已有所有字段）
        primary_account = User(
            wechat_openid="primary_openid",
            phone_number="13900004444",
            phone_hash="primary_hash",
            nickname="主账号昵称",
            name="主账号姓名",
            avatar_url="https://example.com/primary.jpg",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        test_session.add(primary_account)
        test_session.flush()

        # 次要账号（较晚创建，也有所有字段）
        secondary_account = User(
            wechat_openid="secondary_openid",
            phone_number="13900005555",
            phone_hash="secondary_hash",
            nickname="次要账号昵称",
            name="次要账号姓名",
            avatar_url="https://example.com/secondary.jpg",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        test_session.add(secondary_account)
        test_session.commit()

        # Act
        result = use_case.execute(primary_account, secondary_account)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 主账号的字段应该保持不变
        assert primary_account.wechat_openid == "primary_openid"
        assert primary_account.phone_number == "13900004444"
        assert primary_account.nickname == "主账号昵称"
        assert primary_account.name == "主账号姓名"
        assert primary_account.avatar_url == "https://example.com/primary.jpg"

    def test_execute_handles_duplicate_supervision_relations(self, use_case, test_session):
        """
        测试执行成功 - 处理重复的监督关系
        Given: 次要账号有监督关系，且主账号已有相同监督关系
        When: 调用 execute 方法
        Then: 删除重复的监督关系，保留主账号的
        """
        # Arrange
        from datetime import datetime, timedelta

        # 创建监督者
        supervisor = User(
            wechat_openid="supervisor_openid",
            phone_number="13900006666",
            phone_hash="supervisor_hash_2",
            nickname="监督者",
            role=1,
            status=1
        )
        test_session.add(supervisor)
        test_session.flush()

        # 创建打卡规则
        from datetime import time
        # 创建一个临时用户作为规则所有者
        temp_user = User(
            wechat_openid="temp_rule_user_2",
            phone_number="13900008888",
            phone_hash="temp_rule_hash_2",
            nickname="临时用户2",
            role=1,
            status=1
        )
        test_session.add(temp_user)
        test_session.flush()

        rule = CheckinRule(
            rule_name="测试规则2",
            user_id=temp_user.user_id,
            rule_type='personal',
            custom_time=time(9, 0),
            status=1
        )
        test_session.add(rule)
        test_session.flush()
        test_session.add(rule)
        test_session.flush()

        # 主账号（较早创建）
        primary_account = User(
            wechat_openid="primary_openid_2",
            phone_number=None,
            phone_hash=None,
            nickname="主账号",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=2)
        )
        test_session.add(primary_account)
        test_session.flush()

        # 次要账号（较晚创建）
        secondary_account = User(
            wechat_openid=None,
            phone_number="13900007777",
            phone_hash="secondary_hash_2",
            nickname="次要账号",
            role=1,
            status=1,
            created_at=datetime.now() - timedelta(days=1)
        )
        test_session.add(secondary_account)
        test_session.flush()

        # 为主账号创建监督关系
        primary_relation = SupervisionRuleRelation(
            solo_user_id=primary_account.user_id,
            supervisor_user_id=supervisor.user_id,
            rule_id=rule.rule_id,
            status=2,
            invitation_type="link"
        )
        test_session.add(primary_relation)

        # 为次要账号创建相同的监督关系
        secondary_relation = SupervisionRuleRelation(
            solo_user_id=secondary_account.user_id,
            supervisor_user_id=supervisor.user_id,
            rule_id=rule.rule_id,
            status=2,
            invitation_type="link"
        )
        test_session.add(secondary_relation)
        test_session.commit()

        # Act
        result = use_case.execute(primary_account, secondary_account)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        # 不应该迁移任何监督关系，因为已经存在
        assert result.data['migrated_supervision_count'] == 0

        # 验证主账号只有一条监督关系
        primary_relations = use_case.supervision_relation_repository.find_by_solo_user_id(primary_account.user_id)
        assert len(primary_relations) == 1

        # 验证次要账号的监督关系被删除
        secondary_relations = use_case.supervision_relation_repository.find_by_solo_user_id(secondary_account.user_id)
        assert len(secondary_relations) == 0