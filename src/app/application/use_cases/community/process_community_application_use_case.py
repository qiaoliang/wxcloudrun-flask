"""
处理社区申请用例
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from database.flask_models import db, User, CommunityApplication, UserAuditLog
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class ProcessCommunityApplicationUseCase(BaseUseCase):
    """处理社区申请用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def execute(
        self,
        application_id: int,
        approve: bool,
        processor_id: int,
        rejection_reason: str = None
    ) -> UseCaseResult:
        """
        执行处理社区申请用例

        Args:
            application_id: 申请ID
            approve: 是否批准
            processor_id: 处理者用户ID
            rejection_reason: 拒绝理由（仅在拒绝时需要）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not application_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='申请ID不能为空'
                )

            if not processor_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='处理者ID不能为空'
                )

            # 2. 查询申请
            application = db.session.get(CommunityApplication, application_id)
            if not application:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='申请不存在'
                )

            # 3. 检查申请状态
            if application.status != 1:  # 不是待审核状态
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='申请已被处理'
                )

            # 4. 验证处理者存在
            processor = db.session.get(User, processor_id)
            if not processor:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='处理者用户不存在'
                )

            # 5. 处理申请
            with transaction():
                if approve:
                    # 批准申请
                    application.status = 2  # 已批准
                    application.processed_by = processor_id
                    application.updated_at = datetime.now()

                    # 将用户加入社区
                    user = db.session.get(User, application.user_id)
                    if user:
                        user.community_id = application.target_community_id

                    # 同步社区打卡规则到用户
                    from wxcloudrun.community_staff_service import CommunityStaffService
                    CommunityStaffService._activate_new_community_rules(
                        application.user_id,
                        application.target_community_id
                    )

                    # 记录审计日志
                    audit_log = UserAuditLog(
                        user_id=processor_id,
                        action="approve_community_application",
                        detail=f"批准社区申请: 申请ID={application_id}, 用户ID={application.user_id}"
                    )
                    db.session.add(audit_log)

                    logger.info(f"社区申请批准: 申请ID={application_id}")

                    return UseCaseResult(
                        status=UseCaseStatus.SUCCESS,
                        message='批准成功',
                        data={
                            'application_id': application_id,
                            'status': 'approved'
                        }
                    )
                else:
                    # 拒绝申请
                    if not rejection_reason:
                        return UseCaseResult(
                            status=UseCaseStatus.VALIDATION_ERROR,
                            message='拒绝申请必须提供理由'
                        )

                    application.status = 3  # 已拒绝
                    application.rejection_reason = rejection_reason
                    application.processed_by = processor_id
                    application.updated_at = datetime.now()

                    # 记录审计日志
                    audit_log = UserAuditLog(
                        user_id=processor_id,
                        action="reject_community_application",
                        detail=f"拒绝社区申请: 申请ID={application_id}, 理由={rejection_reason}"
                    )
                    db.session.add(audit_log)

                    logger.info(f"社区申请拒绝: 申请ID={application_id}, 理由={rejection_reason}")

                    return UseCaseResult(
                        status=UseCaseStatus.SUCCESS,
                        message='拒绝成功',
                        data={
                            'application_id': application_id,
                            'status': 'rejected',
                            'rejection_reason': rejection_reason
                        }
                    )

        except ValueError as e:
            logger.error(f'处理社区申请失败: {str(e)}')
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=str(e)
            )
        except Exception as e:
            logger.error(f'处理社区申请失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'处理失败: {str(e)}'
            )