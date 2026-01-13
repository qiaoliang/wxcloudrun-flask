"""
获取今日监护数据用例
"""
import logging
from datetime import datetime, date, time, timedelta

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetTodaySupervisionDataUseCase(BaseUseCase):
    """获取今日监护数据用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()

    def execute(
        self,
        supervisor_id: int,
        target_date: date = None
    ) -> UseCaseResult:
        """
        执行获取今日监护数据用例

        Args:
            supervisor_id: 监督者用户ID
            target_date: 目标日期（可选，默认为今天）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not supervisor_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='监督者ID不能为空'
                )

            # 如果没有指定日期，使用今天
            if target_date is None:
                target_date = date.today()

            # 2. 查询监督者的所有已激活监督关系
            relations = self.supervision_relation_repository.find_by_supervisor_id(supervisor_id)
            active_relations = [r for r in relations if r.status == 2]  # 2 = 已激活

            if not active_relations:
                self.logger.info(f'监督者 {supervisor_id} 没有激活的监督关系')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='没有激活的监督关系',
                    data={'supervised_users': []}
                )

            # 3. 按被监护人分组
            supervised_users_map = {}  # {solo_user_id: {user_info, rules: []}}
            
            for relation in active_relations:
                solo_user_id = relation.solo_user_id
                
                if solo_user_id not in supervised_users_map:
                    # 获取被监护人信息
                    supervised_user = self.user_repository.find_by_id(solo_user_id)
                    if not supervised_user:
                        continue
                    
                    supervised_users_map[solo_user_id] = {
                        'user_id': supervised_user.user_id,
                        'nickname': supervised_user.nickname,
                        'avatar_url': supervised_user.avatar_url,
                        'rules': []
                    }
                
                # 获取规则信息
                rule = self.checkin_rule_repository.find_by_id(relation.rule_id)
                if not rule:
                    continue
                
                # 计算今日打卡状态
                today_status = self._calculate_today_status(
                    rule_id=relation.rule_id,
                    solo_user_id=solo_user_id,
                    target_date=target_date
                )
                
                # 获取今日打卡记录时间
                checkin_record_time = None
                if today_status == 'completed':
                    checkin_record = self.checkin_record_repository.get_today_checkin(
                        user_id=solo_user_id,
                        rule_id=relation.rule_id,
                        target_date=target_date
                    )
                    if checkin_record and checkin_record.checkin_time:
                        checkin_record_time = checkin_record.checkin_time.strftime('%H:%M')
                
                supervised_users_map[solo_user_id]['rules'].append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'checkin_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                    'frequency': 'daily',  # 简化处理
                    'today_status': today_status,
                    'checkin_record_time': checkin_record_time,
                    'relation_id': relation.relation_id,
                    'reminder_template': '该打卡了'  # 默认模板
                })

            # 4. 转换为列表格式
            supervised_users = list(supervised_users_map.values())

            self.logger.info(f'获取今日监护数据成功: supervisor_id={supervisor_id}, supervised_count={len(supervised_users)}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取今日监护数据成功',
                data={
                    'supervised_users': supervised_users,
                    'date': target_date.isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f'获取今日监护数据失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取今日监护数据失败: {str(e)}'
            )

    def _calculate_today_status(
        self,
        rule_id: int,
        solo_user_id: int,
        target_date: date
    ) -> str:
        """
        计算今日打卡状态

        Args:
            rule_id: 规则ID
            solo_user_id: 被监护人用户ID
            target_date: 目标日期

        Returns:
            str: 状态（pending/completed/missed）
        """
        try:
            # 获取规则信息
            rule = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule:
                return 'pending'

            # 获取今日打卡记录
            checkin_record = self.checkin_record_repository.get_today_checkin(
                user_id=solo_user_id,
                rule_id=rule_id,
                target_date=target_date
            )

            if checkin_record and checkin_record.checkin_time:
                return 'completed'

            # 检查是否已错过
            current_time = datetime.now().time()
            checkin_time = rule.custom_time
            
            if checkin_time and current_time > checkin_time:
                return 'missed'

            return 'pending'

        except Exception as e:
            self.logger.error(f'计算今日打卡状态失败: {str(e)}', exc_info=True)
            return 'pending'