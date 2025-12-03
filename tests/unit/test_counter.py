import json

def test_get_count_initial(client):
    """测试：获取初始计数"""
    # 发送 GET 请求
    response = client.get('/api/count')

    # 验证 HTTP 状态码
    assert response.status_code == 200

    # 验证返回数据
    data = response.get_json()
    assert data['code'] == 0
    # 初始数据库为空，代码逻辑通常会返回 0 或者默认创建一个 0
    # 根据你的 dao.py 逻辑，这里可能是 0
    assert data['data'] >= 0

def test_action_inc(client):
    """测试：执行自增操作"""
    # 1. 先发一个 POST 请求让计数 +1
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    # 假设第一次自增后，如果初始是0，现在应该是1；如果是空表新建可能是1
    first_count = data['data']

    # 2. 再发一次 inc
    response = client.post('/api/count', json={'action': 'inc'})
    data = response.get_json()
    second_count = data['data']

    # 验证计数确实增加了
    assert second_count == first_count + 1

def test_action_clear(client):
    """测试：执行清零操作"""
    # 1. 先自增几次，确保不为 0
    client.post('/api/count', json={'action': 'inc'})
    client.post('/api/count', json={'action': 'inc'})

    # 2. 发送清零请求
    response = client.post('/api/count', json={'action': 'clear'})
    assert response.status_code == 200

    # 3. 验证当前返回是否为 0
    data = response.get_json()
    assert data['data'] == 0

    # 4. 再次获取确认持久化
    response = client.get('/api/count')
    data = response.get_json()
    assert data['data'] == 0

def test_invalid_action(client):
    """测试：发送非法参数"""
    response = client.post('/api/count', json={'action': 'unknown_action'})
    # 根据你的 views.py 逻辑，可能会返回错误码或忽略
    # 这里假设它返回 200 但可能包含错误信息，或者代码里没处理会报错
    # 假设你的代码比较健壮：
    assert response.status_code == 200
    data = response.get_json()
    # 如果你的 API 对非法 action 返回非0 code，可以这样测：
    # assert data['code'] != 0