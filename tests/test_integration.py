# tests/test_integration.py
def test_complete_counter_workflow(client):
    """Test a complete workflow: get initial value, increment, get updated value, clear."""
    # 1. Get initial count (should be 0)
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['data'] == 0
    
    # 2. Increment the count
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['data'] == 1
    
    # 3. Get the updated count
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['data'] == 1
    
    # 4. Increment again
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['data'] == 2
    
    # 5. Clear the count - make_succ_empty_response returns code 1 with empty data object
    response = client.post('/api/count', json={'action': 'clear'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1  # make_succ_empty_response returns code 1
    assert data['data'] == {}  # make_succ_empty_response returns empty object
    
    # 6. Verify count is back to 0
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 1
    assert data['data'] == 0