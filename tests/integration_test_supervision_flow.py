"""
监督流程集成测试模块：使用统一的 docker-compose 环境并测试监督相关功能
"""
import os
import time
import requests
import subprocess
import pytest
import jwt
import datetime


@pytest.mark.integration
def test_supervision_flow_complete(docker_compose_env: str):
    """
    测试完整的监督流程：创建规则 -> 邀请监护人 -> 接受邀请 -> 查看监督关系
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 步骤1：创建用户并获取token
    # 创建独居者用户
    solo_user_data = {
        "phone_number": "13800138000",
        "nickname": "测试独居者",
        "role": "solo"
    }
    response = requests.post(f"{base_url}/api/register", json=solo_user_data)
    assert response.status_code == 200
    solo_login_response = requests.post(f"{base_url}/api/login_phone", 
                                       json={"phone": "13800138000", "code": "123456"})
    assert solo_login_response.status_code == 200
    solo_token = solo_login_response.json()['data']['token']
    
    # 创建监护人用户
    supervisor_data = {
        "phone_number": "13800138001",
        "nickname": "测试监护人",
        "role": "supervisor"
    }
    response = requests.post(f"{base_url}/api/register", json=supervisor_data)
    assert response.status_code == 200
    supervisor_login_response = requests.post(f"{base_url}/api/login_phone",
                                            json={"phone": "13800138001", "code": "123456"})
    assert supervisor_login_response.status_code == 200
    supervisor_token = supervisor_login_response.json()['data']['token']
    
    # 步骤2：创建打卡规则
    rule_data = {
        "rule_name": "起床打卡",
        "icon_url": "🌅",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "08:00:00",
        "week_days": 127,
        "status": 1
    }
    response = requests.post(f"{base_url}/api/checkin/rules",
                           headers={"Authorization": f"Bearer {solo_token}"},
                           json=rule_data)
    assert response.status_code == 200
    rule_id = response.json()['data']['rule_id']
    
    # 步骤3：邀请监护人
    # 首先搜索监护人用户
    response = requests.get(f"{base_url}/api/users/search?phone=13800138001",
                          headers={"Authorization": f"Bearer {solo_token}"})
    assert response.status_code == 200
    supervisor_user_id = response.json()['data']['users'][0]['user_id']
    
    invitation_data = {
        "rule_id": rule_id,
        "supervisor_user_id": supervisor_user_id,
        "invitation_message": "请监督我起床打卡"
    }
    response = requests.post(f"{base_url}/api/rules/supervision/invite",
                           headers={"Authorization": f"Bearer {solo_token}"},
                           json=invitation_data)
    assert response.status_code == 200
    rule_supervision_id = response.json()['data']['rule_supervision_id']
    
    # 步骤4：监护人接受邀请
    response = requests.post(f"{base_url}/api/supervision/respond",
                           headers={"Authorization": f"Bearer {supervisor_token}"},
                           json={
                               "rule_supervision_id": rule_supervision_id,
                               "action": "accept"
                           })
    assert response.status_code == 200
    
    # 步骤5：查看监督关系
    # 独居者查看发送的邀请
    response = requests.get(f"{base_url}/api/supervision/invitations/sent",
                          headers={"Authorization": f"Bearer {solo_token}"})
    assert response.status_code == 200
    invitations = response.json()['data']['invitations']
    assert len(invitations) > 0
    assert invitations[0]['status'] == 1  # 已接受
    
    # 监护人查看接受的邀请
    response = requests.get(f"{base_url}/api/supervision/invitations/received",
                          headers={"Authorization": f"Bearer {supervisor_token}"})
    assert response.status_code == 200
    invitations = response.json()['data']['invitations']
    assert len(invitations) > 0
    assert invitations[0]['status'] == 1  # 已接受
    
    print("监督流程测试通过！")


@pytest.mark.integration
def test_supervision_rejection_flow(docker_compose_env: str):
    """
    测试拒绝邀请的监督流程
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 创建测试用户
    solo_user_data = {
        "phone_number": "13800138002",
        "nickname": "测试独居者2",
        "role": "solo"
    }
    response = requests.post(f"{base_url}/api/register", json=solo_user_data)
    assert response.status_code == 200
    
    supervisor_user_data = {
        "phone_number": "13800138003",
        "nickname": "测试监护人2",
        "role": "supervisor"
    }
    response = requests.post(f"{base_url}/api/register", json=supervisor_user_data)
    assert response.status_code == 200
    
    # 获取token
    solo_login_response = requests.post(f"{base_url}/api/login_phone",
                                       json={"phone": "13800138002", "code": "123456"})
    solo_token = solo_login_response.json()['data']['token']
    
    supervisor_login_response = requests.post(f"{base_url}/api/login_phone",
                                            json={"phone": "13800138003", "code": "123456"})
    supervisor_token = supervisor_login_response.json()['data']['token']
    
    # 创建规则和邀请
    rule_data = {
        "rule_name": "早餐打卡",
        "icon_url": "🍳",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "08:00:00",
        "week_days": 127,
        "status": 1
    }
    response = requests.post(f"{base_url}/api/checkin/rules",
                           headers={"Authorization": f"Bearer {solo_token}"},
                           json=rule_data)
    rule_id = response.json()['data']['rule_id']
    
    # 搜索监护人
    response = requests.get(f"{base_url}/api/users/search?phone=13800138003",
                          headers={"Authorization": f"Bearer {solo_token}"})
    supervisor_user_id = response.json()['data']['users'][0]['user_id']
    
    # 发送邀请
    invitation_data = {
        "rule_id": rule_id,
        "supervisor_user_id": supervisor_user_id,
        "invitation_message": "请监督我早餐打卡"
    }
    response = requests.post(f"{base_url}/api/rules/supervision/invite",
                           headers={"Authorization": f"Bearer {solo_token}"},
                           json=invitation_data)
    rule_supervision_id = response.json()['data']['rule_supervision_id']
    
    # 监护人拒绝邀请
    response = requests.post(f"{base_url}/api/supervision/respond",
                           headers={"Authorization": f"Bearer {supervisor_token}"},
                           json={
                               "rule_supervision_id": rule_supervision_id,
                               "action": "reject"
                           })
    assert response.status_code == 200
    
    # 验证邀请状态为已拒绝
    response = requests.get(f"{base_url}/api/supervision/invitations/received",
                          headers={"Authorization": f"Bearer {supervisor_token}"})
    invitations = response.json()['data']['invitations']
    assert len(invitations) > 0
    assert invitations[0]['status'] == 2  # 已拒绝
    
    print("拒绝邀请流程测试通过！")


