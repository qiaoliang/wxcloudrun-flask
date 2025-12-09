"""
验证工具模块
包含各种验证相关的工具函数
"""

import os
import logging
from datetime import datetime, timedelta
from hashlib import sha256
from wxcloudrun import app, db
from wxcloudrun.model import VerificationCode

app_logger = logging.getLogger('log')


def _hash_code(phone, code, salt):
    """
    生成验证码哈希值
    """
    return sha256(f"{phone}:{code}:{salt}".encode('utf-8')).hexdigest()


def _code_expiry_minutes():
    """
    获取验证码过期时间（分钟）
    """
    try:
        return int(os.getenv('CONFIG_VERIFICATION_CODE_EXPIRY', '5'))
    except Exception:
        return 5


def _gen_phone_nickname():
    """
    生成基于手机号的昵称
    """
    import secrets
    s = 'phone_' + secrets.token_hex(8)
    return s[:100]


def _verify_sms_code(phone, purpose, code):
    """
    验证短信验证码
    """
    # 在 mock 环境下（should_use_real_sms() 返回 False），直接验证通过
    from config_manager import should_use_real_sms
    if not should_use_real_sms():
        app.logger.info(f"[Mock SMS] 跳过验证码验证，ENV_TYPE={os.getenv('ENV_TYPE', 'unit')}")
        return True
    
    vc = VerificationCode.query.filter_by(
        phone_number=phone, purpose=purpose).first()
    if not vc:
        return False
    if vc.expires_at < datetime.now():
        return False
    # 检查验证码是否已被使用
    if getattr(vc, 'is_used', False):
        return False
    # 验证码匹配
    if vc.code_hash == _hash_code(phone, code, vc.salt):
        # 验证成功后立即标记为已使用
        vc.is_used = True
        db.session.commit()
        return True
    return False


def _audit(user_id, action, detail=None):
    """
    记录用户审计日志
    """
    try:
        import json
        from wxcloudrun.model import UserAuditLog
        log = UserAuditLog(user_id=user_id, action=action, detail=json.dumps(
            detail) if isinstance(detail, dict) else detail)
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass