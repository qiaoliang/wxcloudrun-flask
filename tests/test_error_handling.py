# tests/test_error_handling.py
def test_count_missing_action(client):
    """Test /api/count endpoint with missing action parameter."""
    response = client.post('/api/count', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert '缺少action参数' in data['data']  # Error message is in data field, not msg


def test_count_invalid_action(client):
    """Test /api/count endpoint with invalid action parameter."""
    response = client.post('/api/count', json={'action': 'invalid_action'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0  # Error response code is 0 based on response.py
    assert 'action参数错误' in data['data']  # Error message is in data field, not msg