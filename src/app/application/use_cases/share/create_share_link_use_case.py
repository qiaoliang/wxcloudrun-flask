"""
from app.shared.utils.transaction import transactional
创建分享链接用例
"""
import logging
import os
from datetime import datetime, timedelta

from app.application.use_cases.base import BaseUseCase, UseCaseStatus, UseCaseResult
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import ShareLink
import secrets
import qrcode


class CreateShareLinkUseCase(BaseUseCase):
    """创建分享链接用例"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.user_repository = RepositoryFactory.get_user_repository()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.share_link_repository = RepositoryFactory.get_share_link_repository()
        self.qrcode_dir = 'static/qrcodes'

    @transactional


    def execute(
        self,
        user_id: int,
        rule_id: int,
        expire_hours: int = 168
    ) -> UseCaseResult:
        """
        执行创建分享链接用例

        Args:
            user_id: 用户ID
            rule_id: 打卡规则ID
            expire_hours: 过期小时数（默认168小时=7天）

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            # 1. 参数验证
            if not user_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='用户ID不能为空'
                )

            if not rule_id:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='规则ID不能为空'
                )

            if expire_hours < 1 or expire_hours > 720:  # 最多30天
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message='过期时间必须在1-720小时之间'
                )

            # 2. 查询用户
            user = self.user_repository.find_by_id(user_id)
            if not user:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='用户不存在'
                )

            # 3. 查询打卡规则
            rule = self.checkin_rule_repository.find_by_id(rule_id)
            if not rule:
                return UseCaseResult(
                    status=UseCaseStatus.NOT_FOUND,
                    message='打卡规则不存在'
                )

            # 4. 验证规则归属
            if rule.user_id != user_id:
                return UseCaseResult(
                    status=UseCaseStatus.FORBIDDEN,
                    message='无权限操作此打卡规则'
                )

            # 5. 生成分享token（64位安全随机字符串）
            token = secrets.token_urlsafe(64)
            expires_at = datetime.now() + timedelta(hours=expire_hours)

            # 6. 创建分享链接
            share_link = ShareLink(
                token=token,
                solo_user_id=user_id,
                rule_id=rule_id,
                expires_at=expires_at
            )

            saved_link = self.share_link_repository.save(share_link)

            # 7. 生成二维码图片
            qrcode_url = self._generate_qrcode(token)

            self.logger.info(f'创建分享链接成功: user_id={user_id}, rule_id={rule_id}, token={token}')

            # 8. 返回结果
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='分享链接创建成功',
                data={
                    'token': saved_link.token,
                    'rule_id': saved_link.rule_id,
                    'user_id': saved_link.solo_user_id,
                    'expires_at': saved_link.expires_at.isoformat() if saved_link.expires_at else None,
                    'qrcode_url': qrcode_url
                }
            )

        except Exception as e:
            self.logger.error(f'创建分享链接失败: {str(e)}', exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'创建分享链接失败: {str(e)}'
            )

    def _generate_qrcode(self, token: str) -> str:
        """
        生成二维码图片并保存

        Args:
            token: 分享token

        Returns:
            str: 二维码图片URL
        """
        try:
            # 确保目录存在
            os.makedirs(self.qrcode_dir, exist_ok=True)

            # 构建分享链接URL
            # 注意：这里使用相对路径，实际URL会在路由层构建
            share_url = f"/share/checkin?token={token}"

            # 创建二维码
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(share_url)
            qr.make(fit=True)

            # 生成图片
            img = qr.make_image(fill_color="black", back_color="white")

            # 保存到文件
            filename = f"{token}.png"
            filepath = os.path.join(self.qrcode_dir, filename)
            img.save(filepath)

            # 返回URL路径
            return f"/static/qrcodes/{filename}"

        except Exception as e:
            self.logger.error(f'生成二维码失败: {str(e)}', exc_info=True)
            raise
