import pytest


# 使用标记
@pytest.mark.integration
def test_api_count_persistence(integration_db_setup, integration_app):
    """
    测试：验证数据是否真的持久化到 MySQL 中，而不仅仅是内存。
    """
    with integration_app.test_client() as client:
        # 1. 执行写入操作
        response = client.post('/api/count', json={'action': 'inc'})
        assert response.status_code == 200

        # 2. 验证数据是否在真实数据库中
        with integration_app.app_context():
            from wxcloudrun.model import db, Counters
            count_record = db.session.query(Counters).first()

            assert count_record is not None
            assert count_record.count == 1
