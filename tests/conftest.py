# tests/conftest.py
import os
import time
import requests
import subprocess
import pytest
from typing import Generator

# 在导入应用前设置测试环境变量
os.environ['PYTEST_CURRENT_TEST'] = '1'

from wxcloudrun import app as original_app, db
from wxcloudrun.model import Counters, User, CheckinRule, RuleSupervision


@pytest.fixture(scope="session")
def docker_compose_env() -> Generator[str, None, None]:
    """
    启动 docker-compose 开发环境的 session 级 fixture
    这个 fixture 会在所有测试开始前启动一次，在所有测试结束后停止
    """
    # 检查是否需要运行 Docker 集成测试
    run_docker_integration_tests = os.environ.get("RUN_DOCKER_INTEGRATION_TESTS", "false").lower() == "true"

    if not run_docker_integration_tests:
        # 如果不需要运行 Docker 集成测试，跳过 Docker 启动
        yield "http://localhost:8080"
        return

    # 检查 docker-compose 文件是否存在
    if not os.path.exists("docker-compose.dev.yml"):
        pytest.skip("docker-compose.dev.yml 文件不存在，跳过集成测试")

    # 设置环境变量
    env_vars = {
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", "rootpassword"),
        "WX_APPID": os.environ.get("WX_APPID", "test_appid"),
        "WX_SECRET": os.environ.get("WX_SECRET", "test_secret"),
        "TOKEN_SECRET": "42b32662dc4b61c71eb670d01be317cc830974c2fd0bce818a2febe104cd626f",
        "DOCKER_STARTUP_TIMEOUT": os.environ.get("DOCKER_STARTUP_TIMEOUT", "180")
    }

    # 创建临时的 .env 文件
    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()])
    with open(".env.test", "w") as f:
        f.write(env_content)

    try:
        # 停止可能存在的服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 启动开发环境
        compose_process = subprocess.Popen([
            "docker-compose", "-f", "docker-compose.dev.yml", "up", "--build", "-d"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 获取Docker启动超时时间
        timeout = int(os.environ.get("DOCKER_STARTUP_TIMEOUT", "180"))

        # 等待服务启动
        base_url = "http://localhost:8080"
        if not wait_for_service(f"{base_url}/", timeout=timeout):
            raise RuntimeError("服务启动超时")

        # 等待 MySQL 服务完全准备就绪
        time.sleep(15)

        yield base_url  # 提供服务 URL 给测试用例

    finally:
        # 清理：停止 docker-compose 服务
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 删除临时 .env 文件
        if os.path.exists(".env.test"):
            os.remove(".env.test")


def wait_for_service(url: str, timeout: int = 60) -> bool:
    """
    等待服务启动
    :param url: 服务 URL
    :param timeout: 超时时间（秒）
    :return: 是否成功连接
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(2)
    return False


@pytest.fixture
def client():
    """Create a test client for the app."""
    app = original_app
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            # 初始化一个计数器，确保初始值为0
            initial_counter = Counters(count=0)
            db.session.add(initial_counter)
            db.session.commit()
            yield client


@pytest.fixture
def setup_test_data(client):
    """设置测试数据"""
    app = original_app
    with app.app_context():
        from wxcloudrun.model import db
        session = db.session

        # 创建测试用户
        users = [
            User(
                phone_number='13800000001',
                nickname='用户1',
                is_solo_user=True,
                is_supervisor=False,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000002',
                nickname='监护人1',
                is_solo_user=False,
                is_supervisor=True,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000003',
                nickname='用户3',
                is_solo_user=True,
                is_supervisor=False,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000004',
                nickname='监护人2',
                is_solo_user=False,
                is_supervisor=True,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000005',
                nickname='张三',
                is_solo_user=True,
                is_supervisor=False,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000006',
                nickname='李四',
                is_solo_user=False,
                is_supervisor=True,
                status=1,
                auth_type='phone'
            ),
            User(
                phone_number='13800000007',
                nickname='王五',
                is_solo_user=True,
                is_supervisor=False,
                status=1,
                auth_type='phone'
            )
        ]

        for user in users:
            session.add(user)

        # 创建测试打卡规则
        from datetime import time
        rules = [
            CheckinRule(
                solo_user_id=users[0].user_id,
                rule_name='起床打卡',
                icon_url='🌅',
                frequency_type=0,
                time_slot_type=4,
                custom_time=time(8, 0, 0),
                week_days=127,
                status=1
            ),
            CheckinRule(
                solo_user_id=users[2].user_id,
                rule_name='早餐打卡',
                icon_url='🍳',
                frequency_type=0,
                time_slot_type=4,
                custom_time=time(9, 0, 0),
                week_days=127,
                status=1
            )
        ]

        for rule in rules:
            session.add(rule)

        # 创建监护关系邀请（包括测试中要使用的主要关系）
        invitations = [
            # 用于测试接受邀请 - rule_supervision_id = 1
            RuleSupervision(
                rule_id=rules[0].rule_id,  # 用户1的起床打卡规则
                solo_user_id=users[0].user_id,  # 用户1
                supervisor_user_id=users[1].user_id,  # 监护人1
                status=0,  # 待确认状态
                invitation_message='请监督我起床',
                invited_by_user_id=users[0].user_id
            ),
            # 用于测试拒绝邀请 - rule_supervision_id = 2
            RuleSupervision(
                rule_id=rules[1].rule_id,  # 用户3的早餐打卡规则
                solo_user_id=users[2].user_id,  # 用户3
                supervisor_user_id=users[3].user_id,  # 监护人2
                status=0,  # 待确认状态
                invitation_message='请监督我吃早餐',
                invited_by_user_id=users[2].user_id
            ),
            # 额外的已拒绝邀请（不影响主要测试）
            RuleSupervision(
                rule_id=rules[1].rule_id,
                solo_user_id=users[2].user_id,
                supervisor_user_id=users[1].user_id,
                status=2,  # 已拒绝
                invitation_message='请监督我',
                invited_by_user_id=users[2].user_id
            )
        ]

        for invitation in invitations:
            session.add(invitation)

        session.commit()

        yield users, rules, invitations
    
    # 不需要手动清理，事务会自动回滚