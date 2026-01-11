"""
计数器用例
"""
import logging
from flask import current_app
from sqlalchemy import select, delete
from database.flask_models import db, Counters
from app.shared.utils.transaction import transaction

app_logger = logging.getLogger('log')


class CounterUseCase:
    """计数器用例"""

    def execute(self, action: str, params: dict) -> dict:
        """
        执行计数器操作

        Args:
            action: 操作类型（increment, reset, get, list, clear）
            params: 请求参数

        Returns:
            dict: 包含成功状态和响应数据
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
                current_app.logger.warning(f"不支持的action参数: {action}")
                return {
                    'success': False,
                    'message': f'不支持的action参数: {action}',
                    'data': {}
                }

        except Exception as e:
            current_app.logger.error(f"计数器操作失败: {str(e)}", exc_info=True)
            db.session.rollback()
            return {
                'success': False,
                'message': f'计数器操作失败: {str(e)}',
                'data': {}
            }

    def _increment(self, params: dict) -> dict:
        """增加计数"""
        counter_id = params.get('counter_id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        with transaction():
            if counter:
                counter.count += 1
            else:
                counter = Counters(id=counter_id, count=1)
                db.session.add(counter)

        current_app.logger.info(f"计数器 {counter.id} 增加到 {counter.count}")
        return {
            'success': True,
            'message': '计数增加成功',
            'data': {'id': counter.id, 'count': counter.count}
        }

    def _reset(self, params: dict) -> dict:
        """重置计数"""
        counter_id = params.get('counter_id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        if counter:
            with transaction():
                counter.count = 0
            current_app.logger.info(f"计数器 {counter.id} 已重置")
            return {
                'success': True,
                'message': '计数重置成功',
                'data': {'id': counter.id, 'count': 0}
            }
        else:
            current_app.logger.warning(f"计数器 {counter_id} 不存在")
            return {
                'success': False,
                'message': f'计数器 {counter_id} 不存在',
                'data': {}
            }

    def _get(self, params: dict) -> dict:
        """获取计数"""
        counter_id = params.get('id', 1)
        counter = db.session.execute(select(Counters).filter_by(id=counter_id)).scalar_one_or_none()

        if counter:
            return {
                'success': True,
                'message': '获取计数成功',
                'data': {'id': counter_id, 'count': counter.count}
            }
        else:
            return {
                'success': False,
                'message': f'计数器 {counter_id} 不存在',
                'data': {}
            }

    def _list(self) -> dict:
        """列出所有计数器"""
        counters = db.session.execute(select(Counters)).scalars().all()
        counter_list = [{'id': c.id, 'count': c.count} for c in counters]
        current_app.logger.info(f"获取计数器列表，共 {len(counter_list)} 个计数器")
        return {
            'success': True,
            'message': '获取计数器列表成功',
            'data': {'counters': counter_list}
        }

    def _clear(self) -> dict:
        """清除所有计数器"""
        with transaction():
            db.session.execute(delete(Counters))
        current_app.logger.info("所有计数器已清除")
        return {
            'success': True,
            'message': '所有计数器已清除',
            'data': {'message': '所有计数器已清除'}
        }