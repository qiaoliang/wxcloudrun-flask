"""
其他功能视图模块
包含计数器、环境配置、首页等功能
"""

import logging
from datetime import datetime
from flask import render_template, request, current_app
from . import misc_bp
from app.shared import make_succ_response, make_err_response, make_succ_empty_response
from app.application.use_cases.misc import CounterUseCase, GetEnvironmentsUseCase, UploadMediaUseCase

app_logger = logging.getLogger('log')


@misc_bp.route('/')
def index():
    """
    :return: 返回index页面
    """
    current_app.logger.info("主页访问")
    return render_template('index.html')


@misc_bp.route('/env')
def env_viewer():
    """
    :return: 返回环境配置查看器页面
    """
    current_app.logger.info("环境配置查看器页面访问")
    try:
        with open('static/env_viewer.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "环境配置查看器页面未找到", 404


@misc_bp.route('/count', methods=['POST'])
def count():
    """
    :return: 计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()
    current_app.logger.info(f"接收到计数器POST请求，参数: {params}")

    # 检查action参数
    if 'action' not in params:
        current_app.logger.warning("请求中缺少action参数")
        return make_err_response({}, '缺少action参数')

    action = params.get('action')

    use_case = CounterUseCase()
    result = use_case.execute(action, params)

    if result.is_success:
        return make_succ_response(result.data)
    else:
        return make_err_response(result.data, result.message)


@misc_bp.route('/count', methods=['GET'])
def get_counter():
    """
    :return: 计数器信息
    """
    try:
        # 获取查询参数
        counter_id = request.args.get('id')
        if not counter_id:
            # 列出所有计数器
            use_case = CounterUseCase()
            result = use_case.execute('list', {})
            return make_succ_response(result.data)
        else:
            # 获取特定计数器
            use_case = CounterUseCase()
            result = use_case.execute('get', {'id': int(counter_id)})
            if result.is_success:
                return make_succ_response(result.data)
            else:
                return make_err_response(result.data, result.message)

    except Exception as e:
        current_app.logger.error(f"获取计数器信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取计数器信息失败: {str(e)}')


@misc_bp.route('/get_envs', methods=['GET'])
def get_environments():
    """
    :return: 环境配置信息
    """
    try:
        use_case = GetEnvironmentsUseCase()
        result = use_case.execute()
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f"获取环境配置信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取环境配置信息失败: {str(e)}')


@misc_bp.route('/upload/media', methods=['POST'])
def upload_media():
    """
    上传媒体文件（语音或图片）

    :return: 上传结果
    """
    try:
        use_case = UploadMediaUseCase()
        result = use_case.execute()
        return make_succ_response(result.data)

    except Exception as e:
        current_app.logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'文件上传失败: {str(e)}')