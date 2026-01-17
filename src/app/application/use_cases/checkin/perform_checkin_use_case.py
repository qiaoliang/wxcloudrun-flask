"""
执行打卡用例(重构版 - 符合DDD架构)

重构要点:
- 移除对 database.flask_models 的直接导入
- 使用仓储接口返回的领域实体
- 通过聚合根封装业务逻辑
- 符合依赖倒置原则
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.infrastructure.transaction.transaction_manager import transaction
from app.domain.entities.checkin_rule_entity import CheckinRuleEntity
from app.domain.entities.checkin_record_entity import CheckinRecordEntity
from app.domain.aggregates.checkin_rule_aggregate import CheckinRuleAggregate


class PerformCheckinUseCase(BaseUseCase):
    """执行打卡用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # 通过仓储工厂获取仓储接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    @transaction
    def execute(
        self,
        rule_id: int,
        user_id: int,
        rule_source: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行打卡用例

        事务边界: 查询规则 -> 验证权限 -> 创建记录 -> 保存, 所有操作在同一事务中

        Args:
            rule_id: 规则ID
            user_id: 用户ID
            rule_source: 规则来源

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查找打卡规则实体
            rule_entity = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule_entity:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 4. 验证规则归属
            if rule_entity.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限操作此打卡规则'
                )

            # 5. 检查今天是否已有打卡记录
            today = datetime.now().date()
            today_records = self.checkin_record_repository.find_today_records(user_id, rule_id)

            # 查找当天已有的打卡记录
            for record in today_records:
                if record.is_completed:
                    return UseCaseResult(
                        status=UseCaseStatus.BUSINESS_ERROR,
                        message='今日该事项已打卡,请勿重复打卡'
                    )

            # 6. 记录打卡时间
            checkin_time = datetime.now()

            # 7. 检查是否有未打卡状态的记录可以更新
            existing_unchecked = None
            for record in today_records:
                if not record.is_completed and not record.is_missed and not record.is_cancelled:
                    existing_unchecked = record
                    break

            if existing_unchecked:
                # 更新已有记录
                existing_unchecked.complete(checkin_time)
                updated_record = self.checkin_record_repository.update_entity(existing_unchecked)
            else:
                # 创建新的打卡记录实体
                planned_time = rule_entity.calculate_planned_checkin_time()
                if not planned_time:
                    planned_time = checkin_time

                new_record = CheckinRecordEntity.create(
                    record_id=0,  # 将由数据库生成
                    rule_id=rule_id,
                    user_id=user_id,
                    planned_checkin_time=datetime.combine(today, planned_time.time())
                )
                new_record.complete(checkin_time)
                updated_record = self.checkin_record_repository.save_entity(new_record)

            # 8. 发布领域事件
            try:
                # 创建聚合根
                aggregate = CheckinRuleAggregate(rule_entity)
                aggregate.complete_checkin(updated_record.record_id, checkin_time)
                self.logger.info(f'发布打卡完成事件: record_id={updated_record.record_id}')
            except Exception as e:
                self.logger.warning(f'发布领域事件失败(不影响打卡结果): {str(e)}')

            self.logger.info(f'执行打卡成功: rule_id={rule_id}, user_id={user_id}, record_id={updated_record.record_id}')

            # 9. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='打卡成功',
                data={
                    'rule_id': rule_id,
                    'record_id': updated_record.record_id,
                    'user_id': updated_record.user_id,
                    'checkin_time': updated_record.actual_checkin_time.isoformat() if updated_record.actual_checkin_time else None,
                    'status': 'completed'
                }
            )

        except ValueError as e:
            self.logger.error(f'执行打卡失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.BUSINESS_ERROR,
                message=str(e)
            )
        except Exception as e:
            self.logger.error(f'执行打卡失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'执行打卡失败: {str(e)}'
            )