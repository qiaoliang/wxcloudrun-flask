# tests/conftest.py
import pytest
import os
from wxcloudrun import app as original_app, db
from wxcloudrun.model import Counters


@pytest.fixture
def client():
    """Create a test client for the app."""
    # 确保测试环境变量已设置
    os.environ['PYTEST_CURRENT_TEST'] = '1'
    
    app = original_app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # 初始化一个计数器，确保初始值为0
            initial_counter = Counters(count=0)
            db.session.add(initial_counter)
            db.session.commit()
            yield client