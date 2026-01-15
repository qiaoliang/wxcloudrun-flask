"""
打卡模块 UseCases 单元测试

测试以下 UseCase：
1. PerformCheckinUseCase - 执行打卡
2. CreateCheckinRuleUseCase - 创建打卡规则
3. UpdateCheckinRuleUseCase - 更新打卡规则
4. DeleteCheckinRuleUseCase - 删除打卡规则
5. GetCheckinHistoryUseCase - 获取打卡历史
6. GetTodayCheckinsUseCase - 获取今日打卡
7. CancelCheckinUseCase - 取消打卡
8. ReportMissCheckinUseCase - 报告漏打卡

测试原则：
- 使用 AAA 模式（Arrange-Act-Assert）
- 测试行为而非实现细节
- 一个测试只验证一件事
- 清晰的测试命名
- 使用 mock 来隔离依赖
"""
import pytest
from datetime import datetime, date, time, timedelta
from unittest.mock import Mock, patch, MagicMock

from database.flask_models import User, Community, CheckinRule, CheckinRecord
from app.application.use_cases.checkin.perform_checkin_use_case import PerformCheckinUseCase
from app.application.use_cases.checkin.create_checkin_rule_use_case import CreateCheckinRuleUseCase
from app.application.use_cases.checkin.update_checkin_rule_use_case import UpdateCheckinRuleUseCase
from app.application.use_cases.checkin.delete_checkin_rule_use_case import DeleteCheckinRuleUseCase
from app.application.use_cases.checkin.get_checkin_history_use_case import GetCheckinHistoryUseCase
from app.application.use_cases.checkin.get_today_checkins_use_case import GetTodayCheckinsUseCase
from app.application.use_cases.checkin.cancel_checkin_use_case import CancelCheckinUseCase
from app.application.use_cases.checkin.report_miss_checkin_use_case import ReportMissCheckinUseCase
from app.application.use_cases.checkin.get_checkin_rule_use_case import GetCheckinRuleUseCase
from app.application.use_cases.base import UseCaseStatus


class TestPerformCheckinUseCase:
    """PerformCheckinUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return PerformCheckinUseCase()

    @pytest.fixture
    def test_checkin_rule(self, test_session, test_user, test_community):
        """创建测试打卡规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="测试打卡规则",
            rule_type="personal",
            frequency_type=0,  # 每天
            time_slot_type=4,
            custom_time=time(8, 0),
            week_days=127,  # 每天都打卡
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    @pytest.fixture
    def test_checkin_rule_today(self, test_session, test_user, test_community):
        """创建今日需要打卡的规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="今日打卡规则",
            rule_type="personal",
            frequency_type=0,  # 每天
            time_slot_type=4,
            custom_time=time(8, 0),
            week_days=127,
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    def test_execute_success(self, use_case, test_user, test_checkin_rule):
        """
        测试执行打卡成功
        Given: 有效的规则ID和用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，创建打卡记录
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.message == '打卡成功'
        assert result.data['rule_id'] == rule_id
        assert result.data['user_id'] == user_id
        assert result.data['status'] == 'completed'
        assert 'record_id' in result.data

    def test_execute_missing_rule_id(self, use_case, test_user):
        """
        测试执行打卡失败 - 缺少规则ID
        Given: 规则ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = None
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则ID不能为空" in result.message

    def test_execute_missing_user_id(self, use_case, test_checkin_rule):
        """
        测试执行打卡失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = None

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_user_not_found(self, use_case, test_checkin_rule):
        """
        测试执行打卡失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = 99999

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_rule_not_found(self, use_case, test_user):
        """
        测试执行打卡失败 - 规则不存在
        Given: 不存在的规则ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = 99999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡规则不存在" in result.message

    def test_execute_permission_denied(self, use_case, test_user, test_checkin_rule, test_superuser):
        """
        测试执行打卡失败 - 无权限
        Given: 规则不属于当前用户
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_superuser.user_id  # 使用超级用户尝试打卡

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "无权限操作此打卡规则" in result.message

    def test_execute_duplicate_checkin(self, use_case, test_user, test_checkin_rule, test_session):
        """
        测试执行打卡失败 - 重复打卡
        Given: 今天已经打过卡
        When: 再次调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id

        # 第一次打卡
        use_case.execute(rule_id=rule_id, user_id=user_id)

        # Act - 第二次打卡
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "今日该事项已打卡" in result.message


