"""
获取打卡历史用例
"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetCheckinHistoryUseCase(BaseUseCase):
    """获取打卡历史用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.user_repository = RepositoryFactory.get_user_repository()

    def execute(
        self,
        user_id: int,
        rule_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行获取打卡历史用例

        Args:
            user_id: 用户ID
            rule_id: 规则ID（可选）
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
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

            # 2. 验证用户是否存在
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 处理日期参数
            start_datetime = None
            end_datetime = None

            if start_date:
                try:
                    start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
                except ValueError:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='开始日期格式无效，应为 YYYY-MM-DD'
                    )

            if end_date:
                try:
                    end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                except ValueError:
                    return UseCaseResult(
                        status=UseCaseStatus.VALIDATION_ERROR,
                        message='结束日期格式无效，应为 YYYY-MM-DD'
                    )

            # 4. 查询打卡记录
            if rule_id:
                records = self.checkin_record_repository.find_by_rule_id(rule_id)
            else:
                records = self.checkin_record_repository.find_by_user_id(user_id)

            # 5. 筛选日期范围
            if start_datetime:
                records = [r for r in records if r.checkin_time and r.checkin_time >= start_datetime]

            if end_datetime:
                records = [r for r in records if r.checkin_time and r.checkin_time < end_datetime]

            # 6. 按时间倒序排列
            records.sort(key=lambda x: x.checkin_time if x.checkin_time else datetime.min, reverse=True)

            # 7. 分页处理
            total = len(records)
            start = (page - 1) * page_size
            end = start + page_size
            paged_records = records[start:end]

            # 8. 构造响应数据
            record_list = []
            for record in paged_records:
                # 根据 checkin_status 确定 status_name
                status_map = {0: '未打卡', 1: '已打卡', 2: '已错过', 3: '已取消'}
                status_name = status_map.get(record.checkin_status, '未知')

                record_list.append({
                    'record_id': record.record_id,
                    'user_id': record.user_id,
                    'rule_id': record.rule_id,
                    'checkin_time': record.checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.checkin_time else None,
                    'status': record.checkin_status,
                    'status_name': status_name,
                    'planned_time': record.planned_checkin_time.strftime('%Y-%m-%d %H:%M:%S') if record.planned_checkin_time else None
                })

            response_data = {
                'history': record_list,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }

            self.logger.info(f'获取打卡历史成功: user_id={user_id}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取打卡历史成功',
                data=response_data
            )

        except Exception as e:
            self.logger.error(f'获取打卡历史失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取打卡历史失败: {str(e)}'
            )