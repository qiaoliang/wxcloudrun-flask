"""
获取环境配置用例
"""
import logging
from datetime import datetime
from flask import has_app_context
from config import analyze_all_configs, detect_external_systems_status

from ..base import BaseUseCase, UseCaseResult, UseCaseStatus

app_logger = logging.getLogger('log')


def _get_logger():
    """获取logger，避免在模块级别访问current_app"""
    if has_app_context():
        from flask import current_app
        return current_app.logger
    return app_logger


class GetEnvironmentsUseCase(BaseUseCase):
    """获取环境配置用例"""

    def _validate(self) -> UseCaseResult:
        """
        验证参数

        Returns:
            UseCaseResult: 验证结果
        """
        # 此用例不需要参数验证
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self) -> UseCaseResult:
        """
        执行获取环境配置操作

        Returns:
            UseCaseResult: 执行结果
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

            _get_logger().info("获取环境配置信息成功")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取环境配置信息成功',
                data=env_info
            )

        except Exception as e:
            _get_logger().error(f"获取环境配置信息失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取环境配置信息失败: {str(e)}',
                data={}
            )