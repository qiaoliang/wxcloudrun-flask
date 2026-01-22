"""
获取被监督用户列表用例

修订：增加规则详情，按用户分组返回
"""
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from collections import defaultdict

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class GetSupervisedUsersUseCase(BaseUseCase):
    """获取被监督用户列表用例"""

    # 监督关系状态常量
    STATUS_ACTIVE = 2  # 已激活
    
    # 规则状态常量
    RULE_STATUS_ACTIVE = 1  # 启用
    RULE_STATUS_INACTIVE = 0  # 停用

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

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
            UseCaseResult: 执行结果，包含按用户分组的规则详情
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

            # 2. 查询监督关系（只查询已激活的关系）
            relations = self.supervision_relation_repository.find_by_supervisor_id(supervisor_id)
            active_relations = [
                r for r in relations 
                if r.status == self.STATUS_ACTIVE
            ]

            # 3. 按用户分组，获取规则详情
            user_rules_map = defaultdict(list)
            user_info_map = {}

            for relation in active_relations:
                # 获取规则信息
                rule = self.checkin_rule_repository.find_by_id(relation.rule_id)
                
                # 跳过无效规则（已删除或停用）
                if not rule:
                    self.logger.warning(f'规则不存在: rule_id={relation.rule_id}')
                    continue
                
                if rule.status != self.RULE_STATUS_ACTIVE:
                    self.logger.info(f'规则未启用，跳过: rule_id={relation.rule_id}, status={rule.status}')
                    continue

                # 获取被监护人信息
                solo_user = self.user_repository.find_by_id(relation.solo_user_id)
                if not solo_user:
                    self.logger.warning(f'被监护人不存在: solo_user_id={relation.solo_user_id}')
                    continue

                # 保存用户信息
                if relation.solo_user_id not in user_info_map:
                    user_info_map[relation.solo_user_id] = {
                        'user_id': solo_user.user_id,
                        'nickname': solo_user.nickname,
                        'avatar_url': solo_user.avatar_url
                    }

                # 添加规则详情
                user_rules_map[relation.solo_user_id].append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'rule_icon': rule.icon_url or '📋',
                    'created_at': rule.created_at.isoformat() if rule.created_at else None
                })

            # 4. 构造响应数据（按用户分组）
            supervised_users = []
            for user_id, rules in user_rules_map.items():
                user_info = user_info_map.get(user_id, {})
                supervised_users.append({
                    'user_id': user_id,
                    'nickname': user_info.get('nickname', ''),
                    'avatar_url': user_info.get('avatar_url', ''),
                    'rules': rules,
                    'rules_count': len(rules)
                })

            # 5. 分页处理
            total = len(supervised_users)
            start = (page - 1) * page_size
            end = start + page_size
            paged_users = supervised_users[start:end]

            self.logger.info(
                f'获取被监督用户列表成功: supervisor_id={supervisor_id}, '
                f'total={total}, page={page}, page_size={page_size}'
            )

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取被监督用户列表成功',
                data={
                    'supervised_users': paged_users,
                    'total': total,
                    'page': page,
                    'per_page': page_size,
                    'total_pages': (total + page_size - 1) // page_size if total > 0 else 0
                }
            )

        except Exception as e:
            self.logger.error(f'获取被监督用户列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取被监督用户列表失败: {str(e)}'
            )