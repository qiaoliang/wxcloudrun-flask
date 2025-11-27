# tests/test_model.py
import pytest
from datetime import datetime
from wxcloudrun.model import Counters


def test_counter_model_creation(client):
    """Test creating a Counter model instance."""
    counter = Counters()
    counter.id = 1
    counter.count = 42
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    
    assert counter.id == 1
    assert counter.count == 42
    assert counter.created_at is not None
    assert counter.updated_at is not None
    assert counter.__tablename__ == 'Counters'