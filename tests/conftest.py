"""
Configuration for pytest
"""
import os
import sys
import pytest
from wxcloudrun import create_app, db


@pytest.fixture
def app():
    """Create application for testing"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['USE_SQLITE_FOR_TESTING'] = 'true'
    os.environ['SQLITE_DB_PATH'] = ':memory:'  # Use in-memory database for testing
    
    app = create_app()
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()