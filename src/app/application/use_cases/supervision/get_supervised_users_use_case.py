"""
获取被监督用户列表用例
"""
import logging
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetSupervisedUsersUseCase(BaseUseCase):
    """获取被监督用户列表用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(
        self,
        supervisor_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> UseCaseResult:
        """
        执行获取被监督用户列表用例

        Args:
            supervisor_id: 监督者用户ID
            page: 页码
            page_size: 每页数量

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

            # 2. 查询监督关系
            relations = self.supervision_relation_repository.find_by_supervisor_id(supervisor_id)

            # 3. 构造响应数据
            supervised_users = []
            for relation in relations:
                supervised_user = self.user_repository.find_by_id(relation.solo_user_id)
                if supervised_user:
                    supervised_users.append({
                        'user_id': supervised_user.user_id,
                        'nickname': supervised_user.nickname,
                        'avatar_url': supervised_user.avatar_url,
                        'rule_id': relation.rule_id,
                        'status': 'active'
                    })

            # 4. 分页处理
            total = len(supervised_users)
            start = (page - 1) * page_size
            end = start + page_size
            paged_users = supervised_users[start:end]

            self.logger.info(f'获取被监督用户列表成功: supervisor_id={supervisor_id}, total={total}')

            # 5. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取被监督用户列表成功',
                data={
                    'supervised_users': paged_users,
                    'total': total,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total + page_size - 1) // page_size
                }
            )

        except Exception as e:
            self.logger.error(f'获取被监督用户列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取被监督用户列表失败: {str(e)}'
            )
