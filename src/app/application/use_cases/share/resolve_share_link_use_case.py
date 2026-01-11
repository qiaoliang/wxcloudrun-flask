"""
解析分享链接用例
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import ShareLinkAccessLog


class ResolveShareLinkUseCase(BaseUseCase):
    """解析分享链接用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.share_link_repository = RepositoryFactory.get_share_link_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.share_link_access_log_repository = RepositoryFactory.get_share_link_access_log_repository()

    def execute(
        self,
        token: str,
        ip_address: str = None,
        user_agent: str = None
    ) -> UseCaseResult:
        """
        执行解析分享链接用例

        Args:
            token: 分享链接token
            ip_address: 访问者IP地址
            user_agent: 用户代理字符串

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

            # 7. 构造响应数据
            rule_info = {
                'rule_id': rule.rule_id,
                'title': rule.rule_name,
                'description': '',
                'checkin_time': rule.custom_time.strftime('%H:%M:%S') if rule.custom_time else None,
                'repeat_days': rule.week_days,
                'is_enabled': rule.status == 1
            }

            share_info = {
                'share_user_id': user.user_id,
                'share_user_nickname': user.nickname,
                'share_user_avatar': user.avatar_url,
                'created_at': link.created_at.isoformat() if link.created_at else None,
                'expires_at': link.expires_at.isoformat() if link.expires_at else None
            }

            self.logger.info(f'解析分享链接成功: token={token}')

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='解析分享链接成功',
                data={
                    'rule_info': rule_info,
                    'share_info': share_info
                }
            )

        except Exception as e:
            self.logger.error(f'解析分享链接失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'解析分享链接失败: {str(e)}'
            )
