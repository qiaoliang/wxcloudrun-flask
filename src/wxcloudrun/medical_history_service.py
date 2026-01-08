"""
用户病史信息服务
"""
import json
from datetime import datetime
from sqlalchemy import select
from database.flask_models import db, User, UserMedicalHistory
from const_default import DEFAULT_COMMUNITY_ID


class MedicalHistoryService:
    """用户病史信息服务类"""

    # 常见病史标签
    COMMON_CONDITIONS = [
        "高血压", "糖尿病", "心脏病", "冠心病", "脑卒中",
        "骨质疏松", "阿尔茨海默病", "帕金森病", "抑郁症",
        "失眠症", "关节炎", "白内障", "青光眼"
    ]

    @staticmethod
    def add_medical_history(user_id, condition_name, treatment_plan, visibility=1, operator_id=None):
        """添加病史记录"""
        user = db.session.get(User, user_id)
        if not user:
            raise ValueError("用户不存在")

        history = UserMedicalHistory(
            user_id=user_id,
            condition_name=condition_name,
            treatment_plan=json.dumps(treatment_plan, ensure_ascii=False) if treatment_plan else None,
            visibility=visibility
        )

        db.session.add(history)
        db.session.flush()

        return history.to_dict()

    @staticmethod
    def update_medical_history(history_id, user_id, condition_name=None, treatment_plan=None, visibility=None, operator_id=None):
        """更新病史记录"""
        history = db.session.execute(
            select(UserMedicalHistory).where(
                UserMedicalHistory.id == history_id,
                UserMedicalHistory.user_id == user_id
            )
        ).scalar_one_or_none()

        if not history:
            raise ValueError("病史记录不存在")

        if condition_name:
            history.condition_name = condition_name
        if treatment_plan is not None:
            history.treatment_plan = json.dumps(treatment_plan, ensure_ascii=False)
        if visibility is not None:
            history.visibility = visibility

        history.updated_at = datetime.now()
        db.session.flush()

        return history.to_dict()

    @staticmethod
    def delete_medical_history(history_id, user_id, operator_id=None):
        """删除病史记录"""
        history = db.session.execute(
            select(UserMedicalHistory).where(
                UserMedicalHistory.id == history_id,
                UserMedicalHistory.user_id == user_id
            )
        ).scalar_one_or_none()

        if not history:
            raise ValueError("病史记录不存在")

        db.session.delete(history)
        db.session.flush()

        return {'success': True}

    @staticmethod
    def get_user_medical_histories(user_id, viewer_id=None):
        """获取用户病史列表（带权限过滤）"""
        # 获取病史记录
        stmt = select(UserMedicalHistory).where(
            UserMedicalHistory.user_id == user_id
        ).order_by(UserMedicalHistory.created_at.desc())

        histories = db.session.execute(stmt).scalars().all()

        # 权限过滤
        result = []
        for history in histories:
            history_dict = history.to_dict()

            # 检查权限
            can_view = MedicalHistoryService._check_visibility_permission(
                history_dict, user_id, viewer_id
            )

            if can_view:
                result.append(history_dict)

        return result

    @staticmethod
    def _check_visibility_permission(history_dict, user_id, viewer_id):
        """检查查看权限（私有方法）"""
        # 查看自己的病史
        if viewer_id == user_id:
            return True

        # visibility=1: 仅工作人员可见
        # visibility=2: 工作人员和监护人可见
        if history_dict['visibility'] == 1:
            # TODO: 检查 viewer_id 是否是工作人员
            return True  # 暂时返回 True，实际需要检查权限

        if history_dict['visibility'] == 2:
            # TODO: 检查 viewer_id 是否是工作人员或监护人
            return True  # 暂时返回 True，实际需要检查权限

        return False

    @staticmethod
    def get_common_conditions():
        """获取常见病史标签"""
        return MedicalHistoryService.COMMON_CONDITIONS
