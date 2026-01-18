"""
from app.shared.utils.transaction import transactional
站内邀请监督者用例
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import SupervisionRuleRelation


class SendInternalInvitationUseCase(BaseUseCase):
    """站内邀请监督者用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()

    @transactional


    def execute(
        self,
        sender_id: int,
        rule_id: int,
        receiver_ids: List[int],
        message: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行站内邀请监督者用例

        Args:
            sender_id: 发出邀请用户ID（规则所有者）
            rule_id: 打卡规则ID
            receiver_ids: 被邀请用户ID列表（最多3个）
            message: 邀请消息（可选）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            validation_result = self._validate_parameters(sender_id, rule_id, receiver_ids)
            if not validation_result.is_success:
                return validation_result

            # 2. 验证权限和业务规则
            validation_result = self._validate_business_rules(sender_id, rule_id, receiver_ids)
            if not validation_result.is_success:
                return validation_result

            # 3. 查询邀请者
            sender = self.user_repository.find_by_id(sender_id)
            if not sender:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='邀请者不存在'
                )

            # 4. 查询规则
            rule = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='规则不存在'
                )

            # 5. 验证操作者是否是规则所有者
            if rule.user_id != sender_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='您不是该规则的所有者'
                )

            # 6. 创建监督关系记录
            relation_ids = []
            expires_at = datetime.now() + timedelta(days=30)

            for receiver_id in receiver_ids:
                # 检查是否已存在相同的邀请
                # 注意：find_by_users_and_rule的参数顺序是(supervisor_id, solo_user_id, rule_id)
                # 在站内邀请中：supervisor_user_id=receiver_id（被邀请者），solo_user_id=sender_id（邀请发起者）
                existing = self.supervision_relation_repository.find_by_users_and_rule(
                    receiver_id, sender_id, rule_id
                )
                if existing:
                    # 如果已存在邀请，跳过
                    continue

                # 创建监督关系记录
                relation = SupervisionRuleRelation(
                    solo_user_id=sender_id,  # 邀请发起者是被监督人
                    supervisor_user_id=receiver_id,  # 被邀请者是监督人
                    rule_id=rule_id,
                    status=1,  # 1=待处理
                    invitation_type='internal',
                    message=message,
                    invite_expires_at=expires_at
                )

                saved_relation = self.supervision_relation_repository.save(relation)
                relation_ids.append(saved_relation.relation_id)

            # 7. 发送站内消息通知
            self._send_internal_notifications(sender, rule, receiver_ids)

            self.logger.info(
                f'用户 {sender_id} 成功向 {len(receiver_ids)} 个用户发送站内邀请，'
                f'规则ID: {rule_id}，创建关系数量: {len(relation_ids)}'
            )

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='邀请已发送',
                data={
                    'sender_id': sender_id,
                    'receiver_ids': receiver_ids,
                    'rule_id': rule_id,
                    'relation_ids': relation_ids,
                    'invitation_type': 'internal',
                    'status': 1,
                    'expires_at': expires_at.isoformat()
                }
            )

        except Exception as e:
            self.logger.error(f'站内邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'邀请失败: {str(e)}'
            )

    def _validate_parameters(
        self,
        sender_id: int,
        rule_id: int,
        receiver_ids: List[int]
    ) -> UseCaseResult:
        """
        验证输入参数

        Args:
            sender_id: 发出邀请用户ID
            rule_id: 打卡规则ID
            receiver_ids: 被邀请用户ID列表

        Returns:
            UseCaseResult: 验证结果
        """
        if not sender_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='邀请者ID不能为空'
            )

        if not rule_id:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='规则ID不能为空'
            )

        if not receiver_ids or len(receiver_ids) == 0:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='被邀请用户ID列表不能为空'
            )

        if len(receiver_ids) > 3:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='一次最多只能邀请3个用户'
            )

        # 检查是否有重复的接收者ID
        if len(receiver_ids) != len(set(receiver_ids)):
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='被邀请用户ID列表中有重复'
            )

        # 检查是否邀请自己
        if sender_id in receiver_ids:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='不能邀请自己'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='参数验证通过'
        )

    def _validate_business_rules(
        self,
        sender_id: int,
        rule_id: int,
        receiver_ids: List[int]
    ) -> UseCaseResult:
        """
        验证业务规则

        Args:
            sender_id: 发出邀请用户ID
            rule_id: 打卡规则ID
            receiver_ids: 被邀请用户ID列表

        Returns:
            UseCaseResult: 验证结果
        """
        # 验证所有目标用户是否存在
        for receiver_id in receiver_ids:
            receiver = self.user_repository.find_by_id(receiver_id)
            if not receiver:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message=f'用户ID {receiver_id} 不存在'
                )

            # 检查目标用户是否已经是该规则的监督人
            existing_relation = self.supervision_relation_repository.find_active_relation(
                supervisor_user_id=receiver_id,
                solo_user_id=sender_id,
                rule_id=rule_id
            )
            if existing_relation:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=f'用户ID {receiver_id} 已经是该规则的监督人'
                )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='业务规则验证通过'
        )

    def _send_internal_notifications(
        self,
        sender,
        rule,
        receiver_ids: List[int]
    ) -> None:
        """
        发送站内消息通知

        Args:
            sender: 邀请者用户对象
            rule: 规则对象
            receiver_ids: 被邀请用户ID列表
        """
        # TODO: 实现站内消息通知
        # 这里需要调用站内消息服务发送通知
        # 消息内容："[站内] {邀请人昵称}邀请您监督{规则名称}"
        # 目前先记录日志，后续实现消息通知功能

        notification_content = f"[站内] {sender.nickname or '用户'}邀请您监督{rule.rule_name}"

        for receiver_id in receiver_ids:
            self.logger.info(
                f'发送站内邀请通知: 接收者ID={receiver_id}, '
                f'内容="{notification_content}"'
            )

            # TODO: 实际发送站内消息
            # 示例代码（需要根据实际的站内消息实现调整）:
            # from app.infrastructure.persistence.repository_factory import RepositoryFactory
            # notification_service = RepositoryFactory.get_notification_service()
            # notification_service.send_notification(
            #     receiver_id=receiver_id,
            #     content=notification_content,
            #     type='supervision_invitation',
            #     data={
            #         'sender_id': sender.user_id,
            #         'sender_nickname': sender.nickname,
            #         'rule_id': rule.rule_id,
            #         'rule_name': rule.rule_name
            #     }
            # )
