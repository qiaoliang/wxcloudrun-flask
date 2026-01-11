"""
短信服务视图模块
包含验证码发送和验证功能
"""

import logging
from flask import request, current_app
from . import sms_bp
from app.shared import make_succ_response, make_err_response
from app.application.use_cases.sms import SendVerificationCodeUseCase

app_logger = logging.getLogger('log')


@sms_bp.route('/sms/send_code', methods=['POST'])
def sms_send_code():
    try:
        params = request.get_json() or {}
        phone = params.get('phone')
        purpose = params.get('purpose', 'register')
        if not phone:
            return make_err_response({}, '缺少phone参数')

        use_case = SendVerificationCodeUseCase()
        result = use_case.execute(phone, purpose)

        if result['success']:
            return make_succ_response(result['data'])
        else:
            return make_err_response(result['data'], result['message'])

    except Exception as e:
        current_app.logger.error(f'发送验证码失败: {str(e)}', exc_info=True)
        return make_err_response({}, '服务器错误')