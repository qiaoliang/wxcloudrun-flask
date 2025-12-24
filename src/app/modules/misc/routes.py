"""
其他功能视图模块
包含计数器、环境配置、首页等功能
"""

import logging
from datetime import datetime
from flask import render_template, request, Response, current_app
from . import misc_bp
from app.shared import make_succ_response, make_err_response, make_succ_empty_response
from database.flask_models import Counters, db
from config_manager import analyze_all_configs, detect_external_systems_status

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

    try:
        if action == 'increment':
            # 增加计数
            counter_id = params.get('counter_id', 1)
            counter = Counters.query.filter_by(id=counter_id).first()
            if counter:
                counter.count += 1
            else:
                counter = Counters(count=1)
                db.session.add(counter)
            db.session.commit()
            current_app.logger.info(f"计数器 {counter.id} 增加到 {counter.count}")
            return make_succ_response({'id': counter.id, 'count': counter.count})

        elif action == 'reset':
            # 重置计数
            counter_id = params.get('counter_id', 1)
            counter = Counters.query.filter_by(id=counter_id).first()
            if counter:
                counter.count = 0
                db.session.commit()
                current_app.logger.info(f"计数器 {counter.id} 已重置")
                return make_succ_response({'id': counter.id, 'count': 0})
            else:
                current_app.logger.warning(f"计数器 {counter_id} 不存在")
                return make_err_response({}, f'计数器 {counter_id} 不存在')

        elif action == 'get':
            # 获取计数
            counter_id = params.get('id', 1)
            counter = Counters.query.filter_by(id=counter_id).first()
            if counter:
                return make_succ_response({'id': counter_id, 'count': counter.count})
            else:
                return make_err_response({}, f'计数器 {counter_id} 不存在')

        elif action == 'list':
            # 列出所有计数器
            counters = Counters.query.all()
            counter_list = [{'id': c.id, 'count': c.count} for c in counters]
            current_app.logger.info(f"获取计数器列表，共 {len(counter_list)} 个计数器")
            return make_succ_response({'counters': counter_list})

        elif action == 'clear':
            # 清除所有计数器
            Counters.query.delete()
            db.session.commit()
            current_app.logger.info("所有计数器已清除")
            return make_succ_response({'message': '所有计数器已清除'})

        else:
            current_app.logger.warning(f"不支持的action参数: {action}")
            return make_err_response({}, f'不支持的action参数: {action}')

    except Exception as e:
        current_app.logger.error(f"计数器操作失败: {str(e)}", exc_info=True)
        db.session.rollback()
        return make_err_response({}, f'计数器操作失败: {str(e)}')


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
            counters = Counters.query.all()
            counter_list = [{'id': c.id, 'count': c.count} for c in counters]
            current_app.logger.info(f"获取所有计数器列表，共 {len(counter_list)} 个计数器")
            return make_succ_response({'counters': counter_list})
        else:
            # 获取特定计数器
            counter = Counters.query.filter_by(id=counter_id).first()
            if counter:
                current_app.logger.info(f"获取计数器 {counter_id}，当前值: {counter.count}")
                return make_succ_response({'id': counter_id, 'count': counter.count})
            else:
                current_app.logger.warning(f"计数器 {counter_id} 不存在")
                return make_err_response({}, f'计数器 {counter_id} 不存在')

    except Exception as e:
        current_app.logger.error(f"获取计数器信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取计数器信息失败: {str(e)}')


@misc_bp.route('/get_envs', methods=['GET'])
def get_environments():
    """
    :return: 环境配置信息
    """
    try:
        # 分析所有配置
        config_status = analyze_all_configs()
        external_status = detect_external_systems_status()

        env_info = {
            'config_status': config_status,
            'external_status': external_status,
            'timestamp': datetime.now().isoformat()
        }

        current_app.logger.info("获取环境配置信息成功")
        return make_succ_response(env_info)

    except Exception as e:
        current_app.logger.error(f"获取环境配置信息失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'获取环境配置信息失败: {str(e)}')