class TestCreateCheckinRuleUseCase:
    """CreateCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CreateCheckinRuleUseCase()

    def test_execute_success(self, use_case, test_user, test_community):
        """
        测试创建打卡规则成功
        Given: 有效的规则数据
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，创建规则
        """
        # Arrange
        user_id = test_user.user_id
        rule_data = {
            'rule_name': '测试规则',
            'frequency_type': 0,
            'time_slot_type': 4,
            'custom_time': '08:00',
            'week_days': 127
        }

        # Act
        result = use_case.execute(user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "打卡规则创建成功" in result.message
        assert 'rule' in result.data
        assert result.data['rule'].rule_name == '测试规则'

    def test_execute_missing_rule_name(self, use_case, test_user):
        """
        测试创建打卡规则失败 - 缺少规则名称
        Given: 规则数据中缺少 rule_name
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        rule_data = {}

        # Act
        result = use_case.execute(user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则名称不能为空" in result.message

    def test_execute_user_not_found(self, use_case):
        """
        测试创建打卡规则失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 99999
        rule_data = {
            'rule_name': '测试规则'
        }

        # Act
        result = use_case.execute(user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_with_week_days_list(self, use_case, test_user):
        """
        测试创建打卡规则成功 - 使用 week_days 列表
        Given: week_days 为列表格式
        When: 调用 execute 方法
        Then: 成功创建规则，week_days 转换为整数
        """
        # Arrange
        user_id = test_user.user_id
        rule_data = {
            'rule_name': '测试规则',
            'week_days': [1, 2, 3, 4, 5]  # 周一到周五
        }

        # Act
        result = use_case.execute(user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['rule'].week_days == 31  # 1+2+4+8+16

    def test_execute_custom_frequency_invalid_dates(self, use_case, test_user):
        """
        测试创建打卡规则失败 - 自定义频率日期无效
        Given: 自定义频率的结束日期早于开始日期
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = test_user.user_id
        rule_data = {
            'rule_name': '测试规则',
            'frequency_type': 3,  # 自定义频率
            'custom_start_date': '2026-01-20',
            'custom_end_date': '2026-01-10'
        }

        # Act
        result = use_case.execute(user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "结束日期不能早于开始日期" in result.message


class TestUpdateCheckinRuleUseCase:
    """UpdateCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return UpdateCheckinRuleUseCase()

    @pytest.fixture
    def test_checkin_rule(self, test_session, test_user, test_community):
        """创建测试打卡规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="原始规则名称",
            rule_type="personal",
            frequency_type=0,
            time_slot_type=4,
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    def test_execute_success(self, use_case, test_user, test_checkin_rule):
        """
        测试更新打卡规则成功
        Given: 有效的规则ID和更新数据
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，更新规则
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id
        rule_data = {
            'rule_name': '更新后的规则名称'
        }

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "打卡规则更新成功" in result.message
        assert result.data['rule'].rule_name == '更新后的规则名称'

    def test_execute_missing_rule_id(self, use_case, test_user):
        """
        测试更新打卡规则失败 - 缺少规则ID
        Given: 规则ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = None
        user_id = test_user.user_id
        rule_data = {}

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则ID不能为空" in result.message

    def test_execute_rule_not_found(self, use_case, test_user):
        """
        测试更新打卡规则失败 - 规则不存在
        Given: 不存在的规则ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = 99999
        user_id = test_user.user_id
        rule_data = {}

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡规则不存在" in result.message

    def test_execute_permission_denied(self, use_case, test_checkin_rule, test_superuser):
        """
        测试更新打卡规则失败 - 无权限
        Given: 规则不属于当前用户
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_superuser.user_id
        rule_data = {'rule_name': '尝试修改'}

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "无权限修改此打卡规则" in result.message

    def test_execute_update_multiple_fields(self, use_case, test_user, test_checkin_rule):
        """
        测试更新打卡规则成功 - 更新多个字段
        Given: 更新多个规则字段
        When: 调用 execute 方法
        Then: 成功更新所有字段
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id
        rule_data = {
            'rule_name': '新名称',
            'icon_url': 'https://example.com/icon.png',
            'frequency_type': 1,
            'custom_time': '09:00',
            'status': 0
        }

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, rule_data=rule_data)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        updated_rule = result.data['rule']
        assert updated_rule.rule_name == '新名称'
        assert updated_rule.icon_url == 'https://example.com/icon.png'
        assert updated_rule.frequency_type == 1
        assert updated_rule.custom_time == time(9, 0)
        assert updated_rule.status == 0


class TestDeleteCheckinRuleUseCase:
    """DeleteCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return DeleteCheckinRuleUseCase()

    @pytest.fixture
    def test_checkin_rule(self, test_session, test_user, test_community):
        """创建测试打卡规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="待删除规则",
            rule_type="personal",
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    def test_execute_success(self, use_case, test_user, test_checkin_rule):
        """
        测试删除打卡规则成功
        Given: 有效的规则ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，软删除规则
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "打卡规则删除成功" in result.message
        assert result.data['rule_id'] == rule_id

    def test_execute_missing_rule_id(self, use_case, test_user):
        """
        测试删除打卡规则失败 - 缺少规则ID
        Given: 规则ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = None
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则ID不能为空" in result.message

    def test_execute_rule_not_found(self, use_case, test_user):
        """
        测试删除打卡规则失败 - 规则不存在
        Given: 不存在的规则ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = 99999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡规则不存在" in result.message


class TestGetCheckinHistoryUseCase:
    """GetCheckinHistoryUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCheckinHistoryUseCase()

    @pytest.fixture
    def test_checkin_records(self, test_session, test_user, test_rule):
        """创建测试打卡记录"""
        records = []
        for i in range(5):
            record = CheckinRecord(
                user_id=test_user.user_id,
                rule_id=test_rule.rule_id,
                checkin_time=datetime.now(),
                planned_time=datetime.now(),
                status=1
            )
            test_session.add(record)
            test_session.flush()
            records.append(record)
        test_session.commit()
        return records

    def test_execute_success(self, use_case, test_user, test_checkin_records):
        """
        测试获取打卡历史成功
        Given: 有效的用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回打卡历史
        """
        # Arrange
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取打卡历史成功" in result.message
        assert 'history' in result.data
        assert result.data['total'] == 5

    def test_execute_missing_user_id(self, use_case):
        """
        测试获取打卡历史失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_with_pagination(self, use_case, test_user, test_checkin_records):
        """
        测试获取打卡历史成功 - 分页查询
        Given: 使用分页参数
        When: 调用 execute 方法
        Then: 返回分页后的数据
        """
        # Arrange
        user_id = test_user.user_id
        page = 1
        page_size = 2

        # Act
        result = use_case.execute(user_id=user_id, page=page, page_size=page_size)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert len(result.data['history']) == 2
        assert result.data['page'] == 1
        assert result.data['page_size'] == 2
        assert result.data['total_pages'] == 3

    def test_execute_with_date_range(self, use_case, test_user, test_checkin_records):
        """
        测试获取打卡历史成功 - 日期范围查询
        Given: 使用日期范围参数
        When: 调用 execute 方法
        Then: 返回指定日期范围内的数据
        """
        # Arrange
        user_id = test_user.user_id
        start_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Act
        result = use_case.execute(user_id=user_id, start_date=start_date, end_date=end_date)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data['total'] >= 5


class TestGetTodayCheckinsUseCase:
    """GetTodayCheckinsUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetTodayCheckinsUseCase()

    @pytest.fixture
    def test_checkin_rule_today(self, test_session, test_user, test_community):
        """创建今日需要打卡的规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="今日打卡规则",
            rule_type="personal",
            frequency_type=0,  # 每天
            time_slot_type=4,
            custom_time=time(8, 0),
            week_days=127,
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    def test_execute_success(self, use_case, test_user, test_checkin_rule_today):
        """
        测试获取今日打卡成功
        Given: 有效的用户ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，返回今日打卡事项
        """
        # Arrange
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取今日打卡成功" in result.message
        assert 'checkin_items' in result.data
        assert result.data['total'] >= 1

    def test_execute_missing_user_id(self, use_case):
        """
        测试获取今日打卡失败 - 缺少用户ID
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_user_not_found(self, use_case):
        """
        测试获取今日打卡失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 99999

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_with_checked_record(self, use_case, test_user, test_checkin_rule_today, test_session):
        """
        测试获取今日打卡成功 - 包含已打卡记录
        Given: 今天已经打过卡
        When: 调用 execute 方法
        Then: 返回包含已打卡状态的记录
        """
        # Arrange
        user_id = test_user.user_id

        # 先打一次卡
        perform_use_case = PerformCheckinUseCase()
        perform_use_case.execute(rule_id=test_checkin_rule_today.rule_id, user_id=user_id)

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        checkin_items = result.data['checkin_items']
        assert len(checkin_items) >= 1
        # 查找对应的打卡项
        checked_item = next((item for item in checkin_items if item['rule_id'] == test_checkin_rule_today.rule_id), None)
        assert checked_item is not None
        assert checked_item['status'] == 'checked'


class TestCancelCheckinUseCase:
    """CancelCheckinUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return CancelCheckinUseCase()

    @pytest.fixture
    def test_checkin_record(self, test_session, test_user, test_rule):
        """创建测试打卡记录（未打卡状态）"""
        record = CheckinRecord(
            user_id=test_user.user_id,
            rule_id=test_rule.rule_id,
            checkin_time=None,
            planned_time=datetime.now(),
            status=0  # 0=未打卡
        )
        test_session.add(record)
        test_session.commit()
        return record

    def test_execute_success(self, use_case, test_user, test_checkin_record):
        """
        测试取消打卡成功
        Given: 有效的记录ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，取消打卡
        """
        # Arrange
        record_id = test_checkin_record.record_id
        user_id = test_user.user_id
        reason = "测试取消"

        # Act
        result = use_case.execute(record_id=record_id, user_id=user_id, reason=reason)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "打卡取消成功" in result.message
        assert result.data['record_id'] == record_id

    def test_execute_missing_record_id(self, use_case, test_user):
        """
        测试取消打卡失败 - 缺少记录ID
        Given: 记录ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        record_id = None
        user_id = test_user.user_id

        # Act
        result = use_case.execute(record_id=record_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "打卡记录ID不能为空" in result.message

    def test_execute_record_not_found(self, use_case, test_user):
        """
        测试取消打卡失败 - 记录不存在
        Given: 不存在的记录ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        record_id = 99999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(record_id=record_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡记录不存在" in result.message


class TestReportMissCheckinUseCase:
    """ReportMissCheckinUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return ReportMissCheckinUseCase()

    @pytest.fixture
    def test_checkin_rule(self, test_session, test_user, test_community):
        """创建测试打卡规则"""
        rule = CheckinRule(
            user_id=test_user.user_id,
            community_id=test_community.community_id,
            rule_name="漏打卡测试规则",
            rule_type="personal",
            frequency_type=0,
            time_slot_type=4,
            custom_time=time(8, 0),
            week_days=127,
            status=1
        )
        test_session.add(rule)
        test_session.commit()
        return rule

    def test_execute_success(self, use_case, test_user, test_checkin_rule):
        """
        测试报告漏打卡成功
        Given: 有效的规则ID
        When: 调用 execute 方法
        Then: 返回 SUCCESS 状态，创建漏打卡记录
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id
        reason = "忘记打卡"

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id, reason=reason)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "漏打卡报告成功" in result.message
        assert 'record_id' in result.data
        assert result.data['status'] == 'missed'

    def test_execute_missing_rule_id(self, use_case, test_user):
        """
        测试报告漏打卡失败 - 缺少规则ID
        Given: 规则ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        rule_id = None
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "规则ID不能为空" in result.message

    def test_execute_rule_not_found(self, use_case, test_user):
        """
        测试报告漏打卡失败 - 规则不存在
        Given: 不存在的规则ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = 99999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡规则不存在" in result.message

    def test_execute_after_completed_checkin(self, use_case, test_user, test_checkin_rule):
        """
        测试报告漏打卡失败 - 已完成打卡
        Given: 今天已完成打卡
        When: 调用 execute 方法
        Then: 返回 BUSINESS_ERROR 状态
        """
        # Arrange
        rule_id = test_checkin_rule.rule_id
        user_id = test_user.user_id

        # 先完成打卡
        perform_use_case = PerformCheckinUseCase()
        perform_use_case.execute(rule_id=rule_id, user_id=user_id)

        # Act - 尝试报告漏打卡
        result = use_case.execute(rule_id=rule_id, user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.BUSINESS_ERROR
        assert "今日已完成打卡" in result.message


class TestGetCheckinRuleUseCase:
    """GetCheckinRuleUseCase 测试类"""

    @pytest.fixture
    def use_case(self, test_session):
        """创建 UseCase 实例"""
        return GetCheckinRuleUseCase()

    def test_execute_get_single_rule_success(self, use_case, test_user, test_rule):
        """
        测试获取单个打卡规则成功
        Given: 存在有效的用户和打卡规则
        When: 调用 execute 方法获取单个规则
        Then: 返回 SUCCESS 状态和规则数据
        """
        # Arrange
        rule_id = test_rule.rule_id
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id, rule_id=rule_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取打卡规则成功" in result.message
        assert result.data is not None
        assert 'rule' in result.data
        assert result.data['rule'].rule_id == rule_id

    def test_execute_get_all_rules_success(self, use_case, test_user, test_rule):
        """
        测试获取用户所有打卡规则成功
        Given: 存在有效的用户和打卡规则
        When: 调用 execute 方法获取所有规则
        Then: 返回 SUCCESS 状态和规则列表
        """
        # Arrange
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert "获取打卡规则成功" in result.message
        assert result.data is not None
        assert 'rules' in result.data
        assert len(result.data['rules']) >= 1

    def test_execute_missing_user_id(self, use_case):
        """
        测试获取打卡规则失败 - 用户ID为空
        Given: 用户ID为空
        When: 调用 execute 方法
        Then: 返回 VALIDATION_ERROR 状态
        """
        # Arrange
        user_id = None

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.VALIDATION_ERROR
        assert "用户ID不能为空" in result.message

    def test_execute_user_not_found(self, use_case):
        """
        测试获取打卡规则失败 - 用户不存在
        Given: 不存在的用户ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        user_id = 99999

        # Act
        result = use_case.execute(user_id=user_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "用户不存在" in result.message

    def test_execute_rule_not_found(self, use_case, test_user):
        """
        测试获取单个打卡规则失败 - 规则不存在
        Given: 不存在的规则ID
        When: 调用 execute 方法
        Then: 返回 NOT_FOUND 状态
        """
        # Arrange
        rule_id = 99999
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id, rule_id=rule_id)

        # Assert
        assert result.status == UseCaseStatus.NOT_FOUND
        assert "打卡规则不存在" in result.message

    def test_execute_permission_denied(self, use_case, test_user, test_session):
        """
        测试获取单个打卡规则失败 - 权限不足
        Given: 规则不属于当前用户
        When: 调用 execute 方法
        Then: 返回 FORBIDDEN 状态
        """
        # Arrange
        # 创建另一个用户和规则
        from database.flask_models import User, CheckinRule, Community
        other_user = User(
            phone_number='13900139000',
            name='其他用户',
            avatar_url='http://example.com/avatar.jpg',
            role=1,
            status=1
        )
        test_session.add(other_user)
        test_session.commit()

        community = Community(
            name='其他社区',
            description='其他社区描述',
            status=1
        )
        test_session.add(community)
        test_session.commit()

        other_rule = CheckinRule(
            user_id=other_user.user_id,
            community_id=community.community_id,
            rule_name='其他规则',
            rule_type='personal',
            frequency_type=0,
            time_slot_type=4,
            status=1
        )
        test_session.add(other_rule)
        test_session.commit()

        # 尝试用当前用户获取其他用户的规则
        rule_id = other_rule.rule_id
        user_id = test_user.user_id

        # Act
        result = use_case.execute(user_id=user_id, rule_id=rule_id)

        # Assert
        assert result.status == UseCaseStatus.FORBIDDEN
        assert "无权限查看此打卡规则" in result.message