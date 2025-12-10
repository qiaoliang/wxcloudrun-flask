"""
短信服务视图模块
包含验证码发送和验证功能
"""

import logging
import os
from datetime import datetime, timedelta
from flask import request
from wxcloudrun import app, db
from wxcloudrun.response import make_succ_response, make_err_response
from wxcloudrun.model import VerificationCode
from wxcloudrun.sms_service import create_sms_provider, generate_code
from wxcloudrun.utils.validators import _verify_sms_code, _code_expiry_minutes
from config_manager import should_use_real_sms

app_logger = logging.getLogger('log')


@app.route('/api/sms/send_code', methods=['POST'])
def sms_send_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        purpose = params.get('purpose', 'register')
        if not phone:
            return make_err_response({}, '缺少phone参数')
        
        # 标准化电话号码格式
        from wxcloudrun.utils.validators import normalize_phone_number
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
        from wxcloudrun.utils.validators import _hash_code
        code_hash = _hash_code(normalized_phone, code, salt)
        
        expires_at = now + timedelta(minutes=_code_expiry_minutes())
        if not vc:
            vc = VerificationCode(phone_number=normalized_phone, purpose=purpose, code_hash=code_hash,
                                  salt=salt, expires_at=expires_at, last_sent_at=now)
            db.session.add(vc)
        else:
            vc.code_hash = code_hash
            vc.salt = salt
            vc.expires_at = expires_at
            vc.last_sent_at = now
        db.session.commit()
        
        provider = create_sms_provider()
        provider.send(phone, f"验证码: {code}，{_code_expiry_minutes()}分钟内有效")
        
        resp = {'message': '验证码已发送'}
        debug_flag = os.getenv('SMS_DEBUG_RETURN_CODE', '0') == '1' or request.headers.get(
            'X-Debug-Code') == '1'
        if debug_flag:
            resp['debug_code'] = code
        return make_succ_response(resp)
    except Exception as e:
        app.logger.error(f'发送验证码失败: {str(e)}', exc_info=True)
        return make_err_response({}, f'发送验证码失败: {str(e)}')