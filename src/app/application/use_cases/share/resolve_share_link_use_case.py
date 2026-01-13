"""
解析分享链接用例
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import ShareLinkAccessLog, SupervisionRuleRelation


class ResolveShareLinkUseCase(BaseUseCase):
    """解析分享链接用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.share_link_repository = RepositoryFactory.get_share_link_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.share_link_access_log_repository = RepositoryFactory.get_share_link_access_log_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    def execute(
        self,
        token: str,
        ip_address: str = None,
        user_agent: str = None,
        current_user_id: int = None
    ) -> UseCaseResult:
        """
        执行解析分享链接用例

        Args:
            token: 分享链接token
            ip_address: 访问者IP地址
            user_agent: 用户代理字符串
            current_user_id: 当前登录用户ID（可选）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not token:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='token不能为空'
                )

            # 2. 查询分享链接
            link = self.share_link_repository.find_by_token(token)
            if not link:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='分享链接不存在'
                )

            # 3. 检查链接是否过期
            if link.expires_at < datetime.now():
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='分享链接已过期'
                )

            # 4. 记录访问日志
            if ip_address or user_agent:
                access_log = ShareLinkAccessLog(
                    token=token,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    accessed_at=datetime.now()
                )
                self.share_link_access_log_repository.save(access_log)

            # 5. 获取规则信息
            rule = self.checkin_rule_repository.find_by_id(link.rule_id)
            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='关联的打卡规则不存在'
                )

            # 6. 获取用户信息
            user = self.user_repository.find_by_id(link.solo_user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='分享用户不存在'
                )

            # 7. 检查用户是否已经是监督人（如果提供了当前用户ID）
            is_already_supervisor = False
            if current_user_id:
                existing_relation = self.supervision_relation_repository.find_active_relation(
                    supervisor_user_id=current_user_id,
                    solo_user_id=link.solo_user_id,
                    rule_id=link.rule_id
                )
                is_already_supervisor = existing_relation is not None

            # 8. 构造响应数据
            rule_info = {
                'rule_id': rule.rule_id,
                'rule_name': rule.rule_name,
                'description': '',
                'checkin_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                'frequency': 'daily',  # 简化处理，实际应根据 rule.frequency_type 判断
                'is_enabled': rule.status == 1
            }

            inviter_info = {
                'user_id': user.user_id,
                'nickname': user.nickname,
                'avatar_url': user.avatar_url
            }

            self.logger.info(f'解析分享链接成功: token={token}')

            # 9. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='解析分享链接成功',
                data={
                    'rule_info': rule_info,
                    'inviter_info': inviter_info,
                    'is_expired': False,
                    'is_already_supervisor': is_already_supervisor
                }
            )

        except Exception as e:
            self.logger.error(f'解析分享链接失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'解析分享链接失败: {str(e)}'
            )
