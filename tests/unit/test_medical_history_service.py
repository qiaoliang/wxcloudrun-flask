"""
MedicalHistoryService 单元测试
测试病史管理的核心功能
"""
import pytest
from database.flask_models import User, UserMedicalHistory
from test_constants import TEST_CONSTANTS
from test_data_generator import generate_unique_phone_number, generate_unique_openid
from hashlib import sha256


class TestMedicalHistoryService:
    """测试 MedicalHistoryService 方法"""

    def test_add_medical_history_success(self, test_session):
        """
        测试成功添加病史记录
        验证病史记录能正确保存到数据库
        """
        # Arrange - 创建测试用户
        phone_number = generate_unique_phone_number("medical_add")
        user = User(
            wechat_openid=generate_unique_openid(phone_number, "medical_add"),
            phone_number=phone_number,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_add"),
            name=TEST_CONSTANTS.generate_username("medical_add"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number)
        )
        test_session.add(user)
        test_session.commit()

        # Act - 添加病史记录
        from wxcloudrun.medical_history_service import MedicalHistoryService
        result = MedicalHistoryService.add_medical_history(
            user.user_id,
            condition_name="高血压",
            treatment_plan={"medication": "降压药", "dosage": "每日一次"},
            visibility=1
        )

        # Assert - 验证结果
        assert result is not None
        assert result['condition_name'] == "高血压"
        assert result['user_id'] == user.user_id
        assert result['visibility'] == 1

        # 验证病史记录确实被保存到数据库
        test_session.expire_all()
        saved_history = test_session.query(UserMedicalHistory).filter_by(
            user_id=user.user_id).first()
        assert saved_history is not None
        assert saved_history.condition_name == "高血压"

    def test_get_user_medical_histories(self, test_session):
        """
        测试获取用户病史列表
        验证能正确返回用户的所有病史记录
        """
        # Arrange - 创建测试用户并添加多条病史记录
        phone_number = generate_unique_phone_number("medical_get")
        user = User(
            wechat_openid=generate_unique_openid(phone_number, "medical_get"),
            phone_number=phone_number,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_get"),
            name=TEST_CONSTANTS.generate_username("medical_get"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number)
        )
        test_session.add(user)
        test_session.flush()

        from wxcloudrun.medical_history_service import MedicalHistoryService

        # 添加多条病史记录
        MedicalHistoryService.add_medical_history(user.user_id, "高血压", {"medication": "降压药"}, 1)
        MedicalHistoryService.add_medical_history(user.user_id, "糖尿病", {"medication": "胰岛素"}, 1)

        test_session.commit()

        # Act - 获取病史列表
        viewer_id = user.user_id  # 自己查看自己的病史
        histories = MedicalHistoryService.get_user_medical_histories(user.user_id, viewer_id)

        # Assert - 验证结果
        assert histories is not None
        assert len(histories) == 2
        condition_names = [h['condition_name'] for h in histories]
        assert "高血压" in condition_names
        assert "糖尿病" in condition_names

    def test_update_medical_history(self, test_session):
        """
        测试更新病史记录
        验证能正确更新病史信息
        """
        # Arrange - 创建测试用户并添加病史记录
        phone_number = generate_unique_phone_number("medical_update")
        user = User(
            wechat_openid=generate_unique_openid(phone_number, "medical_update"),
            phone_number=phone_number,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_update"),
            name=TEST_CONSTANTS.generate_username("medical_update"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number)
        )
        test_session.add(user)
        test_session.flush()

        from wxcloudrun.medical_history_service import MedicalHistoryService

        # 添加病史记录
        result = MedicalHistoryService.add_medical_history(
            user.user_id, "高血压", {"medication": "降压药"}, 1
        )
        test_session.commit()
        history_id = result['history_id']

        # Act - 更新病史记录
        updated_result = MedicalHistoryService.update_medical_history(
            history_id=history_id,
            user_id=user.user_id,
            condition_name="高血压（已控制）",
            treatment_plan={"medication": "降压药", "dosage": "每日两次", "notes": "血压稳定"},
            visibility=1
        )

        # Assert - 验证结果
        assert updated_result is not None
        assert updated_result['condition_name'] == "高血压（已控制）"

        # 验证数据库中的记录已更新
        test_session.expire_all()
        updated_history = test_session.query(UserMedicalHistory).filter_by(
            history_id=history_id).first()
        assert updated_history is not None
        assert updated_history.condition_name == "高血压（已控制）"

    def test_delete_medical_history(self, test_session):
        """
        测试删除病史记录
        验证能正确删除病史记录
        """
        # Arrange - 创建测试用户并添加病史记录
        phone_number = generate_unique_phone_number("medical_delete")
        user = User(
            wechat_openid=generate_unique_openid(phone_number, "medical_delete"),
            phone_number=phone_number,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_delete"),
            name=TEST_CONSTANTS.generate_username("medical_delete"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number)
        )
        test_session.add(user)
        test_session.flush()

        from wxcloudrun.medical_history_service import MedicalHistoryService

        # 添加病史记录
        result = MedicalHistoryService.add_medical_history(
            user.user_id, "高血压", {"medication": "降压药"}, 1
        )
        test_session.commit()
        history_id = result['history_id']

        # Act - 删除病史记录
        delete_result = MedicalHistoryService.delete_medical_history(history_id, user.user_id)

        # Assert - 验证结果
        assert delete_result is not None
        assert delete_result['success'] is True

        # 验证数据库中的记录已被删除
        test_session.expire_all()
        deleted_history = test_session.query(UserMedicalHistory).filter_by(
            history_id=history_id).first()
        assert deleted_history is None

    def test_get_common_conditions(self):
        """
        测试获取常见病史标签
        验证能返回预定义的常见病史列表
        """
        # Act - 获取常见病史标签
        from wxcloudrun.medical_history_service import MedicalHistoryService
        conditions = MedicalHistoryService.get_common_conditions()

        # Assert - 验证结果
        assert conditions is not None
        assert isinstance(conditions, list)
        assert len(conditions) > 0

        # 验证包含常见的老年病
        common_conditions = ["高血压", "糖尿病", "冠心病", "脑卒中", "骨质疏松"]
        for condition in common_conditions:
            assert condition in conditions, f"常见病史 '{condition}' 应该在列表中"

    def test_medical_history_visibility_control(self, test_session):
        """
        测试病史可见性控制
        验证不同可见性设置下的访问控制
        """
        # Arrange - 创建两个测试用户
        phone_number1 = generate_unique_phone_number("medical_visible_user")
        user1 = User(
            wechat_openid=generate_unique_openid(phone_number1, "medical_visible_user"),
            phone_number=phone_number1,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number1}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_visible_user"),
            name=TEST_CONSTANTS.generate_username("medical_visible_user"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number1)
        )
        test_session.add(user1)

        phone_number2 = generate_unique_phone_number("medical_viewer")
        user2 = User(
            wechat_openid=generate_unique_openid(phone_number2, "medical_viewer"),
            phone_number=phone_number2,
            phone_hash=sha256(f"{TEST_CONSTANTS.PHONE_ENC_SECRET}:{phone_number2}".encode('utf-8')).hexdigest(),
            nickname=TEST_CONSTANTS.generate_nickname("medical_viewer"),
            name=TEST_CONSTANTS.generate_username("medical_viewer"),
            role=1,
            status=1,
            avatar_url=TEST_CONSTANTS.generate_avatar_url(phone_number2)
        )
        test_session.add(user2)
        test_session.flush()

        from wxcloudrun.medical_history_service import MedicalHistoryService

        # 添加不同可见性的病史记录
        # 1 = 仅自己可见
        MedicalHistoryService.add_medical_history(
            user1.user_id, "私密病史", {"medication": "特殊药物"}, 1
        )
        # 2 = 社区专员可见
        MedicalHistoryService.add_medical_history(
            user1.user_id, "普通病史", {"medication": "普通药物"}, 2
        )

        test_session.commit()

        # Act & Assert - 用户自己查看，应该能看到所有病史
        histories_self = MedicalHistoryService.get_user_medical_histories(
            user1.user_id, user1.user_id
        )
        assert len(histories_self) == 2

        # 其他用户查看，应该只能看到可见性为2的病史
        histories_other = MedicalHistoryService.get_user_medical_histories(
            user1.user_id, user2.user_id
        )
        assert len(histories_other) == 1
        assert histories_other[0]['condition_name'] == "普通病史"
