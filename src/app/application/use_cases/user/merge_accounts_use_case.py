"""
合并账号用例
"""
import logging
from typing import Optional

from database.flask_models import User

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class MergeAccountsUseCase(BaseUseCase):
    """合并账号用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(self, account1: User, account2: User) -> UseCaseResult:
        """
        执行合并账号用例

        Args:
            account1: 第一个用户账号
            account2: 第二个用户账号

        Returns:
            UseCaseResult: 执行结果，包含合并后的用户数据
        """
        try:
            # 1. 参数验证
            if not account1 or not account2:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='账号不能为空'
                )

            if account1.user_id == account2.user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='不能合并同一个账号'
                )

            # 2. 确定主账号（保留较早注册的账号）
            if account1.created_at < account2.created_at:
                primary, secondary = account1, account2
            else:
                primary, secondary = account2, account1

            self.logger.info(f'开始合并账号: primary={primary.user_id}, secondary={secondary.user_id}')

            # 3. 迁移用户信息
            # 只有当主账号没有该信息时，才从次要账号迁移
            if secondary.wechat_openid and not primary.wechat_openid:
                primary.wechat_openid = secondary.wechat_openid
                self.logger.info(f'迁移 wechat_openid: {secondary.wechat_openid[:20]}...')

            if secondary.phone_number and not primary.phone_number:
                primary.phone_number = secondary.phone_number
                self.logger.info(f'迁移 phone_number: {secondary.phone_number}')

            if secondary.nickname and not primary.nickname:
                primary.nickname = secondary.nickname
                self.logger.info(f'迁移 nickname: {secondary.nickname}')

            if secondary.avatar_url and not primary.avatar_url:
                primary.avatar_url = secondary.avatar_url
                self.logger.info(f'迁移 avatar_url')

            if secondary.name and not primary.name:
                primary.name = secondary.name
                self.logger.info(f'迁移 name: {secondary.name}')

            # 4. 迁移监督关系（被监督者）
            supervision_relations = self.supervision_relation_repository.find_by_solo_user_id(
                secondary.user_id
            )

            migrated_count = 0
            for relation in supervision_relations:
                # 检查主账号是否已经有相同的监督关系
                existing_relation = self.supervision_relation_repository.find_by_users_and_rule(
                    supervisor_id=relation.supervisor_user_id,
                    solo_user_id=primary.user_id,
                    rule_id=relation.rule_id
                )

                if not existing_relation:
                    # 迁移关系：将被监督者ID改为主账号ID
                    relation.solo_user_id = primary.user_id
                    self.supervision_relation_repository.update(relation)
                    migrated_count += 1
                    self.logger.info(f'迁移监督关系: supervisor={relation.supervisor_user_id}, rule={relation.rule_id}')
                else:
                    # 删除重复的关系
                    self.supervision_relation_repository.delete(relation.relation_id)
                    self.logger.info(f'删除重复监督关系: relation_id={relation.relation_id}')

            self.logger.info(f'监督关系迁移完成: 迁移{migrated_count}条，删除{len(supervision_relations) - migrated_count}条')

            # 5. 保存主账号更新
            self.user_repository.save(primary)

            # 6. 删除次要账号（在删除前保存user_id）
            secondary_user_id = secondary.user_id
            self.user_repository.delete(secondary)
            self.logger.info(f'删除次要账号: user_id={secondary_user_id}')

            # 7. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='账号合并成功',
                data={
                    'primary_user_id': primary.user_id,
                    'secondary_user_id': secondary_user_id,
                    'migrated_supervision_count': migrated_count
                }
            )

        except Exception as e:
            self.logger.error(f'合并账号失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'合并账号失败: {str(e)}'
            )