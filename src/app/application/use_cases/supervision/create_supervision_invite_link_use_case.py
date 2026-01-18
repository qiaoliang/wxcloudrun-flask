"""
创建监督邀请链接用例
"""
import logging
import secrets
import os
import qrcode
from datetime import datetime, timedelta
from typing import List, Optional

from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.supervision.get_checkin_rule_by_id_use_case import GetCheckinRuleByIdUseCase

app_logger = logging.getLogger('log')


class CreateSupervisionInviteLinkUseCase(BaseUseCase):
    """创建监督邀请链接用例"""

    def __init__(self):
        super().__init__()
        self.supervision_relation_repository = RepositoryFactory.get_supervision_relation_repository()
        self.get_checkin_rule_use_case = GetCheckinRuleByIdUseCase()

    @transactional


    def execute(self, user_id: int, rule_ids: List[int], expire_hours: int = 24) -> UseCaseResult:
        """
        执行创建监督邀请链接

        Args:
            user_id: 用户ID
            rule_ids: 规则ID列表
            expire_hours: 过期小时数，默认24小时

        Returns:
            UseCaseResult: 包含邀请链接信息的结果
        """
        try:
            if not rule_ids:
                return UseCaseResult.fail('缺少rule_ids参数', status=UseCaseStatus.VALIDATION_ERROR)

            # 生成邀请token
            invite_token = secrets.token_urlsafe(32)
            expires_at = datetime.now() + timedelta(hours=expire_hours)

            # 生成二维码
            qrcode_dir = 'static/supervision_qrcodes'
            os.makedirs(qrcode_dir, exist_ok=True)

            # 构建小程序路径
            mini_path = f"/pages/supervisor-invite/supervisor-invite?token={invite_token}"

            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(mini_path)
            qr.make(fit=True)

            # 生成图片
            img = qr.make_image(fill_color="black", back_color="white")

            # 保存到文件
            filename = f"{invite_token}.png"
            filepath = os.path.join(qrcode_dir, filename)
            img.save(filepath)

            # 构建二维码URL
            qrcode_url = f"/static/supervision_qrcodes/{filename}"

            # 为每个规则创建监督关系记录
            from database.flask_models import SupervisionRuleRelation

            created_count = 0
            for rule_id in rule_ids:
                # 检查规则是否存在且属于当前用户
                rule_result = self.get_checkin_rule_use_case.execute(rule_id=rule_id)
                if not rule_result.is_success:
                    app_logger.warning(f'规则 {rule_id} 不存在')
                    continue

                rule = rule_result.data
                if rule.user_id != user_id:
                    app_logger.warning(f'规则 {rule_id} 不属于用户 {user_id}')
                    continue

                # 创建监督关系记录（状态为1=待确认）
                relation = SupervisionRuleRelation(
                    solo_user_id=user_id,
                    supervisor_user_id=user_id,  # 暂时设置为发起人，等待监督人接受后更新
                    rule_id=rule_id,
                    status=1,  # 1=待确认
                    invite_token=invite_token,
                    invite_expires_at=expires_at
                )
                self.supervision_relation_repository.save(relation)
                created_count += 1

            if created_count == 0:
                return UseCaseResult.fail('没有有效的规则可以创建邀请', status=UseCaseStatus.BUSINESS_ERROR)

            invite_data = {
                'token': invite_token,
                'url': qrcode_url,
                'mini_path': mini_path,
                'expire_at': expires_at.isoformat(),
                'created_count': created_count
            }

            return UseCaseResult.success(data=invite_data)

        except Exception as e:
            app_logger.error(f'创建邀请链接失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'创建邀请链接失败: {str(e)}')
