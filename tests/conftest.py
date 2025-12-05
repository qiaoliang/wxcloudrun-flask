"""
Configuration for pytest
"""
import os
import sys
import pytest
from wxcloudrun import app, db


@pytest.fixture
def app_context():
    """Create application context for testing"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['USE_SQLITE_FOR_TESTING'] = 'true'
    os.environ['SQLITE_DB_PATH'] = ':memory:'  # Use in-memory database for testing
    
    with app.app_context():
        yield app


@pytest.fixture
def client(app_context):
    """Create test client"""
    return app_context.test_client()


@pytest.fixture
def runner(app_context):
    """Create test CLI runner"""
    return app_context.test_cli_runner()