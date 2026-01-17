"""
发送提醒用例
"""
import logging
from datetime import datetime
from typing import Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.supervision.get_user_by_id_use_case import GetUserByIdUseCase
from app.application.use_cases.supervision.get_checkin_rule_by_id_use_case import GetCheckinRuleByIdUseCase

app_logger = logging.getLogger('log')


class SendReminderUseCase(BaseUseCase):
    """发送提醒用例"""

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.get_user_use_case = GetUserByIdUseCase()
        self.get_rule_use_case = GetCheckinRuleByIdUseCase()

    def execute(
        self,
        user_id: int,
        supervised_user_id: int,
        rule_id: int,
        template_type: str = 'default',
        template_content: str = ''
    ) -> UseCaseResult:
        """
        执行发送提醒

        Args:
            user_id: 操作用户ID（监督人）
            supervised_user_id: 被监护人ID
            rule_id: 规则ID
            template_type: 模板类型
            template_content: 自定义模板内容

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 验证监督关系
            relation = self.supervision_relation_repository.find_active_relation(
                supervisor_user_id=user_id,
                solo_user_id=supervised_user_id,
                rule_id=rule_id
            )

            if not relation:
                return UseCaseResult.fail('监督关系不存在或未激活', status=UseCaseStatus.FORBIDDEN)

            # 获取被监护人信息
            supervised_user_result = self.get_user_use_case.execute(user_id=supervised_user_id)
            if not supervised_user_result.is_success:
                return UseCaseResult.fail('被监护人不存在', status=UseCaseStatus.NOT_FOUND)

            supervised_user = supervised_user_result.data
            if not supervised_user.wechat_openid:
                return UseCaseResult.fail('被监护人未绑定微信', status=UseCaseStatus.BUSINESS_ERROR)

            # 获取规则信息
            rule_result = self.get_rule_use_case.execute(rule_id=rule_id)
            if not rule_result.is_success:
                return UseCaseResult.fail('打卡规则不存在', status=UseCaseStatus.NOT_FOUND)
            rule = rule_result.data

            # 获取模板内容
            if template_type == 'custom' and template_content:
                message_content = template_content
            else:
                # 使用默认模板
                default_templates = {
                    'default': '该打卡了',
                    'remember': '记得吃药',
                    'wake_up': '该起床了',
                    'sleep': '该睡觉了'
                }
                message_content = default_templates.get(template_type, '该打卡了')

            # TODO: 调用微信模板消息接口发送通知
            # 这里先返回成功，实际项目中需要集成微信 API
            app_logger.info(f'用户 {user_id} 向用户 {supervised_user_id} 发送提醒: {message_content}')

            # 记录提醒发送日志（可选）
            # 可以创建一个 ReminderLog 表来记录所有提醒发送记录

            return UseCaseResult.success(data={
                'message_id': f'msg_{datetime.now().strftime("%Y%m%d%H%M%S")}',
                'sent_at': datetime.now().isoformat()
            })

        except Exception as e:
            app_logger.error(f'发送提醒失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'发送提醒失败: {str(e)}')
