"""
短信服务视图模块
包含验证码发送和验证功能
"""

import logging
import os
from datetime import datetime, timedelta
from flask import request, current_app
from . import sms_bp
from app.shared import make_succ_response, make_err_response
from database.flask_models import db, VerificationCode
from wxcloudrun.sms_service import create_sms_provider, generate_code
from wxcloudrun.utils.validators import _verify_sms_code, _code_expiry_minutes, normalize_phone_number, _hash_code
from config_manager import should_use_real_sms

app_logger = logging.getLogger('log')


@sms_bp.route('/sms/send_code', methods=['POST'])
def sms_send_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        purpose = params.get('purpose', 'register')
        if not phone:
            return make_err_response({}, '缺少phone参数')
        
        # 标准化电话号码格式
        normalized_phone = normalize_phone_number(phone)
        
        # 在 mock 环境下跳过频率限制
        is_mock_env = not should_use_real_sms()
        
        now = datetime.now()
        vc = VerificationCode.query.filter_by(
            phone_number=normalized_phone, purpose=purpose).first()
        
        # 只在非 mock 环境下检查频率限制
        if not is_mock_env and vc and (now - vc.last_sent_at).total_seconds() < 60:
            return make_err_response({}, '请求过于频繁，请稍后再试')
        
        code = generate_code(6)
        import secrets
        salt = secrets.token_hex(8)
        
        # 使用验证工具函数生成哈希
        code_hash = _hash_code(normalized_phone, code, salt)
        
        if vc:
            # 更新现有记录
            vc.code_hash = code_hash
            vc.salt = salt
            vc.expires_at = now + timedelta(minutes=_code_expiry_minutes())
            vc.last_sent_at = now
            vc.attempts = 0
        else:
            # 创建新记录
            vc = VerificationCode(
                phone_number=normalized_phone,
                purpose=purpose,
                code_hash=code_hash,
                salt=salt,
                expires_at=now + timedelta(minutes=_code_expiry_minutes()),
                last_sent_at=now,
                attempts=0
            )
            db.session.add(vc)
        
        db.session.commit()
        
        # 发送短信
        if is_mock_env:
            current_app.logger.info(f'Mock环境：验证码已生成，手机号：{normalized_phone}，验证码：{code}')
            return make_succ_response({
                'message': '验证码发送成功（测试环境）',
                'code': code  # 仅在测试环境返回验证码
            })
        else:
            # 生产环境发送真实短信
            provider = create_sms_provider()
            success = provider.send_verification_code(normalized_phone, code)
            
            if success:
                current_app.logger.info(f'验证码发送成功，手机号：{normalized_phone}')
                return make_succ_response({'message': '验证码发送成功'})
            else:
                current_app.logger.error(f'验证码发送失败，手机号：{normalized_phone}')
                return make_err_response({}, '验证码发送失败')
    
    except Exception as e:
        current_app.logger.error(f'发送验证码失败: {str(e)}', exc_info=True)
        return make_err_response({}, '服务器错误')