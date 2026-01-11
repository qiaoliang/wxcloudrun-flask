"""
获取监督记录用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetSupervisionRecordsUseCase(BaseUseCase):
    """获取监督记录用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(
        self,
        user_id: int,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行获取监督记录用例

        Args:
            user_id: 用户ID
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            page: 页码
            page_size: 每页数量

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if page < 1:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='页码必须大于0'
                )

            if page_size < 1 or page_size > 100:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='每页数量必须在1-100之间'
                )

            # 2. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查询监督关系
            relations = self.supervision_relation_repository.find_by_supervisor_id(user_id)
            if not relations:
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='获取监督记录成功',
                    data={
                        'records': [],
                        'total': 0,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': 0
                    }
                )

            # 4. 查询打卡记录
            records = []
            for relation in relations:
                supervised_user = self.user_repository.find_by_id(relation.solo_user_id)
                rule = self.checkin_rule_repository.find_by_id(relation.rule_id)
                
                # 查询该规则的打卡记录
                checkin_records = self.checkin_record_repository.find_by_rule_id(relation.rule_id)
                
                for record in checkin_records:
                    if record.user_id == relation.solo_user_id:
                        # 日期过滤
                        if start_date and record.planned_time < datetime.strptime(start_date, '%Y-%m-%d'):
                            continue
                        if end_date and record.planned_time > datetime.strptime(end_date, '%Y-%m-%d'):
                            continue

                        records.append({
                            'record_id': record.record_id,
                            'supervisor_id': user_id,
                            'supervisor_nickname': user.nickname,
                            'supervised_id': supervised_user.user_id if supervised_user else None,
                            'supervised_nickname': supervised_user.nickname if supervised_user else None,
                            'rule_id': relation.rule_id,
                            'rule_name': rule.rule_name if rule else None,
                            'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                            'status': 'completed' if record.status == 1 else 'pending',
                            'created_at': record.created_at.isoformat() if record.created_at else None
                        })

            # 5. 分页处理
            total = len(records)
            start = (page - 1) * page_size
            end = start + page_size
            paged_records = records[start:end]

            self.logger.info(f'获取监督记录成功: user_id={user_id}, total={total}')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取监督记录成功',
                data={
                    'records': paged_records,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            )

        except Exception as e:
            self.logger.error(f'获取监督记录失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取监督记录失败: {str(e)}'
            )
