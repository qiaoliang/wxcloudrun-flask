# 集成测试

本目录包含项目的集成测试，这些测试比单元测试更全面，但比端到端（e2e）测试更轻量。

## 设计理念

集成测试旨在：

1. 验证多个组件之间的交互
2. 使用共享的Flask应用实例以提高性能
3. 通过事务回滚保证测试间的隔离性
4. 避免每个测试启动独立进程的开销

## 架构特点

### 1. 共享Flask应用实例
- 使用 `scope="session"` fixture创建单个Flask应用
- 避免重复的应用初始化开销
- 提高测试执行速度

### 2. 数据库事务隔离
- 每个测试使用独立的数据库事务
- 测试结束后自动回滚事务，确保数据隔离
- 避免测试间的数据污染

### 3. 内存数据库
- 使用SQLite内存数据库
- 快速的数据库操作
- 避免对磁盘数据库的影响

## 测试结构

- `conftest.py`: 包含共享的pytest fixtures
- `test_*.py`: 具体的测试文件，按功能模块组织

## 主要Fixtures

### `app`
- 作用域：session
- 创建一次性的Flask应用实例
- 配置为unit环境，使用内存数据库

### `client`
- 作用域：function
- 为每个测试提供HTTP客户端
- 使用共享的Flask应用

### `db_session`
- 作用域：function
- 为每个测试提供数据库会话
- 自动在测试结束时回滚事务

## 使用示例

```python
def test_user_api(client, db_session):
    # 所有API调用都通过client进行
    response = client.get('/api/users')
    assert response.status_code == 200
    
    # 所有数据库操作都通过db_session进行
    # 测试结束后，事务将自动回滚
```

## 最佳实践

1. 使用提供的fixtures而不是直接导入应用
2. 避免在测试中进行长时间的外部调用
3. 每个测试应专注于特定的功能模块
4. 利用数据库事务隔离而不是手动清理数据