"""
上传媒体文件用例
"""
import logging
import os
import uuid
from flask import current_app, request
from werkzeug.utils import secure_filename

app_logger = logging.getLogger('log')


class UploadMediaUseCase:
    """上传媒体文件用例"""

    def execute(self) -> dict:
        """
        执行上传媒体文件操作

        Returns:
            dict: 包含成功状态和响应数据
        """
        try:
            # 检查是否有文件
            if 'file' not in request.files:
                return {
                    'success': False,
                    'message': '没有上传文件',
                    'data': {}
                }

            file = request.files['file']
            if file.filename == '':
                return {
                    'success': False,
                    'message': '没有选择文件',
                    'data': {}
                }

            # 获取文件类型
            file_type = request.form.get('file_type', 'image')  # image 或 voice

            # 验证文件类型
            if file_type not in ['image', 'voice']:
                return {
                    'success': False,
                    'message': '无效的文件类型',
                    'data': {}
                }

            # 验证文件扩展名
            allowed_extensions = {
                'image': {'jpg', 'jpeg', 'png', 'gif'},
                'voice': {'mp3', 'wav', 'm4a', 'aac'}
            }

            file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
            if file_ext not in allowed_extensions[file_type]:
                return {
                    'success': False,
                    'message': f'不支持的文件格式，支持: {", ".join(allowed_extensions[file_type])}',
                    'data': {}
                }

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
                return {
                    'success': False,
                    'message': f'文件大小超过限制（最大{max_size_mb}MB）',
                    'data': {}
                }

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

            return {
                'success': True,
                'message': '文件上传成功',
                'data': {
                    'file_url': file_url,
                    'file_type': file_type,
                    'file_size': file_size,
                    'filename': unique_filename
                }
            }

        except Exception as e:
            current_app.logger.error(f"文件上传失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'文件上传失败: {str(e)}',
                'data': {}
            }