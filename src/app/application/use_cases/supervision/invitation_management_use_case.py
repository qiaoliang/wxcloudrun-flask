"""
邀请管理用例

处理邀请列表查询、接受、拒绝、忽略和批量接受逻辑
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import SupervisionRuleRelation
from app.domain.repositories.supervision_relation_repository import SupervisionRelationRepository


class InvitationManagementUseCase(BaseUseCase):
    """邀请管理用例"""

    # 邀请状态常量
    STATUS_PENDING = 1  # 待处理
    STATUS_ACCEPTED = 2  # 已接受
    STATUS_REJECTED = 3  # 已拒绝
    STATUS_EXPIRED = 4  # 已过期

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()

    def get_invitations(
        self,
        user_id: int,
        page: int = 1,
        limit: int = 10,
        status: Optional[int] = None
    ) -> UseCaseResult:
        """
        获取用户收到的邀请列表

        Args:
            user_id: 用户ID
            page: 页码（默认1）
            limit: 每页数量（默认10）
            status: 状态筛选（可选，值：1=待处理，2=已接受，3=已拒绝，4=已过期）

        Returns:
            UseCaseResult: 执行结果，包含邀请列表和分页信息
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if page < 1:
                page = 1
            if limit < 1 or limit > 100:
                limit = 10

            # 2. 查询邀请列表
            # 注意：邀请是发送给监督者（supervisor_user_id）的
            query = db.session.query(SupervisionRuleRelation).filter(
                SupervisionRuleRelation.supervisor_user_id == user_id
            )

            # 3. 状态筛选
            if status is not None:
                query = query.filter(SupervisionRuleRelation.status == status)
            else:
                # 默认不显示已拒绝的邀请
                query = query.filter(SupervisionRuleRelation.status != self.STATUS_REJECTED)

            # 4. 排序：按创建时间倒序（最新的在前）
            query = query.order_by(db.desc(SupervisionRuleRelation.created_at))

            # 5. 分页
            total = query.count()
            offset = (page - 1) * limit
            invitations = query.offset(offset).limit(limit).all()

            # 6. 转换为响应格式
            invitation_list = []
            for invitation in invitations:
                # 获取被监护人信息（邀请人）
                solo_user = self.user_repository.find_by_id(invitation.solo_user_id)
                if not solo_user:
                    continue

                # 获取规则信息
                rule = self.checkin_rule_repository.find_by_id(invitation.rule_id)
                if not rule:
                    continue

                # 检查是否过期
                is_expired = False
                if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                    is_expired = True

                invitation_list.append({
                    'relation_id': invitation.relation_id,
                    'rule_info': {
                        'rule_id': rule.rule_id,
                        'rule_name': rule.rule_name,
                        'checkin_time': rule.custom_time.strftime('%H:%M') if rule.custom_time else None,
                        'frequency': 'daily'  # 简化处理
                    },
                    'inviter_info': {
                        'user_id': solo_user.user_id,
                        'nickname': solo_user.nickname,
                        'avatar_url': solo_user.avatar_url,
                        'community_name': solo_user.community.name if solo_user.community else None
                    },
                    'invitation_type': invitation.invitation_type or 'link',
                    'status': invitation.status,
                    'message': invitation.message,
                    'created_at': invitation.created_at.isoformat() if invitation.created_at else None,
                    'expires_at': invitation.invite_expires_at.isoformat() if invitation.invite_expires_at else None,
                    'is_expired': is_expired
                })

            # 7. 计算总页数
            total_pages = (total + limit - 1) // limit if total > 0 else 0

            self.logger.info(f'获取邀请列表成功: user_id={user_id}, count={len(invitation_list)}, total={total}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取邀请列表成功',
                data={
                    'invitations': invitation_list,
                    'total': total,
                    'page': page,
                    'limit': limit,
                    'total_pages': total_pages
                }
            )

        except Exception as e:
            self.logger.error(f'获取邀请列表失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取邀请列表失败: {str(e)}'
            )

    def accept_invitation(self, invitation_id: int, user_id: int) -> UseCaseResult:
        """
        接受邀请

        Args:
            invitation_id: 邀请ID（关系ID）
            user_id: 当前用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not invitation_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查找并验证邀请
            invitation = self.supervision_relation_repository.find_by_id(invitation_id)
            if not invitation:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='邀请不存在'
                )

            # 3. 验证权限
            if invitation.supervisor_user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='您不是该邀请的监督人'
                )

            # 4. 验证状态
            if invitation.status == self.STATUS_ACCEPTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='您已经接受过该邀请'
                )

            if invitation.status == self.STATUS_REJECTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='您已经拒绝过该邀请'
                )

            if invitation.status != self.STATUS_PENDING:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请状态异常，无法接受'
                )

            # 5. 验证是否过期
            if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已过期，请联系邀请人重新生成'
                )

            # 6. 更新邀请状态为已接受
            invitation.status = self.STATUS_ACCEPTED
            self.supervision_relation_repository.update(invitation)

            # 7. 激活监督关系
            self._activate_supervision_relation(invitation)

            self.logger.info(f'接受邀请成功: invitation_id={invitation_id}, user_id={user_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='已接受邀请',
                data={
                    'relation_id': invitation.relation_id,
                    'status': invitation.status
                }
            )

        except Exception as e:
            self.logger.error(f'接受邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'接受邀请失败: {str(e)}'
            )

    def reject_invitation(self, invitation_id: int, user_id: int, reason: Optional[str] = None) -> UseCaseResult:
        """
        拒绝邀请

        Args:
            invitation_id: 邀请ID（关系ID）
            user_id: 当前用户ID
            reason: 拒绝原因（可选）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not invitation_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查找并验证邀请
            invitation = self.supervision_relation_repository.find_by_id(invitation_id)
            if not invitation:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='邀请不存在'
                )

            # 3. 验证权限
            if invitation.supervisor_user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='您不是该邀请的监督人'
                )

            # 4. 验证状态
            if invitation.status == self.STATUS_REJECTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已拒绝，无法再次拒绝'
                )

            if invitation.status == self.STATUS_ACCEPTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已接受，无法拒绝'
                )

            if invitation.status != self.STATUS_PENDING:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请状态异常，无法拒绝'
                )

            # 5. 验证是否过期
            if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已过期，无法拒绝'
                )

            # 6. 更新邀请状态为已拒绝
            invitation.status = self.STATUS_REJECTED
            self.supervision_relation_repository.update(invitation)

            # 7. 通知邀请人已拒绝邀请
            self._notify_rejection(invitation, reason)

            self.logger.info(f'拒绝邀请成功: invitation_id={invitation_id}, user_id={user_id}, reason={reason}')

            # 8. 构建响应消息
            message = '已拒绝邀请'
            if reason:
                message = f'已拒绝邀请({reason})'

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message=message,
                data={
                    'relation_id': invitation.relation_id,
                    'status': invitation.status,
                    'reason': reason
                }
            )

        except Exception as e:
            self.logger.error(f'拒绝邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'拒绝邀请失败: {str(e)}'
            )

    def ignore_invitation(self, invitation_id: int, user_id: int) -> UseCaseResult:
        """
        忽略邀请（删除邀请记录）

        Args:
            invitation_id: 邀请ID（关系ID）
            user_id: 当前用户ID

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not invitation_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请ID不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            # 2. 查找并验证邀请
            invitation = self.supervision_relation_repository.find_by_id(invitation_id)
            if not invitation:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='邀请不存在'
                )

            # 3. 验证权限
            if invitation.supervisor_user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='您不是该邀请的监督人'
                )

            # 4. 验证状态
            if invitation.status == self.STATUS_ACCEPTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已接受，无法忽略'
                )

            if invitation.status == self.STATUS_REJECTED:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已拒绝，无法忽略'
                )

            if invitation.status != self.STATUS_PENDING:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请状态异常，无法忽略'
                )

            # 5. 验证是否过期
            if invitation.invite_expires_at and invitation.invite_expires_at < datetime.now():
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message='邀请已过期，无法忽略'
                )

            # 6. 删除邀请记录
            success = self.supervision_relation_repository.delete(invitation_id)
            if not success:
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='删除邀请失败'
                )

            self.logger.info(f'忽略邀请成功: invitation_id={invitation_id}, user_id={user_id}')

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='已忽略邀请',
                data={
                    'relation_id': invitation_id
                }
            )

        except Exception as e:
            self.logger.error(f'忽略邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'忽略邀请失败: {str(e)}'
            )

    def batch_accept_invitations(self, invitation_ids: List[int], user_id: int) -> UseCaseResult:
        """
        批量接受邀请

        Args:
            invitation_ids: 邀请ID列表
            user_id: 当前用户ID

        Returns:
            UseCaseResult: 执行结果，包含成功和失败数量
        """
        try:
            # 1. 参数验证
            if not invitation_ids:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请ID列表不能为空'
                )

            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if not isinstance(invitation_ids, list):
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='邀请ID列表格式错误'
                )

            # 2. 去重
            invitation_ids = list(set(invitation_ids))

            # 3. 批量接受邀请
            accepted_count = 0
            failed_count = 0
            failed_ids = []

            for invitation_id in invitation_ids:
                try:
                    result = self.accept_invitation(invitation_id, user_id)
                    if result.is_success:
                        accepted_count += 1
                    else:
                        failed_count += 1
                        failed_ids.append(invitation_id)
                except Exception as e:
                    self.logger.error(f'批量接受邀请失败: invitation_id={invitation_id}, error={str(e)}')
                    failed_count += 1
                    failed_ids.append(invitation_id)

            self.logger.info(
                f'批量接受邀请完成: user_id={user_id}, '
                f'total={len(invitation_ids)}, accepted={accepted_count}, failed={failed_count}'
            )

            # 4. 构建响应消息
            if accepted_count == 0:
                message = '所有邀请接受失败'
            elif failed_count == 0:
                message = f'成功接受 {accepted_count} 个邀请'
            else:
                message = f'批量操作完成：成功 {accepted_count} 个，失败 {failed_count} 个'

            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message=message,
                data={
                    'accepted_count': accepted_count,
                    'failed_count': failed_count,
                    'total_count': len(invitation_ids),
                    'failed_ids': failed_ids
                }
            )

        except Exception as e:
            self.logger.error(f'批量接受邀请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'批量接受邀请失败: {str(e)}'
            )

    def _activate_supervision_relation(self, invitation: SupervisionRuleRelation) -> None:
        """
        激活监督关系

        Args:
            invitation: 邀请对象
        """
        # 监督关系在创建时状态已经是待确认（status=1）
        # 接受邀请后，状态更新为已激活（status=2）
        # 这个逻辑已经在 accept_invitation 中处理
        self.logger.info(
            f'激活监督关系: relation_id={invitation.relation_id}, '
            f'supervisor={invitation.supervisor_user_id}, solo={invitation.solo_user_id}'
        )

    def _notify_rejection(self, invitation: SupervisionRuleRelation, reason: Optional[str]) -> None:
        """
        通知邀请人已拒绝邀请

        Args:
            invitation: 邀请对象
            reason: 拒绝原因
        """
        # 获取邀请人信息
        inviter = self.user_repository.find_by_id(invitation.solo_user_id)
        if not inviter:
            self.logger.warning(f'无法通知邀请人：邀请人不存在, solo_user_id={invitation.solo_user_id}')
            return

        # 获取监督人信息
        supervisor = self.user_repository.find_by_id(invitation.supervisor_user_id)
        if not supervisor:
            self.logger.warning(f'无法通知邀请人：监督人不存在, supervisor_user_id={invitation.supervisor_user_id}')
            return

        # 获取规则信息
        rule = self.checkin_rule_repository.find_by_id(invitation.rule_id)
        rule_name = rule.rule_name if rule else '未知规则'

        # TODO: 实现通知逻辑（站内消息、推送等）
        # 这里只记录日志，实际通知功能需要额外的通知服务
        message = f'{supervisor.nickname} 拒绝了您监督 {rule_name} 的邀请'
        if reason:
            message += f'，原因：{reason}'

        self.logger.info(
            f'通知邀请人已拒绝: inviter={inviter.nickname}, '
            f'supervisor={supervisor.nickname}, rule={rule_name}, reason={reason}'
        )

        # 实际实现中，这里应该调用通知服务发送站内消息
        # 例如：
        # from app.infrastructure.notifications.notification_service import NotificationService
        # notification_service = NotificationService()
        # notification_service.send_notification(
        #     user_id=inviter.user_id,
        #     message=message,
        #     type='invitation_rejected'
        # )
