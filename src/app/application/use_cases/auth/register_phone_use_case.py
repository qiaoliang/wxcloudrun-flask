"""
手机号注册用例
处理用户通过手机号注册的业务逻辑
"""

from typing import Optional
from sqlalchemy.orm import joinedload

from app.shared.utils.transaction import transactional
from app.shared.utils.auth_helpers import (
    normalize_and_hash_phone
)
from wxcloudrun.utils.validators import (
    normalize_phone_number,
    _mask_phone_number,
    _gen_phone_nickname,
    generate_phone_hash
)
from app.application.use_cases.base import BaseUseCase, UseCaseResult
from app.domain.repositories.user_repository import UserRepository
from app.infrastructure.persistence.repository_factory import RepositoryFactory


class RegisterPhoneUseCase(BaseUseCase):
    """手机号注册用例"""

    def __init__(self):
        super().__init__()
        import logging
        self.logger = logging.getLogger(__name__)
        self.PWD_SALT = "default_salt"  # 应该从配置中读取
        self.user_repository = RepositoryFactory.get_user_repository()

    def _pwd_hash(self, pwd: str) -> str:
        """密码哈希"""
        import hashlib
        from hashlib import sha256
        import secrets
        PWD_SALT = secrets.token_hex(8)
        return sha256(f"{pwd}:{PWD_SALT}".encode('utf-8')).hexdigest()

    def execute(
        self,
        phone: str,
        code: str,
        nickname: Optional[str] = None,
        avatar_url: Optional[str] = None,
        password: Optional[str] = None
    ) -> UseCaseResult:
        """
        执行手机号注册

        Args:
            phone: 手机号
            code: 验证码
            nickname: 昵称
            avatar_url: 头像URL
            password: 密码（可选）

        Returns:
            UseCaseResult: 包含用户信息和token的结果
        """
        try:
            # 验证验证码
            from wxcloudrun.utils.validators import _verify_sms_code
            normalized_phone, phone_hash = normalize_and_hash_phone(phone, self.logger)

            if not _verify_sms_code(normalized_phone, 'register', code):
                return UseCaseResult.fail('验证码错误')

            # 验证密码强度
            if password:
                pwd = str(password)
                if len(pwd) < 8 or (not any(c.isalpha() for c in pwd)) or (not any(c.isdigit() for c in pwd)):
                    return UseCaseResult.fail('密码强度不足')

            # 检查手机号是否已注册
            existing = self._query_user_by_phone_hash(phone_hash)
            if existing:
                self.logger.info(f'手机号已注册，提示用户直接登录: {phone}')
                return UseCaseResult.fail('该手机号已注册，请直接登录')

            # 创建新用户
            user = self._create_user(
                normalized_phone=normalized_phone,
                phone_hash=phone_hash,
                nickname=nickname,
                avatar_url=avatar_url,
                password=password
            )

            # 生成token
            from .generate_auth_tokens_use_case import GenerateAuthTokensUseCase
            generate_tokens_use_case = GenerateAuthTokensUseCase()
            tokens_result = generate_tokens_use_case.execute(user)

            if not tokens_result.is_success:
                return UseCaseResult.fail('生成token失败')

            token = tokens_result.data['token']
            refresh_token = tokens_result.data['refresh_token']

            # 记录审计日志
            self._audit_user(user.user_id, 'register_phone', {'phone': normalized_phone})

            # 返回结果
            response_data = self._format_login_response(
                user=user,
                token=token,
                refresh_token=refresh_token,
                is_new_user=True
            )

            return UseCaseResult.success(response_data)

        except Exception as e:
            self.logger.error(f'手机号注册失败: {str(e)}', exc_info=True)
            return UseCaseResult.fail(f'注册失败: {str(e)}')

    @transactional
    def _query_user_by_phone_hash(self, phone_hash: str):
        """根据手机号哈希查询用户"""
        try:
            user = self.user_repository.find_by_phone_hash_with_community(phone_hash)
            if user:
                self.logger.info(
                    f"query_user_by_phone_hash: user_id={user.user_id}, "
                    f"community_id={user.community_id}, phone_number={user.phone_number}"
                )
            return user
        except Exception as e:
            self.logger.info(f"query_user_by_phone_hash errorMsg= {e}")
            return None

    @transactional
    def _create_user(
        self,
        normalized_phone: str,
        phone_hash: str,
        nickname: Optional[str],
        avatar_url: Optional[str],
        password: Optional[str]
    ):
        """创建新用户（在事务中执行）"""
        # 生成脱敏号码用于显示
        masked = normalized_phone[:3] + '****' + normalized_phone[-4:] if len(normalized_phone) >= 7 else normalized_phone
        self.logger.info(f"Creating user with masked phone: {masked} (phone_hash will be used for uniqueness)")

        nick = nickname or _gen_phone_nickname()

        # 默认头像 URL
        DEFAULT_AVATAR_URL = 'https://www.helloimg.com/i/2026/01/23/69737caaeb57a.png'
        final_avatar_url = avatar_url or DEFAULT_AVATAR_URL

        # 如果没有提供密码，使用默认密码 F00000000（用于邀请链接注册的用户）
        default_password = password if password else 'F00000000'

        # 导入 User 模型和默认社区ID
        from database.flask_models import User
        from const_default import DEFAULT_COMMUNITY_ID

        # 创建用户对象
        user = User(
            phone_number=masked,  # 存储脱敏号码
            phone_hash=phone_hash,  # 哈希值使用原始号码
            nickname=nick,
            avatar_url=final_avatar_url,
            role=1,
            status=1,
            wechat_openid=None,
            password_hash=self._pwd_hash(default_password),
            password_salt=self.PWD_SALT,
            community_id=DEFAULT_COMMUNITY_ID  # 新用户自动加入默认社区（安卡大家庭）
        )

        # 使用 save 方法保存用户
        saved_user = self.user_repository.save(user)

        # 重新加载用户对象以获取关联的 community 数据
        # 因为 save 只做 flush，返回的对象不包含关联关系
        # 使用 find_by_id 来获取预加载了 community 的完整对象
        reloaded_user = self.user_repository.find_by_id(saved_user.user_id)

        if not reloaded_user:
            self.logger.error(f"无法重新加载用户: user_id={saved_user.user_id}")
            return saved_user

        # 验证 community 关联是否正确加载
        if reloaded_user.community_id:
            if reloaded_user.community:
                self.logger.info(f"User created successfully: user_id={reloaded_user.user_id}, community_id={reloaded_user.community_id}, community_name={reloaded_user.community.name}")
            else:
                self.logger.warning(f"User created but community relation not loaded: user_id={reloaded_user.user_id}, community_id={reloaded_user.community_id}")
        else:
            self.logger.warning(f"User created but without community_id: user_id={reloaded_user.user_id}")

        return reloaded_user

    def _audit_user(self, user_id: int, action: str, details: dict):
        """记录用户审计日志"""
        try:
            from wxcloudrun.utils.validators import _audit
            _audit(user_id, action, details)
        except Exception as e:
            self.logger.warning(f"Failed to audit user action: {e}")

    def _format_login_response(
        self,
        user,
        token: str,
        refresh_token: str,
        is_new_user: bool
    ) -> dict:
        """格式化登录响应"""
        from app.modules.auth.services import _format_user_login_response
        return _format_user_login_response(
            user=user,
            token=token,
            refresh_token=refresh_token,
            is_new_user=is_new_user
        )