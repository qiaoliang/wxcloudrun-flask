"""
获取环境配置用例
"""
import logging
from datetime import datetime
from flask import current_app
from config import analyze_all_configs, detect_external_systems_status

from ..base import BaseUseCase, UseCaseResult, UseCaseStatus

app_logger = logging.getLogger('log')


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

            current_app.logger.info("获取环境配置信息成功")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取环境配置信息成功',
                data=env_info
            )

        except Exception as e:
            current_app.logger.error(f"获取环境配置信息失败: {str(e)}", exc_info=True)
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'获取环境配置信息失败: {str(e)}',
                data={}
            )