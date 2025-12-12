"""
社区管理API测试脚本
用于快速验证新实现的API接口
"""

import requests
import json

# 配置
BASE_URL = "http://localhost:9999"
TOKEN = "your_token_here"  # 请替换为实际的super_admin token

headers = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}


def test_get_community_list():
    """测试获取社区列表"""
    print("\n=== 测试: 获取社区列表 ===")
    url = f"{BASE_URL}/api/community/list"
    params = {"page": 1, "page_size": 20, "status": "all"}
    
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_create_community():
    """测试创建社区"""
    print("\n=== 测试: 创建社区 ===")
    url = f"{BASE_URL}/api/community/create"
    data = {
        "name": "测试社区_" + str(int(time.time())),
        "location": "北京市朝阳区测试街道",
        "description": "这是一个测试社区"
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_staff_list(community_id):
    """测试获取工作人员列表"""
    print(f"\n=== 测试: 获取工作人员列表 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/staff/list"
    params = {"community_id": community_id, "role": "all", "sort_by": "time"}
    
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_add_staff(community_id, user_ids, role="staff"):
    """测试添加工作人员"""
    print(f"\n=== 测试: 添加工作人员 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/add-staff"
    data = {
        "community_id": community_id,
        "user_ids": user_ids,
        "role": role
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_get_community_users(community_id):
    """测试获取社区用户列表"""
    print(f"\n=== 测试: 获取社区用户列表 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/users"
    params = {"community_id": community_id, "page": 1, "page_size": 20}
    
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_add_users(community_id, user_ids):
    """测试添加社区用户"""
    print(f"\n=== 测试: 添加社区用户 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/add-users"
    data = {
        "community_id": community_id,
        "user_ids": user_ids
    }
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_search_users(keyword):
    """测试搜索用户"""
    print(f"\n=== 测试: 搜索用户 (关键词: {keyword}) ===")
    url = f"{BASE_URL}/api/user/search"
    params = {"keyword": keyword}
    
    response = requests.get(url, params=params, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_update_community(community_id, updates):
    """测试更新社区"""
    print(f"\n=== 测试: 更新社区 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/update"
    data = {"community_id": community_id, **updates}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_toggle_status(community_id, status):
    """测试切换社区状态"""
    print(f"\n=== 测试: 切换社区状态 (社区ID: {community_id}, 状态: {status}) ===")
    url = f"{BASE_URL}/api/community/toggle-status"
    data = {"community_id": community_id, "status": status}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_remove_user(community_id, user_id):
    """测试移除社区用户"""
    print(f"\n=== 测试: 移除社区用户 (社区ID: {community_id}, 用户ID: {user_id}) ===")
    url = f"{BASE_URL}/api/community/remove-user"
    data = {"community_id": community_id, "user_id": user_id}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


def test_delete_community(community_id):
    """测试删除社区"""
    print(f"\n=== 测试: 删除社区 (社区ID: {community_id}) ===")
    url = f"{BASE_URL}/api/community/delete"
    data = {"community_id": community_id}
    
    response = requests.post(url, json=data, headers=headers)
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    return response.json()


if __name__ == "__main__":
    import time
    
    print("=" * 60)
    print("社区管理API测试")
    print("=" * 60)
    print("\n⚠️  请先:")
    print("1. 启动后端服务: cd backend && make localrun")
    print("2. 替换上方的 TOKEN 为实际的super_admin token")
    print("3. 运行测试: python test_community_api.py")
    print("\n" + "=" * 60)
    
    # 示例测试流程 (需要先获取有效的token和用户ID)
    # 1. 获取社区列表
    # result = test_get_community_list()
    
    # 2. 创建社区
    # result = test_create_community()
    # community_id = result['data']['community_id']
    
    # 3. 搜索用户
    # result = test_search_users("张")
    
    # 4. 添加工作人员
    # test_add_staff(community_id, ["user_id_1"], role="manager")
    
    # 5. 获取工作人员列表
    # test_get_staff_list(community_id)
    
    # 6. 添加用户
    # test_add_users(community_id, ["user_id_2", "user_id_3"])
    
    # 7. 获取用户列表
    # test_get_community_users(community_id)
    
    # 8. 更新社区
    # test_update_community(community_id, {"description": "更新后的描述"})
    
    # 9. 切换状态
    # test_toggle_status(community_id, "inactive")
    
    # 10. 删除社区
    # test_delete_community(community_id)
    
    print("\n✅ 测试脚本已就绪")
    print("请取消注释上方的测试代码并替换实际参数后运行")