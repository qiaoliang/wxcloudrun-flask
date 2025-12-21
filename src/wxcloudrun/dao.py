import logging
from datetime import datetime, date
from sqlalchemy.exc import OperationalError
from sqlalchemy import and_, or_
from flask import current_app

from database import get_database
from database.models import Counters, User, CheckinRule, CheckinRecord

# 初始化日志
logger = logging.getLogger('log')


def get_db():
    """获取数据库实例，优先从Flask应用上下文获取"""
    try:
        # 尝试从Flask应用上下文获取数据库实例
        if hasattr(current_app, 'db_core'):
            return current_app.db_core
    except RuntimeError:
        # 不在Flask应用上下文中，回退到全局实例
        pass

    # 检查是否在测试环境中
    import os
    if os.getenv('ENV_TYPE') == 'unit':
        return get_database('test')
    
    # 回退到全局数据库实例
    return get_database()


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        with get_db().get_session() as session:
            result = session.query(Counters).filter(Counters.id == id).first()
            logger.info(f"query_counterbyid: 查询ID {id} 的结果 - {'找到计数器' if result else '未找到计数器'}")
            if result:
                logger.info(f"query_counterbyid: 计数器值为 {result.count}")
            return result
    except OperationalError as e:
        logger.error("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        with get_db().get_session() as session:
            logger.info(f"delete_counterbyid: 准备删除ID为 {id} 的计数器")
            counter = session.query(Counters).get(id)
            if counter is None:
                logger.warning(f"delete_counterbyid: 未找到ID为 {id} 的计数器进行删除")
                return
            logger.info(f"delete_counterbyid: 找到计数器，值为 {counter.count}")
            session.delete(counter)
            session.commit()
            logger.info(f"delete_counterbyid: 成功删除ID为 {id} 的计数器")
    except OperationalError as e:
        logger.error("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        with get_db().get_session() as session:
            logger.info(f"insert_counter: 准备插入计数器，ID: {counter.id}, 值: {counter.count}")
            session.add(counter)
            session.commit()
            logger.info(f"insert_counter: 成功插入计数器，ID: {counter.id}, 值: {counter.count}")
    except OperationalError as e:
        logger.error("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        with get_db().get_session() as session:
            logger.info(f"update_counterbyid: 准备更新计数器，ID: {counter.id}, 新值: {counter.count}")
            existing_counter = session.query(Counters).filter(Counters.id == counter.id).first()
            if existing_counter is None:
                logger.warning(f"update_counterbyid: 未找到ID为 {counter.id} 的计数器进行更新")
                return
            logger.info(f"update_counterbyid: 找到现有计数器，当前值: {existing_counter.count}")
            # 更新现有记录的值
            existing_counter.count = counter.count
            existing_counter.updated_at = counter.updated_at
            logger.info(f"update_counterbyid: 设置新值为 {existing_counter.count}")
            session.flush()
            logger.info("update_counterbyid: 执行session flush")
            # session.commit() is handled by the context manager
            logger.info(f"update_counterbyid: 成功提交更新，ID: {counter.id}, 值: {existing_counter.count}")
    except OperationalError as e:
        logger.error("update_counterbyid errorMsg= {} ".format(e))

# 打卡规则相关数据访问方法














# 监督规则关系数据访问方法






















