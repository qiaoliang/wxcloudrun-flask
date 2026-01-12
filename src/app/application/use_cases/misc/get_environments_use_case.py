"""
获取环境配置用例
"""
import logging
from datetime import datetime
from flask import current_app
from config import analyze_all_configs, detect_external_systems_status

app_logger = logging.getLogger('log')


class GetEnvironmentsUseCase:
    """获取环境配置用例"""

    def execute(self) -> dict:
        """
        执行获取环境配置操作

        Returns:
            dict: 包含成功状态和响应数据
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
            return {
                'success': True,
                'message': '获取环境配置信息成功',
                'data': env_info
            }

        except Exception as e:
            current_app.logger.error(f"获取环境配置信息失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'获取环境配置信息失败: {str(e)}',
                'data': {}
            }