@pytest.mark.integration
def test_multiple_supervisors_flow(docker_compose_env: str):
    """
    测试多个监护人的场景
    :param docker_compose_env: docker-compose 环境 fixture
    """
    base_url = docker_compose_env
    
    # 创建一个独居者和多个监护人
    users = [
        {"phone_number": "13800138004", "nickname": "独居者", "role": "solo"},
        {"phone_number": "13800138005", "nickname": "监护人1", "role": "supervisor"},
        {"phone_number": "13800138006", "nickname": "监护人2", "role": "supervisor"},
        {"phone_number": "13800138007", "nickname": "监护人3", "role": "supervisor"}
    ]
    
    tokens = {}
    for user in users:
        response = requests.post(f"{base_url}/api/register", json=user)
        assert response.status_code == 200
        
        login_response = requests.post(f"{base_url}/api/login_phone",
                                     json={"phone": user["phone_number"], "code": "123456"})
        assert login_response.status_code == 200
        tokens[user["phone_number"]] = login_response.json()['data']['token']
    
    # 创建规则
    rule_data = {
        "rule_name": "服药打卡",
        "icon_url": "💊",
        "frequency_type": 0,
        "time_slot_type": 4,
        "custom_time": "20:00:00",
        "week_days": 127,
        "status": 1
    }
    response = requests.post(f"{base_url}/api/checkin/rules",
                           headers={"Authorization": f"Bearer {tokens['13800138004']}"},
                           json=rule_data)
    rule_id = response.json()['data']['rule_id']
    
    # 邀请所有监护人
    supervisor_ids = []
    for phone in ["13800138005", "13800138006", "13800138007"]:
        response = requests.get(f"{base_url}/api/users/search?phone={phone}",
                              headers={"Authorization": f"Bearer {tokens['13800138004']}"})
        supervisor_ids.append(response.json()['data']['users'][0]['user_id'])
    
    # 发送邀请
    for supervisor_id in supervisor_ids:
        invitation_data = {
            "rule_id": rule_id,
            "supervisor_user_id": supervisor_id,
            "invitation_message": "请监督我服药"
        }
        response = requests.post(f"{base_url}/api/rules/supervision/invite",
                               headers={"Authorization": f"Bearer {tokens['13800138004']}"},
                               json=invitation_data)
        assert response.status_code == 200
    
    # 部分监护人接受邀请
    # 监护人1接受
    response = requests.get(f"{base_url}/api/supervision/invitations/received",
                          headers={"Authorization": f"Bearer {tokens['13800138005']}"})
    rule_supervision_id = response.json()['data']['invitations'][0]['rule_supervision_id']
    
    response = requests.post(f"{base_url}/api/supervision/respond",
                           headers={"Authorization": f"Bearer {tokens['13800138005']}"},
                           json={
                               "rule_supervision_id": rule_supervision_id,
                               "action": "accept"
                           })
    assert response.status_code == 200
    
    # 监护人2接受
    response = requests.get(f"{base_url}/api/supervision/invitations/received",
                          headers={"Authorization": f"Bearer {tokens['13800138006']}"})
    rule_supervision_id = response.json()['data']['invitations'][0]['rule_supervision_id']
    
    response = requests.post(f"{base_url}/api/supervision/respond",
                           headers={"Authorization": f"Bearer {tokens['13800138006']}"},
                           json={
                               "rule_supervision_id": rule_supervision_id,
                               "action": "accept"
                           })
    assert response.status_code == 200
    
    # 监护人3拒绝
    response = requests.get(f"{base_url}/api/supervision/invitations/received",
                          headers={"Authorization": f"Bearer {tokens['13800138007']}"})
    rule_supervision_id = response.json()['data']['invitations'][0]['rule_supervision_id']
    
    response = requests.post(f"{base_url}/api/supervision/respond",
                           headers={"Authorization": f"Bearer {tokens['13800138007']}"},
                           json={
                               "rule_supervision_id": rule_supervision_id,
                               "action": "reject"
                           })
    assert response.status_code == 200
    
    # 验证监督关系
    response = requests.get(f"{base_url}/api/supervision/invitations/sent",
                          headers={"Authorization": f"Bearer {tokens['13800138004']}"})
    invitations = response.json()['data']['invitations']
    
    accepted_count = sum(1 for inv in invitations if inv['status'] == 1)
    rejected_count = sum(1 for inv in invitations if inv['status'] == 2)
    
    assert accepted_count == 2
    assert rejected_count == 1
    
    print("多监护人流程测试通过！")