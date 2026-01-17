"""
解析监督邀请链接用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.supervision.get_user_by_id_use_case import GetUserByIdUseCase

app_logger = logging.getLogger('log')


class ResolveSupervisionInviteLinkUseCase(BaseUseCase):
    """解析监督邀请链接用例"""

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.get_user_use_case = GetUserByIdUseCase()

    def execute(self, invite_token: str) -> UseCaseResult:
        """
        执行解析监督邀请链接

        Args:
            invite_token: 邀请令牌

        Returns:
            UseCaseResult: 包含邀请信息的结果
        """
        try:
            if not invite_token:
                return UseCaseResult.fail('缺少token参数', status=UseCaseStatus.VALIDATION_ERROR)

            # 从数据库查询邀请信息
            relations = self.supervision_relation_repository.find_by_invite_token(
                invite_token=invite_token,
                status=1  # 1=待确认
            )

            if not relations:
                return UseCaseResult.fail('邀请链接不存在或已过期', status=UseCaseStatus.NOT_FOUND)

            # 检查邀请是否过期
            now = datetime.now()
            if relations[0].invite_expires_at and relations[0].invite_expires_at < now:
                return UseCaseResult.fail('邀请链接已过期', status=UseCaseStatus.BUSINESS_ERROR)

            # 获取被监督人信息
            solo_user_result = self.get_user_use_case.execute(user_id=relations[0].solo_user_id)
            if not solo_user_result.is_success:
                return UseCaseResult.fail('被监督人不存在', status=UseCaseStatus.NOT_FOUND)
            solo_user = solo_user_result.data

            # 获取规则信息
            rule_ids = [r.rule_id for r in relations]
            rules = self.checkin_rule_repository.find_by_ids(rule_ids)

            # 构建规则信息（返回第一个规则的详细信息）
            rule_info = None
            if rules:
                rule = rules[0]
                rule_info = {
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'rule_type': rule.rule_type,
                    'checkin_time': rule.custom_time.strftime('%H:%M:%S') if rule.custom_time else '灵活时间',
                    'frequency': 'daily' if rule.frequency_type == 0 else 'weekly'
                }

            # 构建邀请人信息
            inviter_info = {
                'user_id': solo_user.user_id,
                'nickname': solo_user.nickname or '未知用户',
                'phone_number': solo_user.phone_number,
                'avatar_url': solo_user.avatar_url or ''
            }

            # 构建返回数据
            invite_data = {
                'relation_id': relations[0].relation_id,
                'rule_info': rule_info,
                'inviter_info': inviter_info,
                'expires_at': relations[0].invite_expires_at.isoformat() if relations[0].invite_expires_at else None,
                'is_expired': relations[0].invite_expires_at and relations[0].invite_expires_at < now,
                'is_already_supervisor': False  # 需要在实际应用中检查当前用户是否已经是监督人
            }

            return UseCaseResult.success(data=invite_data)

        except Exception as e:
            app_logger.error(f'解析邀请链接失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'解析邀请链接失败: {str(e)}')
