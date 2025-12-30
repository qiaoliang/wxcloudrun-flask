"""
其他功能视图模块
包含计数器、环境配置、首页等功能
"""

import logging
from datetime import datetime
from flask import render_template, request, Response, current_app
from sqlalchemy import select, delete
from . import misc_bp
from app.shared import make_succ_response, make_err_response, make_succ_empty_response
from database.flask_models import Counters, db
from app.shared.utils.transaction import transaction
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
            counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()
            # 使用事务管理器确保数据一致性
            with transaction():
                if counter:
                    counter.count += 1
                else:
                    # 创建新计数器时，设置 id 为请求中指定的 counter_id
                    counter = Counters(id=counter_id, count=1)
                    db.session.add(counter)
            current_app.logger.info(f"计数器 {counter.id} 增加到 {counter.count}")
            return make_succ_response({'id': counter.id, 'count': counter.count})

        elif action == 'reset':
            # 重置计数
            counter_id = params.get('counter_id', 1)
            counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()
            if counter:
                with transaction():
                    counter.count = 0
                current_app.logger.info(f"计数器 {counter.id} 已重置")
                return make_succ_response({'id': counter.id, 'count': 0})
            else:
                current_app.logger.warning(f"计数器 {counter_id} 不存在")
                return make_err_response({}, f'计数器 {counter_id} 不存在')

        elif action == 'get':
            # 获取计数
            counter_id = params.get('id', 1)
            counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()
            if counter:
                return make_succ_response({'id': counter_id, 'count': counter.count})
            else:
                return make_err_response({}, f'计数器 {counter_id} 不存在')

        elif action == 'list':
            # 列出所有计数器
            counters = db.session.execute(select(Counters)).scalars().all()
            counter_list = [{'id': c.id, 'count': c.count} for c in counters]
            current_app.logger.info(f"获取计数器列表，共 {len(counter_list)} 个计数器")
            return make_succ_response({'counters': counter_list})

        elif action == 'clear':
            # 清除所有计数器
            with transaction():
                db.session.execute(delete(Counters))
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
            counters = db.session.execute(select(Counters)).scalars().all()
            counter_list = [{'id': c.id, 'count': c.count} for c in counters]
            current_app.logger.info(f"获取所有计数器列表，共 {len(counter_list)} 个计数器")
            return make_succ_response({'counters': counter_list})
        else:
            # 获取特定计数器
            counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()
            if counter:
                current_app.logger.info(f"获取计数器 {counter_id}，当前值: {counter.count}")
                return make_succ_response({'id': counter.id, 'count': counter.count})
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


@misc_bp.route('/upload/media', methods=['POST'])
def upload_media():
    """
    上传媒体文件（语音或图片）
    
    :return: 上传结果
    """
    try:
        import os
        import uuid
        from werkzeug.utils import secure_filename
        
        # 检查是否有文件
        if 'file' not in request.files:
            return make_err_response({}, '没有上传文件')
        
        file = request.files['file']
        if file.filename == '':
            return make_err_response({}, '没有选择文件')
        
        # 获取文件类型
        file_type = request.form.get('file_type', 'image')  # image 或 voice
        
        # 验证文件类型
        if file_type not in ['image', 'voice']:
            return make_err_response({}, '无效的文件类型')
        
        # 验证文件扩展名
        allowed_extensions = {
            'image': {'jpg', 'jpeg', 'png', 'gif'},
            'voice': {'mp3', 'wav', 'm4a', 'aac'}
        }
        
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions[file_type]:
            return make_err_response({}, f'不支持的文件格式，支持: {", ".join(allowed_extensions[file_type])}')
        
        # 验证文件大小
        max_sizes = {
            'image': 5 * 1024 * 1024,  # 5MB
            'voice': 10 * 1024 * 1024  # 10MB
        }
        
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > max_sizes[file_type]:
            max_size_mb = max_sizes[file_type] / (1024 * 1024)
            return make_err_response({}, f'文件大小超过限制（最大{max_size_mb}MB）')
        
        # 生成唯一文件名
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # 创建上传目录
        upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', file_type)
        os.makedirs(upload_dir, exist_ok=True)
        
        # 保存文件
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        # 生成访问URL
        file_url = f"/static/uploads/{file_type}/{unique_filename}"
        
        current_app.logger.info(f"文件上传成功: {file_url}, 类型: {file_type}, 大小: {file_size} bytes")
        
        return make_succ_response({
            'file_url': file_url,
            'file_type': file_type,
            'file_size': file_size,
            'filename': unique_filename
        })
        
    except Exception as e:
        current_app.logger.error(f"文件上传失败: {str(e)}", exc_info=True)
        return make_err_response({}, f'文件上传失败: {str(e)}')