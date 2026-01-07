"""
异常值计算器 - 用于社区数字看板
计算用户未按时打卡的异常值
"""
import logging
from datetime import datetime, time, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, and_, or_
from database.flask_models import db, User, CommunityCheckinRule, CheckinRecord, UserDailyAbnormality

logger = logging.getLogger('AbnormalityCalculator')


class AbnormalityCalculator:
    """异常值计算器类"""

    @staticmethod
    def calculate_abnormality_for_record(scheduled_time: datetime, actual_time: Optional[datetime]) -> int:
        """
        计算单次打卡的异常值

        Args:
            scheduled_time: 计划打卡时间
            actual_time: 实际打卡时间，如果未打卡则为 None

        Returns:
            异常值（小时数）
        """
        if actual_time is None:
            # 未打卡，计算从计划时间到当前时间的异常值
            current_time = datetime.now()
        else:
            current_time = actual_time

        # 如果实际打卡时间早于或等于计划时间，异常值为0
        if current_time <= scheduled_time:
            return 0

        # 计算时间差（秒），然后转换为小时
        time_diff_seconds = (current_time - scheduled_time).total_seconds()
        abnormality = int(time_diff_seconds // 3600)  # 每小时增加1点异常值

        return abnormality

    @staticmethod
    def get_user_rule_abnormality(user_id: int, rule_id: int, target_date: date) -> Optional[UserDailyAbnormality]:
        """
        获取用户在指定日期的规则异常值记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            target_date: 目标日期

        Returns:
            UserDailyAbnormality 对象或 None
        """
        stmt = select(UserDailyAbnormality).where(
            and_(
                UserDailyAbnormality.user_id == user_id,
                UserDailyAbnormality.rule_id == rule_id,
                UserDailyAbnormality.date == target_date
            )
        )
        return db.session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def create_or_update_abnormality_record(
        user_id: int,
        rule_id: int,
        target_date: date,
        scheduled_time: datetime,
        checkin_time: Optional[datetime] = None
    ) -> UserDailyAbnormality:
        """
        创建或更新异常值记录

        Args:
            user_id: 用户ID
            rule_id: 规则ID
            target_date: 目标日期
            scheduled_time: 计划打卡时间
            checkin_time: 实际打卡时间（可选）

        Returns:
            更新后的 UserDailyAbnormality 对象
        """
        # 计算异常值
        abnormality = AbnormalityCalculator.calculate_abnormality_for_record(
            scheduled_time, checkin_time
        )

        # 查找现有记录
        record = AbnormalityCalculator.get_user_rule_abnormality(user_id, rule_id, target_date)

        if record is None:
            # 创建新记录
            record = UserDailyAbnormality(
                user_id=user_id,
                rule_id=rule_id,
                date=target_date,
                total_abnormality=abnormality,
                last_scheduled_time=scheduled_time,
                last_checkin_time=checkin_time,
                is_completed=(checkin_time is not None)
            )
            db.session.add(record)
            logger.debug(f"创建异常值记录: User{user_id}, Rule{rule_id}, Date{target_date}, Abnormality={abnormality}")
        else:
            # 更新现有记录
            record.total_abnormality = abnormality
            record.last_scheduled_time = scheduled_time
            if checkin_time is not None:
                record.last_checkin_time = checkin_time
                record.is_completed = True
            record.updated_at = datetime.now()
            logger.debug(f"更新异常值记录: User{user_id}, Rule{rule_id}, Date{target_date}, Abnormality={abnormality}")

        return record

    @staticmethod
    def calculate_all_pending_users(target_date: Optional[date] = None) -> Dict[str, int]:
        """
        计算所有未完成打卡用户的异常值

        Args:
            target_date: 目标日期，默认为今天

        Returns:
            统计信息字典 {'updated': 更新数量, 'created': 创建数量, 'errors': 错误数量}
        """
        if target_date is None:
            target_date = date.today()

        stats = {'updated': 0, 'created': 0, 'errors': 0, 'skipped': 0}

        try:
            # 获取所有启用的社区规则
            stmt = select(CommunityCheckinRule).where(
                CommunityCheckinRule.status == 1  # 启用状态
            )
            rules = db.session.execute(stmt).scalars().all()

            logger.info(f"开始计算异常值，日期: {target_date}, 启用规则数: {len(rules)}")

            for rule in rules:
                try:
                    # 获取该规则下的所有用户（通过 UserCommunityRule 关联）
                    from database.flask_models import UserCommunityRule
                    user_rule_stmt = select(UserCommunityRule).where(
                        and_(
                            UserCommunityRule.community_rule_id == rule.community_rule_id,
                            UserCommunityRule.is_active == True
                        )
                    )
                    user_mappings = db.session.execute(user_rule_stmt).scalars().all()

                    for mapping in user_mappings:
                        user_id = mapping.user_id

                        # 计算当天的计划打卡时间
                        scheduled_time = datetime.combine(
                            target_date,
                            rule.scheduled_time
                        )

                        # 检查用户今天是否已打卡
                        checkin_stmt = select(CheckinRecord).where(
                            and_(
                                CheckinRecord.user_id == user_id,
                                CheckinRecord.community_rule_id == rule.community_rule_id,
                                db.func.date(CheckinRecord.checkin_time) == target_date
                            )
                        ).order_by(CheckinRecord.checkin_time.desc())

                        checkin_record = db.session.execute(checkin_stmt).first()

                        if checkin_record:
                            checkin_time = checkin_record[0].checkin_time
                        else:
                            checkin_time = None

                        # 创建或更新异常值记录
                        record = AbnormalityCalculator.create_or_update_abnormality_record(
                            user_id=user_id,
                            rule_id=rule.community_rule_id,
                            target_date=target_date,
                            scheduled_time=scheduled_time,
                            checkin_time=checkin_time
                        )

                        if record.id is None:
                            stats['created'] += 1
                        else:
                            stats['updated'] += 1

                except Exception as e:
                    logger.error(f"处理规则 {rule.community_rule_id} 时出错: {str(e)}")
                    stats['errors'] += 1
                    continue

            # 提交更改
            db.session.commit()
            logger.info(f"异常值计算完成: {stats}")

        except Exception as e:
            db.session.rollback()
            logger.error(f"计算异常值时发生错误: {str(e)}", exc_info=True)
            stats['errors'] += 1

        return stats

    @staticmethod
    def get_user_total_abnormality(user_id: int, target_date: Optional[date] = None) -> int:
        """
        获取用户在指定日期的总异常值（所有未完成规则的异常值之和）

        Args:
            user_id: 用户ID
            target_date: 目标日期，默认为今天

        Returns:
            总异常值
        """
        if target_date is None:
            target_date = date.today()

        stmt = select(db.func.coalesce(db.func.sum(UserDailyAbnormality.total_abnormality), 0)).where(
            and_(
                UserDailyAbnormality.user_id == user_id,
                UserDailyAbnormality.date == target_date,
                UserDailyAbnormality.is_completed == False  # 只计算未完成的规则
            )
        )

        result = db.session.execute(stmt).scalar()
        return int(result) if result is not None else 0

    @staticmethod
    def get_abnormal_users(community_id: int, target_date: Optional[date] = None) -> List[Dict]:
        """
        获取社区中的异常用户列表

        Args:
            community_id: 社区ID
            target_date: 目标日期，默认为今天

        Returns:
            异常用户列表
        """
        if target_date is None:
            target_date = date.today()

        # 获取社区的规则总数
        rule_count_stmt = select(db.func.count(CommunityCheckinRule.community_rule_id)).where(
            and_(
                CommunityCheckinRule.community_id == community_id,
                CommunityCheckinRule.status == 1
            )
        )
        rule_count = db.session.execute(rule_count_stmt).scalar()

        if rule_count == 0:
            return []

        # 查询异常用户
        stmt = select(
            User.user_id,
            User.nickname,
            User.avatar_url,
            db.func.coalesce(db.func.sum(UserDailyAbnormality.total_abnormality), 0).label('total_abnormality')
        ).join(
            UserDailyAbnormality, User.user_id == UserDailyAbnormality.user_id
        ).where(
            and_(
                User.community_id == community_id,
                User.status == 1,  # 正常状态
                UserDailyAbnormality.date == target_date,
                UserDailyAbnormality.is_completed == False
            )
        ).group_by(
            User.user_id, User.nickname, User.avatar_url
        ).having(
            db.func.sum(UserDailyAbnormality.total_abnormality) >= rule_count
        ).order_by(
            db.desc('total_abnormality')
        )

        results = db.session.execute(stmt).all()

        abnormal_users = []
        for row in results:
            abnormal_users.append({
                'user_id': row.user_id,
                'nickname': row.nickname,
                'avatar_url': row.avatar_url,
                'total_abnormality': int(row.total_abnormality)
            })

        return abnormal_users
