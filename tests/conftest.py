# tests/conftest.py
import pytest
from wxcloudrun import app, db
from wxcloudrun.model import Counters


@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # 初始化一个计数器，确保初始值为0
            initial_counter = Counters(count=0)
            db.session.add(initial_counter)
            db.session.commit()
            yield client