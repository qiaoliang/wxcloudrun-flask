#!/usr/bin/env python
"""
集成测试脚本：测试计数器 API 功能
"""

import os
import time
import requests
import subprocess
import sys


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
                print(f"✅ 服务已启动: {url}")
                return True
        except requests.exceptions.RequestException:
            pass
        print(f"⏳ 等待服务启动... {url}")
        time.sleep(2)
    print(f"❌ 服务启动失败: {url}")
    return False


def test_counter_api(base_url: str) -> bool:
    """
    测试计数器 API
    :param base_url: 服务基础 URL
    :return: 测试是否成功
    """
    print("🚀 开始测试计数器 API...")
    print("-" * 40)
    
    # 测试 GET /api/count - 获取初始计数
    print("1. 📥 测试 GET /api/count - 获取初始计数")
    try:
        response = requests.get(f"{base_url}/api/count")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("   ❌ 获取初始计数失败")
            return False
            
        data = response.json()
        print(f"   响应: {data}")
        
        if data['code'] != 1 or not isinstance(data['data'], int):
            print("   ❌ 响应格式错误")
            return False
            
        initial_count = data['data']
        print(f"   ✅ 初始计数: {initial_count}")
        
    except Exception as e:
        print(f"   ❌ 测试 GET /api/count 时出错: {e}")
        return False
    
    # 测试 POST /api/count - 自增操作
    print("\n2. ➕ 测试 POST /api/count - 自增操作")
    try:
        response = requests.post(
            f"{base_url}/api/count",
            json={"action": "inc"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("   ❌ 自增操作失败")
            return False
            
        data = response.json()
        print(f"   响应: {data}")
        
        if data['code'] != 1 or not isinstance(data['data'], int):
            print("   ❌ 响应格式错误")
            return False
            
        incremented_count = data['data']
        print(f"   ✅ 自增后计数: {incremented_count}")
        
        if incremented_count != initial_count + 1:
            print(f"   ❌ 自增结果错误: 期望 {initial_count + 1}, 实际 {incremented_count}")
            return False
        else:
            print(f"   ✅ 自增操作正确: {initial_count} -> {incremented_count}")
            
    except Exception as e:
        print(f"   ❌ 测试 POST /api/count 自增操作时出错: {e}")
        return False
    
    # 测试 POST /api/count - 清零操作
    print("\n3. 🔄 测试 POST /api/count - 清零操作")
    try:
        response = requests.post(
            f"{base_url}/api/count",
            json={"action": "clear"},
            headers={"Content-Type": "application/json"}
        )
        print(f"   状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("   ❌ 清零操作失败")
            return False
            
        data = response.json()
        print(f"   响应: {data}")
        
        if data['code'] != 1:
            print("   ❌ 响应格式错误")
            return False
            
        print("   ✅ 清零操作成功")
        
    except Exception as e:
        print(f"   ❌ 测试 POST /api/count 清零操作时出错: {e}")
        return False
    
    # 再次测试 GET /api/count - 验证清零
    print("\n4. 📥 测试 GET /api/count - 验证清零后状态")
    try:
        response = requests.get(f"{base_url}/api/count")
        print(f"   状态码: {response.status_code}")
        
        if response.status_code != 200:
            print("   ❌ 验证清零失败")
            return False
            
        data = response.json()
        print(f"   响应: {data}")
        
        if data['code'] != 1 or not isinstance(data['data'], int):
            print("   ❌ 响应格式错误")
            return False
            
        final_count = data['data']
        print(f"   ✅ 清零后计数: {final_count}")
        
    except Exception as e:
        print(f"   ❌ 验证清零时出错: {e}")
        return False
    
    print("-" * 40)
    print("🎉 所有计数器 API 测试通过!")
    return True


def main():
    """主函数"""
    print("🧪 开始集成测试...")
    print("=" * 50)
    
    # 检查 docker-compose 文件是否存在
    if not os.path.exists("docker-compose.dev.yml"):
        print("❌ docker-compose.dev.yml 文件不存在")
        return False
        
    # 设置环境变量
    env_vars = {
        "MYSQL_PASSWORD": os.environ.get("MYSQL_PASSWORD", "rootpassword"),
        "WX_APPID": os.environ.get("WX_APPID", "test_appid"),
        "WX_SECRET": os.environ.get("WX_SECRET", "test_secret"),
        "TOKEN_SECRET": os.environ.get("TOKEN_SECRET", "test_token_secret")
    }
    
    # 创建临时的 .env 文件
    env_content = "\n".join([f"{k}={v}" for k, v in env_vars.items()])
    with open(".env.test", "w") as f:
        f.write(env_content)
    
    try:
        # 启动 docker-compose 开发环境
        print("🐳 启动 docker-compose 开发环境...")
        
        # 停止可能存在的服务
        print("🧹 清理现有服务...")
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 启动开发环境
        print("🚀 启动服务...")
        compose_process = subprocess.Popen([
            "docker-compose", "-f", "docker-compose.dev.yml", "up", "--build"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 等待服务启动
        base_url = "http://localhost:8080"
        print(f"⏳ 等待服务在 {base_url} 启动...")
        
        if not wait_for_service(f"{base_url}/", timeout=180):  # 增加超时时间
            print("❌ 服务启动超时")
            return False
        
        # 等待 MySQL 服务完全准备就绪
        print("🔄 等待 MySQL 服务准备就绪...")
        time.sleep(15)
        
        # 执行 API 测试
        test_success = test_counter_api(base_url)
        
        if test_success:
            print("\n✅ 集成测试成功!")
        else:
            print("\n❌ 集成测试失败!")
        
        return test_success
        
    finally:
        # 清理：停止 docker-compose 服务
        print("\n🧹 清理: 停止 docker-compose 服务...")
        subprocess.run([
            "docker-compose", "-f", "docker-compose.dev.yml", "down", "--remove-orphans"
        ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # 删除临时 .env 文件
        if os.path.exists(".env.test"):
            os.remove(".env.test")


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)