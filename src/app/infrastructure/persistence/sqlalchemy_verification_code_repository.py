"""
验证码仓储 SQLAlchemy 实现
"""
from typing import List, Optional
from datetime import datetime, timedelta

from sqlalchemy import select, and_, func
from database.flask_models import db, VerificationCode
from app.domain.repositories.verification_code_repository import VerificationCodeRepository


class SQLAlchemyVerificationCodeRepository(VerificationCodeRepository):
    """验证码仓储 SQLAlchemy 实现"""

    def find_by_id(self, code_id: int) -> Optional[VerificationCode]:
        """
        根据ID查找验证码

        Args:
            code_id: 验证码ID

        Returns:
            验证码对象，如果不存在则返回 None
        """
        return db.session.get(VerificationCode, code_id)

    def find_by_phone_and_purpose(self, phone_number: str, purpose: str) -> Optional[VerificationCode]:
        """
        根据手机号和用途查找验证码

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            验证码对象，如果不存在则返回 None
        """
        query = select(VerificationCode).where(
            VerificationCode.phone_number == phone_number,
            VerificationCode.purpose == purpose
        ).order_by(VerificationCode.created_at.desc())

        result = db.session.execute(query)
        return result.scalar_one_or_none()

    def find_valid_by_phone_and_purpose(self, phone_number: str, purpose: str) -> Optional[VerificationCode]:
        """
        根据手机号和用途查找有效验证码（未过期且未使用）

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            验证码对象，如果不存在则返回 None
        """
        now = datetime.now()

        query = select(VerificationCode).where(
            VerificationCode.phone_number == phone_number,
            VerificationCode.purpose == purpose,
            VerificationCode.expires_at > now,
            VerificationCode.is_used == False
        ).order_by(VerificationCode.created_at.desc())

        result = db.session.execute(query)
        return result.scalar_one_or_none()

    def find_expired_codes(self, before: datetime) -> List[VerificationCode]:
        """
        查找过期的验证码

        Args:
            before: 过期时间点

        Returns:
            验证码列表
        """
        query = select(VerificationCode).where(
            VerificationCode.expires_at < before
        )

        result = db.session.execute(query)
        return list(result.scalars().all())

    def save(self, code: VerificationCode) -> VerificationCode:
        """
        保存验证码

        Args:
            code: 验证码对象

        Returns:
            保存后的验证码对象
        """
        db.session.add(code)
        db.session.flush()
        return code

    def update_last_sent_time(self, code: VerificationCode, sent_time: datetime) -> VerificationCode:
        """
        更新验证码的最后发送时间

        Args:
            code: 验证码对象
            sent_time: 发送时间

        Returns:
            更新后的验证码对象
        """
        code.last_sent_at = sent_time
        code.updated_at = datetime.now()
        db.session.flush()
        return code

    def mark_as_used(self, code: VerificationCode) -> VerificationCode:
        """
        标记验证码为已使用

        Args:
            code: 验证码对象

        Returns:
            更新后的验证码对象
        """
        code.is_used = True
        code.updated_at = datetime.now()
        db.session.flush()
        return code

    def delete(self, code_id: int) -> bool:
        """
        删除验证码

        Args:
            code_id: 验证码ID

        Returns:
            是否删除成功
        """
        code = self.find_by_id(code_id)
        if code:
            db.session.delete(code)
            db.session.flush()
            return True
        return False

    def delete_by_phone_and_purpose(self, phone_number: str, purpose: str) -> bool:
        """
        根据手机号和用途删除验证码

        Args:
            phone_number: 手机号
            purpose: 用途

        Returns:
            是否删除成功
        """
        query = select(VerificationCode).where(
            VerificationCode.phone_number == phone_number,
            VerificationCode.purpose == purpose
        )

        result = db.session.execute(query)
        codes = result.scalars().all()

        for code in codes:
            db.session.delete(code)

        db.session.flush()
        return len(codes) > 0

    def delete_expired_codes(self, before: datetime) -> int:
        """
        删除过期的验证码

        Args:
            before: 过期时间点

        Returns:
            删除的验证码数量
        """
        codes = self.find_expired_codes(before)

        for code in codes:
            db.session.delete(code)

        db.session.flush()
        return len(codes)

    def count_recent_sent(self, phone_number: str, purpose: str, minutes: int = 1) -> int:
        """
        统计最近N分钟内发送的验证码数量

        Args:
            phone_number: 手机号
            purpose: 用途
            minutes: 分钟数

        Returns:
            验证码数量
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        query = select(func.count(VerificationCode.id)).where(
            VerificationCode.phone_number == phone_number,
            VerificationCode.purpose == purpose,
            VerificationCode.last_sent_at >= cutoff_time
        )

        result = db.session.execute(query)
        return result.scalar() or 0