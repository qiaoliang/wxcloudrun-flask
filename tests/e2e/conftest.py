
import os
import sys
import pytest
import subprocess
import time
import requests
import tempfile
import socket

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))
sys.path.insert(0, project_root)

def get_free_port():
    with socket.create_server(('localhost', 0)) as s:
        return s.getsockname()[1]

@pytest.fixture(scope='function')
def test_server():
    print('\n=== 启动 Flask 测试服务器 ===')
    
    port = get_free_port()
    base_url = f'http://localhost:{port}'
    
    # Set up environment
    env = os.environ.copy()
    env['ENV_TYPE'] = 'unit'
    temp_db = tempfile.mktemp(suffix='.db')
    env['SQLITE_DB_PATH'] = temp_db
    env['PYTHONPATH'] = project_root
    
    process = None
    try:
        process = subprocess.Popen(
            [sys.executable, 'main.py', 'localhost', str(port)],
            cwd=project_root,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for server
        for _ in range(30):
            try:
                response = requests.get(f'{base_url}/api/count', timeout=2)
                if response.status_code == 200:
                    break
            except:
                time.sleep(1)
        else:
            raise RuntimeError('Server failed to start')
        
        yield base_url
        
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        if os.path.exists(temp_db):
            os.unlink(temp_db)
