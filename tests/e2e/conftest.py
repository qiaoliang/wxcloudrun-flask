"""
E2E测试的pytest配置文件
提供共享的Flask应用实例以避免重复启动
"""
import os
import sys
import time
import signal
import subprocess
import requests
import pytest


def start_flask_app():
    """启动Flask应用并返回进程对象"""
    # 设置环境变量为unit，使用内存数据库确保测试隔离
    os.environ['ENV_TYPE'] = 'unit'
    
    # 确保 src 目录在 Python 路径中
    src_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src')
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    
    # 清理可能存在的进程
    cleanup_existing_processes()
    
    # 启动 Flask 应用（在后台运行）
    flask_process = subprocess.Popen(
        [sys.executable, 'main.py', '127.0.0.1', '9998'],
        cwd=src_path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=os.environ.copy()
    )
    
    # 等待应用启动
    time.sleep(5)
    
    # 验证应用是否成功启动
    max_attempts = 10
    for attempt in range(max_attempts):
        try:
            response = requests.get('http://localhost:9998/', timeout=2)
            if response.status_code == 200:
                print(f"Flask 应用成功启动 (尝试 {attempt + 1}/{max_attempts})")
                return flask_process
        except requests.exceptions.RequestException:
            if attempt == max_attempts - 1:
                flask_process.terminate()
                try:
                    flask_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    flask_process.kill()
                    flask_process.wait()
                pytest.fail("Flask 应用启动失败")
            time.sleep(1)


def cleanup_existing_processes():
    """清理可能存在的 Flask 进程"""
    try:
        # 查找占用端口 9998 的进程
        result = subprocess.run(['lsof', '-t', '-i:9998'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(['kill', '-9', pid], capture_output=True)
                    print(f"已终止进程 {pid}")
    except Exception as e:
        print(f"清理进程时出错: {e}")


@pytest.fixture(scope='session')
def shared_flask_app():
    """Session级别的fixture，为所有e2e测试提供共享的Flask应用"""
    print("启动共享的Flask应用...")
    flask_process = start_flask_app()
    
    # 提供应用信息
    app_info = {
        'base_url': 'http://localhost:9998',
        'process': flask_process
    }
    
    yield app_info
    
    # 测试结束后清理
    print("关闭共享的Flask应用...")
    if flask_process:
        flask_process.terminate()
        try:
            flask_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            flask_process.kill()
            flask_process.wait()
    
    # 再次清理可能残留的进程
    cleanup_existing_processes()


@pytest.fixture(scope='function')
def base_url(shared_flask_app):
    """为每个测试提供base_url"""
    return shared_flask_app['base_url']
