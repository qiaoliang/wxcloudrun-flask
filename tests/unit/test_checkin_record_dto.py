"""
测试 CheckinRecordDTO
"""
import pytest
from datetime import datetime
from app.domain.entities.checkin_record_entity import CheckinRecordEntity, CheckinStatus
from app.application.dtos.checkin_record_dto import CheckinRecordDTO


class TestCheckinRecordDTO:
    """测试CheckinRecordDTO"""

    def test_from_entity_completed_status(self):
        """测试已完成状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.complete(datetime.now())

        result = CheckinRecordDTO.from_entity(entity)

        assert result['record_id'] == 1
        assert result['rule_id'] == 10
        assert result['status'] == 1
        assert result['status_name'] == 'completed'

    def test_from_entity_pending_status(self):
        """测试未打卡状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now(),
            checkin_status=CheckinStatus.PENDING.value
        )

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 0
        assert result['status_name'] == 'pending'

    def test_from_entity_missed_status(self):
        """测试已错过状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.mark_missed()

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 2
        assert result['status_name'] == 'missed'

    def test_from_entity_cancelled_status(self):
        """测试已取消状态转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now()
        )

        entity.cancel()

        result = CheckinRecordDTO.from_entity(entity)

        assert result['status'] == 3
        assert result['status_name'] == 'cancelled'

    def test_from_entity_with_null_checkin_time(self):
        """测试空打卡时间的转换"""
        entity = CheckinRecordEntity.create(
            record_id=1,
            rule_id=10,
            user_id=100,
            planned_checkin_time=datetime.now(),
            checkin_status=CheckinStatus.PENDING.value
        )

        result = CheckinRecordDTO.from_entity(entity)

        assert result['checkin_time'] is None

    def test_from_entity_list(self):
        """测试列表转换"""
        entities = [
            CheckinRecordEntity.create(
                record_id=i,
                rule_id=10,
                user_id=100,
                planned_checkin_time=datetime.now(),
                checkin_status=CheckinStatus.PENDING.value
            ) for i in range(1, 4)
        ]

        entities[0].complete(datetime.now())
        entities[1].mark_missed()
        entities[2].cancel()

        result = CheckinRecordDTO.from_entity_list(entities)

        assert len(result) == 3
        assert result[0]['status_name'] == 'completed'
        assert result[1]['status_name'] == 'missed'
        assert result[2]['status_name'] == 'cancelled'
