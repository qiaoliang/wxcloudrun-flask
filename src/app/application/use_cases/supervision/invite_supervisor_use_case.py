"""
from app.shared.utils.transaction import transactional
邀请监督者用例
"""
import logging
from typing import List, Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import SupervisionRuleRelation


class InviteSupervisorUseCase(BaseUseCase):
    """邀请监督者用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    @transactional


    def execute(
        self,
        inviter_id: int,
        target_user_id: int,
        rule_ids: Optional[List[int]] = None
    ) -> UseCaseResult:
        """
        执行邀请监督者用例

        Args:
            inviter_id: 邀请者用户ID
            target_user_id: 目标用户ID
            rule_ids: 要监督的规则ID列表，空表示监督所有规则

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not inviter_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请者ID不能为空'
                )

            if not target_user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='目标用户ID不能为空'
                )

            # 2. 查询邀请者
            inviter = self.user_repository.find_by_id(inviter_id)
            if not inviter:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='邀请者不存在'
                )

            # 3. 查询目标用户
            target_user = self.user_repository.find_by_id(target_user_id)
            if not target_user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='目标用户不存在'
                )

            # 4. 检查规则是否都属于邀请者
            if rule_ids:
                for rule_id in rule_ids:
                    rule = self.checkin_rule_repository.find_by_id(rule_id)
                    if not rule:
                        return UseCaseResult(
                            status=UseCaseStatus.NOT_FOUND,
                            message=f'规则ID {rule_id} 不存在'
                        )
                    if rule.user_id != inviter_id:
                        return UseCaseResult(
                            status=UseCaseStatus.FORBIDDEN,
                            message=f'无权限操作规则ID {rule_id}'
                        )

            # 5. 创建监督关系
            relations = []
            if rule_ids:
                # 监督指定规则
                for rule_id in rule_ids:
                    # 检查是否已存在相同的监督关系
                    existing = self.supervision_relation_repository.find_by_users_and_rule(
                        inviter_id, target_user_id, rule_id
                    )
                    if existing:
                        continue  # 跳过已存在的关系

                    relation = SupervisionRuleRelation(
                        solo_user_id=target_user_id,
                        supervisor_user_id=inviter_id,
                        rule_id=rule_id,
                        status=1
                    )
                    saved_relation = self.supervision_relation_repository.save(relation)
                    relations.append(saved_relation)
            else:
                # 监督所有规则
                all_rules = self.checkin_rule_repository.find_by_user_id(inviter_id)
                for rule in all_rules:
                    # 检查是否已存在相同的监督关系
                    existing = self.supervision_relation_repository.find_by_users_and_rule(
                        inviter_id, target_user_id, rule.rule_id
                    )
                    if existing:
                        continue  # 跳过已存在的关系

                    relation = SupervisionRuleRelation(
                        solo_user_id=target_user_id,
                        supervisor_user_id=inviter_id,
                        rule_id=rule.rule_id,
                        status=1
                    )
                    saved_relation = self.supervision_relation_repository.save(relation)
                    relations.append(saved_relation)

            self.logger.info(f'用户 {inviter_id} 成功邀请用户 {target_user_id} 监督，共 {len(relations)} 个规则')

            # 6. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='邀请发送成功',
                data={
                    'message': '邀请发送成功',
                    'relations_count': len(relations),
                    'relations': [
                        {
                            'relation_id': r.relation_id,
                            'rule_id': r.rule_id,
                            'supervisor_user_id': r.supervisor_user_id,
                            'solo_user_id': r.solo_user_id
                        } for r in relations
                    ]
                }
            )

        except Exception as e:
            self.logger.error(f'邀请监督者失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'邀请失败: {str(e)}'
            )
