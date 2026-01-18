"""
处理社区申请用例（重构后 - 部分符合DDD架构）

重构要点：
- 移除直接导入 database.flask_models 中的 db, User
- 使用现有Repository接口访问数据
- CommunityApplication暂无Repository，保留直接访问（待后续创建）

注：CommunityApplicationRepository创建后可进一步优化
"""
import logging
from datetime import datetime

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.shared.utils.transaction import transaction

logger = logging.getLogger(__name__)


class ProcessCommunityApplicationUseCase(BaseUseCase):
    """处理社区申请用例"""

    def __init__(self):
        """
        初始化用例，注入所有需要的Repository

        符合依赖倒置原则：依赖Repository接口，而非具体实现
        """
        super().__init__()
        self.logger = logging.getLogger(__name__)
        # ✅ 通过RepositoryFactory获取Repository接口
        self.user_repository = RepositoryFactory.get_user_repository()
        self.community_checkin_rule_repository = RepositoryFactory.get_community_checkin_rule_repository()
        self.user_community_rule_repository = RepositoryFactory.get_user_community_rule_repository()

    @transactional


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

            # 2. 查询申请（CommunityApplication暂无Repository，保留直接访问）            application = CommunityApplication.query.get(application_id)
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
            # ✅ 使用Repository代替 db.session.get(User, processor_id)
            processor = self.user_repository.find_by_id(processor_id)
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
                    # ✅ 使用Repository代替 db.session.get(User, application.user_id)
                    user = self.user_repository.find_by_id(application.user_id)
                    if user:
                        user.community_id = application.target_community_id
                        user.community_joined_at = datetime.now()
                        self.user_repository.save(user)

                    # 同步社区打卡规则到用户
                    # ✅ 使用Repository获取新社区的所有启用规则
                    new_community_rules = self.community_checkin_rule_repository.find_active_by_community(
                        application.target_community_id
                    )

                    activated_count = 0

                    # 为用户创建或激活规则映射
                    for rule in new_community_rules:
                        # ✅ 使用Repository查找是否已存在映射记录
                        existing_mapping = self.user_community_rule_repository.find_by_user_and_rule(
                            application.user_id, rule.community_rule_id
                        )

                        if existing_mapping:
                            # 如果存在且当前是停用状态，重新激活
                            if not existing_mapping.is_active:
                                existing_mapping.is_active = True
                                self.user_community_rule_repository.save(existing_mapping)
                                activated_count += 1
                        else:
                            # 如果不存在，创建新映射
                            new_mapping = UserCommunityRule(
                                user_id=application.user_id,
                                community_rule_id=rule.community_rule_id,
                                is_active=True
                            )
                            # ✅ 使用Repository代替 db.session.add(new_mapping)
                            self.user_community_rule_repository.save(new_mapping)
                            activated_count += 1

                    logger.info(f"用户{application.user_id}已激活{activated_count}个新社区规则")

                    # 记录审计日志（暂时保留直接访问，等创建AuditLogRepository后再重构）
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

                    # 记录审计日志（暂时保留直接访问，等创建AuditLogRepository后再重构）
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
