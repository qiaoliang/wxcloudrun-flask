# tests/test_dao.py
import pytest
from datetime import datetime
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun import db


def test_query_counterbyid(client):
    """Test querying counter by ID."""
    # Create a counter - let database auto-generate the ID
    counter = Counters()
    counter.count = 5
    insert_counter(counter)
    
    # Get the auto-generated ID
    auto_id = counter.id
    
    # Query the counter
    result = query_counterbyid(auto_id)
    assert result is not None
    assert result.id == auto_id
    assert result.count == 5


def test_insert_counter(client):
    """Test inserting a counter."""
    counter = Counters()
    counter.count = 10
    insert_counter(counter)
    
    # Verify the counter was inserted
    result = query_counterbyid(counter.id)
    assert result is not None
    assert result.id == counter.id
    assert result.count == 10


def test_update_counterbyid(client):
    """Test updating counter by ID."""
    # First insert a counter
    counter = Counters()
    counter.count = 15
    insert_counter(counter)
    
    # Update the counter
    counter.count = 20
    counter.updated_at = datetime.now()
    update_counterbyid(counter)
    
    # Verify the counter was updated
    result = query_counterbyid(counter.id)
    assert result is not None
    assert result.id == counter.id
    assert result.count == 20


def test_delete_counterbyid(client):
    """Test deleting counter by ID."""
    # First insert a counter
    counter = Counters()
    counter.count = 25
    insert_counter(counter)
    
    # Verify it exists
    result = query_counterbyid(counter.id)
    assert result is not None
    
    # Delete the counter
    delete_counterbyid(counter.id)
    
    # Verify it's deleted
    result = query_counterbyid(counter.id)
    assert result is None