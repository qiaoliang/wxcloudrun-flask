# tests/test_api.py
def test_get_count_initial_value(client):
    """Test getting initial count value."""
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success response has code 1
    assert data['data'] == 0  # Initial count should be 0


def test_post_count_inc(client):
    """Test incrementing count."""
    # First increment
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success response has code 1
    assert data['data'] == 1  # Should be 1 after first increment
    
    # Second increment
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success response has code 1
    assert data['data'] == 2  # Should be 2 after second increment


def test_post_count_clear(client):
    """Test clearing count."""
    # Increment first to set a value
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    
    # Clear the count - returns make_succ_empty_response() which has code 1 and empty data
    response = client.post('/api/count', json={'action': 'clear'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # make_succ_empty_response has code 1
    assert data['data'] == {}  # make_succ_empty_response returns empty object
    
    # Verify count is back to 0
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # Success response has code 1
    assert data['data'] == 0