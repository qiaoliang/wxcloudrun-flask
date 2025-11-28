import logging
from datetime import datetime
from sqlalchemy.exc import OperationalError

from wxcloudrun import db
from wxcloudrun.model import Counters, User

# 初始化日志
logger = logging.getLogger('log')


def query_counterbyid(id):
    """
    根据ID查询Counter实体
    :param id: Counter的ID
    :return: Counter实体
    """
    try:
        return Counters.query.filter(Counters.id == id).first()
    except OperationalError as e:
        logger.info("query_counterbyid errorMsg= {} ".format(e))
        return None


def delete_counterbyid(id):
    """
    根据ID删除Counter实体
    :param id: Counter的ID
    """
    try:
        counter = Counters.query.get(id)
        if counter is None:
            return
        db.session.delete(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("delete_counterbyid errorMsg= {} ".format(e))


def insert_counter(counter):
    """
    插入一个Counter实体
    :param counter: Counters实体
    """
    try:
        db.session.add(counter)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_counter errorMsg= {} ".format(e))


def update_counterbyid(counter):
    """
    根据ID更新counter的值
    :param counter实体
    """
    try:
        existing_counter = query_counterbyid(counter.id)
        if existing_counter is None:
            return
        # 更新现有记录的值
        existing_counter.count = counter.count
        existing_counter.updated_at = counter.updated_at
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_counterbyid errorMsg= {} ".format(e))


def query_user_by_openid(openid):
    """
    根据微信OpenID查询用户实体
    :param openid: 微信OpenID
    :return: User实体
    """
    try:
        return User.query.filter(User.wechat_openid == openid).first()
    except OperationalError as e:
        logger.info("query_user_by_openid errorMsg= {} ".format(e))
        return None


def query_user_by_id(user_id):
    """
    根据用户ID查询用户实体
    :param user_id: 用户ID
    :return: User实体
    """
    try:
        return User.query.filter(User.user_id == user_id).first()
    except OperationalError as e:
        logger.info("query_user_by_id errorMsg= {} ".format(e))
        return None


def insert_user(user):
    """
    插入一个User实体
    :param user: User实体
    """
    try:
        db.session.add(user)
        db.session.commit()
    except OperationalError as e:
        logger.info("insert_user errorMsg= {} ".format(e))


def update_user_by_id(user):
    """
    根据ID更新用户信息
    :param user: User实体
    """
    try:
        existing_user = query_user_by_id(user.user_id)
        if existing_user is None:
            return
        # 更新用户信息
        if user.nickname is not None:
            existing_user.nickname = user.nickname
        if user.avatar_url is not None:
            existing_user.avatar_url = user.avatar_url
        if user.phone_number is not None:
            existing_user.phone_number = user.phone_number
        if user.role is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(user.role, str):
                role_value = User.get_role_value(user.role)
                if role_value is not None:
                    existing_user.role = role_value
            elif isinstance(user.role, int):
                existing_user.role = user.role
        if user.community_id is not None:
            existing_user.community_id = user.community_id
        if user.status is not None:
            # 如果传入的是字符串，转换为对应的整数值
            if isinstance(user.status, str):
                status_value = User.get_status_value(user.status)
                if status_value is not None:
                    existing_user.status = status_value
            elif isinstance(user.status, int):
                existing_user.status = user.status
        existing_user.updated_at = user.updated_at or datetime.now()
        
        db.session.flush()
        db.session.commit()
    except OperationalError as e:
        logger.info("update_user_by_id errorMsg= {} ".format(e))
