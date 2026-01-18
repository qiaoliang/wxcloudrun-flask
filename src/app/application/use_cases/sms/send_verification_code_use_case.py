"""
发送验证码用例
"""
from datetime import datetime, timedelta
from flask import current_app
from wxcloudrun.sms_service import create_sms_provider, generate_code
from wxcloudrun.utils.validators import _code_expiry_minutes, normalize_phone_number, _hash_code
from config import should_use_real_sms
from app.shared.utils.transaction import transaction
from app.application.use_cases.base import BaseUseCase, UseCaseResult, UseCaseStatus
from app.domain.repositories.verification_code_repository import VerificationCodeRepository
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from database.flask_models import VerificationCode
import secrets


class SendVerificationCodeUseCase(BaseUseCase):
    """发送验证码用例"""

    def __init__(self):
        super().__init__()
        self.verification_code_repo = RepositoryFactory.get_verification_code_repository()

    def _validate(self, phone: str, purpose: str = 'register') -> UseCaseResult:
        """
        验证输入参数

        Args:
            phone: 手机号码
            purpose: 验证码用途（register/login等）

        Returns:
            UseCaseResult: 验证结果
        """
        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        # 在 mock 环境下跳过频率限制
        is_mock_env = not should_use_real_sms()

        now = datetime.now()
        vc = self.verification_code_repo.find_by_phone_and_purpose(
            normalized_phone, purpose
        )

        # 只在非 mock 环境下检查频率限制
        if not is_mock_env and vc and (now - vc.last_sent_at).total_seconds() < 60:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='请求过于频繁，请稍后再试'
            )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    @transactional


    def _execute(self, phone: str, purpose: str = 'register') -> UseCaseResult:
        """
        执行发送验证码操作

        Args:
            phone: 手机号码
            purpose: 验证码用途（register/login等）

        Returns:
            UseCaseResult: 执行结果
        """
        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)

        # 在 mock 环境下跳过频率限制
        is_mock_env = not should_use_real_sms()

        now = datetime.now()
        vc = self.verification_code_repo.find_by_phone_and_purpose(
            normalized_phone, purpose
        )

        code = generate_code(6)
        salt = secrets.token_hex(8)

        # 使用验证工具函数生成哈希
        code_hash = _hash_code(normalized_phone, code, salt)

        # 使用事务管理器确保数据一致性
        with transaction():
            if vc:
                # 更新现有记录
                vc.code_hash = code_hash
                vc.salt = salt
                vc.expires_at = now + timedelta(minutes=_code_expiry_minutes())
                vc.last_sent_at = now
                vc.updated_at = now
                self.verification_code_repo.save(vc)
            else:
                # 创建新记录
                new_vc = VerificationCode(
                    phone_number=normalized_phone,
                    purpose=purpose,
                    code_hash=code_hash,
                    salt=salt,
                    expires_at=now + timedelta(minutes=_code_expiry_minutes()),
                    last_sent_at=now
                )
                self.verification_code_repo.save(new_vc)

        # 发送短信
        if is_mock_env:
            current_app.logger.info(f'Mock环境：验证码已生成，手机号：{normalized_phone}，验证码：{code}')
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='验证码发送成功（测试环境）',
                data={
                    'message': '验证码发送成功（测试环境）',
                    'code': code  # 仅在测试环境返回验证码
                }
            )
        else:
            # 生产环境发送真实短信
            provider = create_sms_provider()
            success = provider.send_verification_code(normalized_phone, code)

            if success:
                current_app.logger.info(f'验证码发送成功，手机号：{normalized_phone}')
                return UseCaseResult(
                    status=UseCaseStatus.SUCCESS,
                    message='验证码发送成功',
                    data={
                        'message': '验证码发送成功'
                    }
                )
            else:
                current_app.logger.error(f'验证码发送失败，手机号：{normalized_phone}')
                return UseCaseResult(
                    status=UseCaseStatus.FAILURE,
                    message='验证码发送失败'
                )