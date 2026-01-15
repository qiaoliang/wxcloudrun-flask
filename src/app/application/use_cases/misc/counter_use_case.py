"""
计数器用例
"""
import logging
from flask import has_app_context
from sqlalchemy import select, delete
from database.flask_models import db, Counters
from app.shared.utils.transaction import transaction

from ..base import BaseUseCase, UseCaseResult, UseCaseStatus

app_logger = logging.getLogger('log')


def _get_logger():
    """获取logger，避免在模块级别访问current_app"""
    if has_app_context():
        from flask import current_app
        return current_app.logger
    return app_logger


class CounterUseCase(BaseUseCase):
    """计数器用例"""

    def _validate(self, action: str, params: dict) -> UseCaseResult:
        """
        验证参数

        Args:
            action: 操作类型
            params: 请求参数

        Returns:
            UseCaseResult: 验证结果
        """
        # 验证 action 参数
        valid_actions = ['increment', 'reset', 'get', 'list', 'clear']
        if action not in valid_actions:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message=f'不支持的action参数: {action}，支持: {", ".join(valid_actions)}'
            )

        # 验证特定操作需要的参数
        if action in ['increment', 'reset', 'get']:
            if action == 'get':
                counter_id = params.get('id')
            else:
                counter_id = params.get('counter_id')
            
            if counter_id is None:
                return UseCaseResult(
                    status=UseCaseStatus.VALIDATION_ERROR,
                    message=f'{action} 操作需要 counter_id 参数'
                )

        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message="验证通过"
        )

    def _execute(self, action: str, params: dict) -> UseCaseResult:
        """
        执行计数器操作

        Args:
            action: 操作类型
            params: 请求参数

        Returns:
            UseCaseResult: 执行结果
        """
        try:
            if action == 'increment':
                return self._increment(params)
            elif action == 'reset':
                return self._reset(params)
            elif action == 'get':
                return self._get(params)
            elif action == 'list':
                return self._list()
            elif action == 'clear':
                return self._clear()
            else:
                return UseCaseResult(
                    status=UseCaseStatus.BUSINESS_ERROR,
                    message=f'不支持的action参数: {action}'
                )

        except Exception as e:
            _get_logger().error(f"计数器操作失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return UseCaseResult(
                status=UseCaseStatus.FAILURE,
                message=f'计数器操作失败: {str(e)}',
                data={}
            )

    def _increment(self, params: dict) -> UseCaseResult:
        """增加计数"""
        counter_id = params.get('counter_id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        with transaction():
            if counter:
                counter.count += 1
            else:
                counter = Counters(id=counter_id, count=1)
                db.session.add(counter)

        _get_logger().info(f"计数器 {counter.id} 增加到 {counter.count}")
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='计数增加成功',
            data={'id': counter.id, 'count': counter.count}
        )

    def _reset(self, params: dict) -> UseCaseResult:
        """重置计数"""
        counter_id = params.get('counter_id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        if counter:
            with transaction():
                counter.count = 0
            _get_logger().info(f"计数器 {counter.id} 已重置")
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='计数重置成功',
                data={'id': counter.id, 'count': 0}
            )
        else:
            _get_logger().warning(f"计数器 {counter_id} 不存在")
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message=f'计数器 {counter_id} 不存在',
                data={}
            )

    def _get(self, params: dict) -> UseCaseResult:
        """获取计数"""
        counter_id = params.get('id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        if counter:
            return UseCaseResult(
                status=UseCaseStatus.SUCCESS,
                message='获取计数成功',
                data={'id': counter_id, 'count': counter.count}
            )
        else:
            return UseCaseResult(
                status=UseCaseStatus.NOT_FOUND,
                message=f'计数器 {counter_id} 不存在',
                data={}
            )

    def _list(self) -> UseCaseResult:
        """列出所有计数器"""
        counters = db.session.execute(select(Counters)).scalars().all()
        counter_list = [{'id': c.id, 'count': c.count} for c in counters]
        _get_logger().info(f"获取计数器列表，共 {len(counter_list)} 个计数器")
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='获取计数器列表成功',
            data={'counters': counter_list}
        )

    def _clear(self) -> UseCaseResult:
        """清除所有计数器"""
        with transaction():
            db.session.execute(delete(Counters))
        _get_logger().info("所有计数器已清除")
        return UseCaseResult(
            status=UseCaseStatus.SUCCESS,
            message='所有计数器已清除',
            data={'message': '所有计数器已清除'}
        )