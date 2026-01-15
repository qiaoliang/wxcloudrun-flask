# DDD 迁移测试策略

**版本**: v1.0
**创建日期**: 2026-01-15
**目标**: 确保 DDD 迁移过程中的质量和稳定性

---

## 目录

1. [测试原则](#测试原则)
2. [测试类型](#测试类型)
3. [测试覆盖率要求](#测试覆盖率要求)
4. [测试工具和框架](#测试工具和框架)
5. [单元测试策略](#单元测试策略)
6. [集成测试策略](#集成测试策略)
7. [端到端测试策略](#端到端测试策略)
8. [性能测试策略](#性能测试策略)
9. [测试数据管理](#测试数据管理)
10. [CI/CD 集成](#cicd-集成)
11. [测试执行计划](#测试执行计划)
12. [测试报告和监控](#测试报告和监控)

---

## 测试原则

### 1. 测试金字塔

```
         E2E Tests (5%)
        /             \
       /               \
      /                 \
     /                   \
    /                     \
   /                       \
  /                         \
 /                           \
/                             \
------------------------------
          Integration Tests (15%)
------------------------------
         Unit Tests (80%)
------------------------------
```

**原则**:
- 80% 单元测试：快速、隔离、可重复
- 15% 集成测试：验证组件间交互
- 5% 端到端测试：验证完整业务流程

### 2. 测试先行

**原则**: 在修改代码前，先编写测试。

**实施**:
- 为旧服务编写集成测试（如有必要）
- 为新 UseCase 编写单元测试
- 确保测试通过后再修改代码

### 3. 测试独立性

**原则**: 每个测试应该独立运行，不依赖其他测试。

**实施**:
- 使用测试数据生成器创建独立数据
- 每个测试使用独立的数据库事务
- 测试之间不共享状态

### 4. 测试可重复性

**原则**: 测试应该可以重复运行，结果一致。

**实施**:
- 使用内存数据库（SQLite in-memory）
- 固定的随机种子
- 清理测试数据

### 5. 测试可维护性

**原则**: 测试代码应该易于理解和维护。

**实施**:
- 清晰的测试命名
- 测试注释说明意图
- 使用测试工具和辅助函数

---

## 测试类型

### 单元测试

**目标**: 验证单个函数、类或模块的行为。

**范围**:
- UseCase 类
- Entity 类
- Value Object 类
- Repository 类
- Service 类（旧服务）

**特点**:
- 快速执行（< 100ms）
- 不依赖外部资源（数据库、网络）
- 使用 Mock 和 Stub

### 集成测试

**目标**: 验证多个组件之间的交互。

**范围**:
- 路由 + UseCase + Repository
- UseCase + 多个 Repository
- Repository + 数据库
- 领域事件 + 事件处理器

**特点**:
- 中等执行时间（< 1s）
- 使用真实数据库（SQLite in-memory）
- 验证组件间协作

### 端到端测试

**目标**: 验证完整的业务流程。

**范围**:
- 用户登录 → 创建社区 → 加入社区 → 创建打卡规则 → 执行打卡
- 用户登录 → 创建事件 → 支持事件 → 关闭事件

**特点**:
- 较长执行时间（< 10s）
- 使用真实 API
- 验证端到端业务流程

### 性能测试

**目标**: 验证系统性能指标。

**范围**:
- API 响应时间
- 数据库查询时间
- 并发请求处理

**特点**:
- 使用性能测试工具
- 基准测试
- 压力测试

---

## 测试覆盖率要求

### 总体要求

- **代码覆盖率**: ≥ 80%
- **分支覆盖率**: ≥ 70%
- **行覆盖率**: ≥ 85%

### 模块级别要求

| 模块 | 代码覆盖率 | 分支覆盖率 | 行覆盖率 | 优先级 |
|------|-----------|-----------|---------|--------|
| UseCase | ≥ 90% | ≥ 80% | ≥ 95% | P0 |
| Entity | ≥ 85% | ≥ 75% | ≥ 90% | P0 |
| Value Object | ≥ 90% | ≥ 80% | ≥ 95% | P0 |
| Repository | ≥ 80% | ≥ 70% | ≥ 85% | P0 |
| Route | ≥ 70% | ≥ 60% | ≥ 75% | P1 |
| Service (旧) | ≥ 70% | ≥ 60% | ≥ 75% | P1 |

### 关键路径要求

- **认证流程**: 100% 覆盖
- **用户管理**: ≥ 90% 覆盖
- **社区管理**: ≥ 85% 覆盖
- **打卡管理**: ≥ 85% 覆盖
- **事件管理**: ≥ 80% 覆盖

---

## 测试工具和框架

### 单元测试

**框架**: pytest

**工具**:
- `pytest`: 测试框架
- `pytest-cov`: 代码覆盖率
- `pytest-mock`: Mock 工具
- `pytest-xdist`: 并行测试执行
- `pytest-asyncio`: 异步测试支持

**配置**:
```ini
# pytest.ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=src/app
    --cov-report=html
    --cov-report=term-missing
    --cov-fail-under=80
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    slow: Slow running tests
```

### 集成测试

**框架**: pytest + SQLAlchemy

**工具**:
- `pytest`: 测试框架
- `pytest-xdist`: 并行测试执行
- `SQLAlchemy`: 数据库 ORM
- `SQLite in-memory`: 内存数据库

**配置**:
```python
# tests/integration/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def db_session():
    """创建内存数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()

    # 创建所有表
    from database.flask_models import Base
    Base.metadata.create_all(engine)

    yield session

    # 清理
    session.close()
    engine.dispose()
```

### 端到端测试

**框架**: pytest + requests

**工具**:
- `pytest`: 测试框架
- `requests`: HTTP 客户端
- `pytest-flask`: Flask 测试工具

**配置**:
```python
# tests/e2e/conftest.py
import pytest
from app import create_app

@pytest.fixture(scope="function")
def client():
    """创建测试客户端"""
    app = create_app(testing=True)
    with app.test_client() as client:
        yield client
```

### 性能测试

**框架**: pytest + pytest-benchmark

**工具**:
- `pytest-benchmark`: 性能测试
- `locust`: 负载测试
- `memory_profiler`: 内存分析

**配置**:
```python
# tests/performance/test_api_performance.py
import pytest

@pytest.mark.benchmark
def test_login_performance(benchmark):
    """测试登录性能"""
    result = benchmark(login, username, password)
    assert result.status_code == 200
```

### Mock 工具

**工具**:
- `unittest.mock`: 标准 Mock 库
- `pytest-mock`: pytest Mock 插件
- `responses`: HTTP Mock

**示例**:
```python
from unittest.mock import Mock, patch

def test_use_case_with_mock():
    # Mock Repository
    mock_repo = Mock()
    mock_repo.get_user.return_value = user_entity

    # Patch
    with patch('app.infrastructure.persistence.repository_factory.RepositoryFactory.get_user_repository', return_value=mock_repo):
        use_case = GetUserUseCase()
        result = use_case.execute(user_id=1)

    assert result.status == UseCaseStatus.SUCCESS
```

---

## 单元测试策略

### UseCase 测试

**测试结构**:
```python
# tests/unit/test_login_wechat_use_case.py
import pytest
from app.application.use_cases.auth.login_wechat_use_case import LoginWeChatUseCase
from app.application.use_cases.base import UseCaseStatus, UseCaseResult
from unittest.mock import Mock, patch

class TestLoginWeChatUseCase:
    """登录用例测试"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return LoginWeChatUseCase()

    @pytest.fixture
    def mock_user_repository(self):
        """Mock 用户仓储"""
        mock_repo = Mock()
        mock_repo.get_user_by_wechat_openid.return_value = None
        return mock_repo

    @pytest.fixture
    def mock_wechat_service(self):
        """Mock 微信服务"""
        mock_service = Mock()
        mock_service.get_openid.return_value = "mock_openid"
        return mock_service

    def test_login_success_with_new_user(self, use_case, mock_user_repository, mock_wechat_service):
        """测试新用户登录成功"""
        # Arrange
        code = "valid_code"
        mock_wechat_service.get_openid.return_value = "new_openid"
        mock_user_repository.get_user_by_wechat_openid.return_value = None

        with patch('app.application.use_cases.auth.login_wechat_use_case.RepositoryFactory.get_user_repository', return_value=mock_user_repository):
            with patch('app.application.use_cases.auth.login_wechat_use_case.WechatService', return_value=mock_wechat_service):
                # Act
                result = use_case.execute(code=code)

                # Assert
                assert result.status == UseCaseStatus.SUCCESS
                assert result.data is not None
                assert 'token' in result.data
                mock_user_repository.save.assert_called_once()

    def test_login_success_with_existing_user(self, use_case, mock_user_repository, mock_wechat_service):
        """测试已有用户登录成功"""
        # Arrange
        code = "valid_code"
        mock_wechat_service.get_openid.return_value = "existing_openid"
        mock_user = Mock()
        mock_user.user_id = 1
        mock_user_repository.get_user_by_wechat_openid.return_value = mock_user

        with patch('app.application.use_cases.auth.login_wechat_use_case.RepositoryFactory.get_user_repository', return_value=mock_user_repository):
            with patch('app.application.use_cases.auth.login_wechat_use_case.WechatService', return_value=mock_wechat_service):
                # Act
                result = use_case.execute(code=code)

                # Assert
                assert result.status == UseCaseStatus.SUCCESS
                assert result.data is not None
                assert 'token' in result.data
                mock_user_repository.save.assert_not_called()

    def test_login_failure_with_invalid_code(self, use_case, mock_wechat_service):
        """测试无效 code 登录失败"""
        # Arrange
        code = "invalid_code"
        mock_wechat_service.get_openid.side_effect = Exception("Invalid code")

        with patch('app.application.use_cases.auth.login_wechat_use_case.WechatService', return_value=mock_wechat_service):
            # Act
            result = use_case.execute(code=code)

            # Assert
            assert result.status == UseCaseStatus.FAILURE
            assert result.message is not None
```

### Entity 测试

**测试结构**:
```python
# tests/unit/test_user_entity.py
import pytest
from app.domain.entities.user_entity import UserEntity
from app.domain.value_objects.role import Role, RoleType

class TestUserEntity:
    """用户实体测试"""

    @pytest.fixture
    def user_entity(self):
        """创建用户实体"""
        return UserEntity(
            user_id=1,
            nickname="Test User",
            phone_number="13800138000",
            role=Role(RoleType.USER),
            status=1
        )

    def test_set_password(self, user_entity):
        """测试设置密码"""
        # Arrange
        password = "test_password"

        # Act
        user_entity.set_password(password)

        # Assert
        assert user_entity.password_hash is not None
        assert user_entity.verify_password(password) is True

    def test_verify_password_with_correct_password(self, user_entity):
        """测试验证正确密码"""
        # Arrange
        password = "test_password"
        user_entity.set_password(password)

        # Act
        result = user_entity.verify_password(password)

        # Assert
        assert result is True

    def test_verify_password_with_incorrect_password(self, user_entity):
        """测试验证错误密码"""
        # Arrange
        password = "test_password"
        user_entity.set_password(password)

        # Act
        result = user_entity.verify_password("wrong_password")

        # Assert
        assert result is False

    def test_is_admin_with_admin_role(self):
        """测试管理员角色"""
        # Arrange
        user_entity = UserEntity(
            user_id=1,
            nickname="Admin",
            phone_number="13800138000",
            role=Role(RoleType.ADMIN),
            status=1
        )

        # Act
        result = user_entity.is_admin()

        # Assert
        assert result is True

    def test_is_admin_with_user_role(self, user_entity):
        """测试普通用户角色"""
        # Act
        result = user_entity.is_admin()

        # Assert
        assert result is False

    def test_can_manage_community_with_staff_role(self):
        """测试工作人员权限"""
        # Arrange
        user_entity = UserEntity(
            user_id=1,
            nickname="Staff",
            phone_number="13800138000",
            role=Role(RoleType.STAFF),
            status=1
        )
        community_id = 1

        # Act
        result = user_entity.can_manage_community(community_id)

        # Assert
        assert result is True
```

### Value Object 测试

**测试结构**:
```python
# tests/unit/test_phone_number.py
import pytest
from app.domain.value_objects.phone_number import PhoneNumber
from app.domain.value_objects.phone_number import InvalidPhoneNumberError

class TestPhoneNumber:
    """手机号值对象测试"""

    def test_create_valid_phone_number(self):
        """测试创建有效手机号"""
        # Arrange
        phone = "13800138000"

        # Act
        phone_number = PhoneNumber(phone)

        # Assert
        assert phone_number.value == phone
        assert phone_number.is_valid() is True

    def test_create_invalid_phone_number_too_short(self):
        """测试创建过短手机号"""
        # Arrange
        phone = "138001380"

        # Act & Assert
        with pytest.raises(InvalidPhoneNumberError):
            PhoneNumber(phone)

    def test_create_invalid_phone_number_too_long(self):
        """测试创建过长手机号"""
        # Arrange
        phone = "138001380000"

        # Act & Assert
        with pytest.raises(InvalidPhoneNumberError):
            PhoneNumber(phone)

    def test_create_invalid_phone_number_invalid_format(self):
        """测试创建无效格式手机号"""
        # Arrange
        phone = "abcdefghijk"

        # Act & Assert
        with pytest.raises(InvalidPhoneNumberError):
            PhoneNumber(phone)

    def test_mask_phone_number(self):
        """测试手机号脱敏"""
        # Arrange
        phone = "13800138000"
        phone_number = PhoneNumber(phone)

        # Act
        masked = phone_number.mask()

        # Assert
        assert masked == "138****8000"

    def test_phone_number_immutability(self):
        """测试手机号不可变性"""
        # Arrange
        phone = "13800138000"
        phone_number = PhoneNumber(phone)

        # Act & Assert
        with pytest.raises(AttributeError):
            phone_number.value = "13900139000"
```

### Repository 测试

**测试结构**:
```python
# tests/unit/test_sqlalchemy_user_repository.py
import pytest
from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
from app.domain.entities.user_entity import UserEntity
from app.domain.value_objects.role import Role, RoleType

class TestSQLAlchemyUserRepository:
    """用户仓储测试"""

    @pytest.fixture
    def repository(self, db_session):
        """创建仓储实例"""
        return SQLAlchemyUserRepository(db_session)

    @pytest.fixture
    def user_entity(self):
        """创建用户实体"""
        return UserEntity(
            user_id=1,
            nickname="Test User",
            phone_number="13800138000",
            role=Role(RoleType.USER),
            status=1
        )

    def test_save_user(self, repository, user_entity):
        """测试保存用户"""
        # Act
        saved_user = repository.save(user_entity)

        # Assert
        assert saved_user.user_id is not None
        assert saved_user.nickname == user_entity.nickname

    def test_get_user_by_id(self, repository, user_entity):
        """测试根据 ID 获取用户"""
        # Arrange
        saved_user = repository.save(user_entity)

        # Act
        found_user = repository.get_by_id(saved_user.user_id)

        # Assert
        assert found_user is not None
        assert found_user.user_id == saved_user.user_id
        assert found_user.nickname == user_entity.nickname

    def test_get_user_by_phone_number(self, repository, user_entity):
        """测试根据手机号获取用户"""
        # Arrange
        saved_user = repository.save(user_entity)

        # Act
        found_user = repository.get_by_phone_number(user_entity.phone_number.value)

        # Assert
        assert found_user is not None
        assert found_user.user_id == saved_user.user_id
        assert found_user.phone_number.value == user_entity.phone_number.value

    def test_update_user(self, repository, user_entity):
        """测试更新用户"""
        # Arrange
        saved_user = repository.save(user_entity)
        saved_user.nickname = "Updated User"

        # Act
        updated_user = repository.save(saved_user)

        # Assert
        assert updated_user.nickname == "Updated User"

    def test_delete_user(self, repository, user_entity):
        """测试删除用户"""
        # Arrange
        saved_user = repository.save(user_entity)

        # Act
        repository.delete(saved_user.user_id)

        # Assert
        found_user = repository.get_by_id(saved_user.user_id)
        assert found_user is None
```

---

## 集成测试策略

### 路由 + UseCase 集成测试

**测试结构**:
```python
# tests/integration/test_auth_routes_integration.py
import pytest
from app import create_app
from database.flask_models import db, User

class TestAuthRoutesIntegration:
    """认证路由集成测试"""

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        app = create_app(testing=True)
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return app.test_client()

    def test_login_wechat_success(self, client):
        """测试微信登录成功"""
        # Arrange
        code = "valid_code"

        # Act
        response = client.post('/api/auth/login/wechat', json={'code': code})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert 'data' in data
        assert 'token' in data['data']

    def test_login_wechat_failure_with_invalid_code(self, client):
        """测试微信登录失败（无效 code）"""
        # Arrange
        code = "invalid_code"

        # Act
        response = client.post('/api/auth/login/wechat', json={'code': code})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] != 0

    def test_refresh_token_success(self, client):
        """测试刷新 Token 成功"""
        # Arrange
        # 先登录获取 token
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        login_data = login_response.get_json()
        refresh_token = login_data['data']['refreshToken']

        # Act
        response = client.post('/api/auth/refresh', json={'refreshToken': refresh_token})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert 'data' in data
        assert 'token' in data['data']

    def test_logout_success(self, client):
        """测试登出成功"""
        # Arrange
        # 先登录获取 token
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        login_data = login_response.get_json()
        token = login_data['data']['token']

        # Act
        response = client.post('/api/auth/logout', headers={'Authorization': f'Bearer {token}'})

        # Assert
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
```

### UseCase + Repository 集成测试

**测试结构**:
```python
# tests/integration/test_create_community_use_case_integration.py
import pytest
from app.application.use_cases.community.create_community_use_case import CreateCommunityUseCase
from app.infrastructure.persistence.repository_factory import RepositoryFactory
from app.application.use_cases.base import UseCaseStatus

class TestCreateCommunityUseCaseIntegration:
    """创建社区用例集成测试"""

    @pytest.fixture
    def use_case(self, db_session):
        """创建 UseCase 实例"""
        return CreateCommunityUseCase()

    @pytest.fixture
    def user_data(self, db_session):
        """创建测试用户"""
        from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository
        from app.domain.entities.user_entity import UserEntity
        from app.domain.value_objects.role import Role, RoleType

        user_repo = SQLAlchemyUserRepository(db_session)
        user = UserEntity(
            nickname="Test User",
            phone_number="13800138000",
            role=Role(RoleType.USER),
            status=1
        )
        saved_user = user_repo.save(user)
        return saved_user

    def test_create_community_success(self, use_case, user_data):
        """测试创建社区成功"""
        # Arrange
        community_data = {
            'name': 'Test Community',
            'description': 'Test Description',
            'address': 'Test Address'
        }

        # Act
        result = use_case.execute(
            user_id=user_data.user_id,
            **community_data
        )

        # Assert
        assert result.status == UseCaseStatus.SUCCESS
        assert result.data is not None
        assert result.data['name'] == community_data['name']
        assert result.data['creator_id'] == user_data.user_id

    def test_create_community_with_invalid_data(self, use_case, user_data):
        """测试创建社区失败（无效数据）"""
        # Arrange
        community_data = {
            'name': '',  # 空名称
            'description': 'Test Description',
            'address': 'Test Address'
        }

        # Act
        result = use_case.execute(
            user_id=user_data.user_id,
            **community_data
        )

        # Assert
        assert result.status == UseCaseStatus.FAILURE
        assert result.message is not None
```

### 领域事件集成测试

**测试结构**:
```python
# tests/integration/test_user_domain_events_integration.py
import pytest
from app.domain.events.user_events import UserCreatedEvent, UserUpdatedEvent
from app.domain.events.event_bus import EventBus

class TestUserDomainEventsIntegration:
    """用户领域事件集成测试"""

    @pytest.fixture
    def event_handler(self):
        """创建事件处理器"""
        events = []

        def handler(event):
            events.append(event)

        return handler, events

    def test_user_created_event_published(self, event_handler):
        """测试用户创建事件发布"""
        # Arrange
        handler, events = event_handler
        EventBus.subscribe(UserCreatedEvent, handler)

        # Act
        event = UserCreatedEvent(aggregate_id=1, data={'name': 'Test User'})
        EventBus.publish(event)

        # Assert
        assert len(events) == 1
        assert events[0].aggregate_id == 1
        assert events[0].data['name'] == 'Test User'

    def test_user_updated_event_published(self, event_handler):
        """测试用户更新事件发布"""
        # Arrange
        handler, events = event_handler
        EventBus.subscribe(UserUpdatedEvent, handler)

        # Act
        event = UserUpdatedEvent(aggregate_id=1, data={'name': 'Updated User'})
        EventBus.publish(event)

        # Assert
        assert len(events) == 1
        assert events[0].aggregate_id == 1
        assert events[0].data['name'] == 'Updated User'

    def test_multiple_event_handlers(self):
        """测试多个事件处理器"""
        # Arrange
        events1 = []
        events2 = []

        def handler1(event):
            events1.append(event)

        def handler2(event):
            events2.append(event)

        EventBus.subscribe(UserCreatedEvent, handler1)
        EventBus.subscribe(UserCreatedEvent, handler2)

        # Act
        event = UserCreatedEvent(aggregate_id=1, data={'name': 'Test User'})
        EventBus.publish(event)

        # Assert
        assert len(events1) == 1
        assert len(events2) == 1
```

---

## 端到端测试策略

### 业务流程测试

**测试结构**:
```python
# tests/e2e/test_community_workflow_e2e.py
import pytest

class TestCommunityWorkflowE2E:
    """社区工作流端到端测试"""

    def test_complete_community_workflow(self, client):
        """测试完整的社区工作流"""
        # 1. 用户登录
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        token = login_data['data']['token']
        user_id = login_data['data']['user']['userId']

        # 2. 创建社区
        create_community_response = client.post(
            '/api/community/create',
            json={
                'name': 'Test Community',
                'description': 'Test Description',
                'address': 'Test Address'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert create_community_response.status_code == 200
        community_data = create_community_response.get_json()
        community_id = community_data['data']['communityId']

        # 3. 加入社区
        join_community_response = client.post(
            f'/api/community/{community_id}/join',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert join_community_response.status_code == 200

        # 4. 创建打卡规则
        create_rule_response = client.post(
            '/api/checkin/rule/create',
            json={
                'communityId': community_id,
                'name': 'Morning Check-in',
                'time': '08:00',
                'frequency': 1
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert create_rule_response.status_code == 200
        rule_data = create_rule_response.get_json()
        rule_id = rule_data['data']['ruleId']

        # 5. 执行打卡
        perform_checkin_response = client.post(
            '/api/checkin/perform',
            json={
                'ruleId': rule_id,
                'location': {'latitude': 39.9, 'longitude': 116.4}
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert perform_checkin_response.status_code == 200

        # 6. 查看今日打卡
        get_checkins_response = client.get(
            '/api/checkin/today',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert get_checkins_response.status_code == 200
        checkins_data = get_checkins_response.get_json()
        assert len(checkins_data['data']) > 0

    def test_event_workflow_e2e(self, client):
        """测试事件工作流"""
        # 1. 用户登录
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        assert login_response.status_code == 200
        login_data = login_response.get_json()
        token = login_data['data']['token']
        user_id = login_data['data']['user']['userId']

        # 2. 创建社区
        create_community_response = client.post(
            '/api/community/create',
            json={
                'name': 'Test Community',
                'description': 'Test Description',
                'address': 'Test Address'
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert create_community_response.status_code == 200
        community_data = create_community_response.get_json()
        community_id = community_data['data']['communityId']

        # 3. 创建事件
        create_event_response = client.post(
            '/api/events/create',
            json={
                'communityId': community_id,
                'type': 'call_for_help',
                'description': 'Help needed',
                'location': {'latitude': 39.9, 'longitude': 116.4}
            },
            headers={'Authorization': f'Bearer {token}'}
        )
        assert create_event_response.status_code == 200
        event_data = create_event_response.get_json()
        event_id = event_data['data']['eventId']

        # 4. 支持事件
        support_event_response = client.post(
            f'/api/events/{event_id}/support',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert support_event_response.status_code == 200

        # 5. 关闭事件
        close_event_response = client.post(
            f'/api/events/{event_id}/close',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert close_event_response.status_code == 200
```

---

## 性能测试策略

### API 响应时间测试

**测试结构**:
```python
# tests/performance/test_api_performance.py
import pytest
import time

class TestAPIPerformance:
    """API 性能测试"""

    def test_login_performance(self, client):
        """测试登录性能"""
        # Arrange
        code = "valid_code"

        # Act
        start_time = time.time()
        response = client.post('/api/auth/login/wechat', json={'code': code})
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 0.5, f"Login took {response_time}s, expected < 0.5s"

    def test_create_community_performance(self, client):
        """测试创建社区性能"""
        # Arrange
        # 先登录
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        login_data = login_response.get_json()
        token = login_data['data']['token']

        community_data = {
            'name': 'Test Community',
            'description': 'Test Description',
            'address': 'Test Address'
        }

        # Act
        start_time = time.time()
        response = client.post(
            '/api/community/create',
            json=community_data,
            headers={'Authorization': f'Bearer {token}'}
        )
        end_time = time.time()

        # Assert
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0, f"Create community took {response_time}s, expected < 1.0s"

    @pytest.mark.benchmark
    def test_checkin_performance_benchmark(self, client, benchmark):
        """测试打卡性能（基准测试）"""
        # Arrange
        # 先登录
        login_response = client.post('/api/auth/login/wechat', json={'code': 'valid_code'})
        login_data = login_response.get_json()
        token = login_data['data']['token']

        checkin_data = {
            'ruleId': 1,
            'location': {'latitude': 39.9, 'longitude': 116.4}
        }

        # Act
        result = benchmark(
            client.post,
            '/api/checkin/perform',
            json=checkin_data,
            headers={'Authorization': f'Bearer {token}'}
        )

        # Assert
        assert result.status_code == 200
```

### 数据库查询性能测试

**测试结构**:
```python
# tests/performance/test_database_performance.py
import pytest
import time
from app.infrastructure.persistence.sqlalchemy_user_repository import SQLAlchemyUserRepository

class TestDatabasePerformance:
    """数据库性能测试"""

    def test_get_user_by_id_performance(self, db_session):
        """测试根据 ID 获取用户性能"""
        # Arrange
        repo = SQLAlchemyUserRepository(db_session)
        user = repo.save(UserEntity(
            nickname="Test User",
            phone_number="13800138000",
            role=Role(RoleType.USER),
            status=1
        ))

        # Act
        start_time = time.time()
        found_user = repo.get_by_id(user.user_id)
        end_time = time.time()

        # Assert
        assert found_user is not None
        query_time = end_time - start_time
        assert query_time < 0.1, f"Query took {query_time}s, expected < 0.1s"

    def test_batch_insert_performance(self, db_session):
        """测试批量插入性能"""
        # Arrange
        repo = SQLAlchemyUserRepository(db_session)
        users = [
            UserEntity(
                nickname=f"User {i}",
                phone_number=f"13800138{i:04d}",
                role=Role(RoleType.USER),
                status=1
            )
            for i in range(100)
        ]

        # Act
        start_time = time.time()
        for user in users:
            repo.save(user)
        end_time = time.time()

        # Assert
        insert_time = end_time - start_time
        assert insert_time < 5.0, f"Batch insert took {insert_time}s, expected < 5.0s"
```

---

## 测试数据管理

### 测试数据生成器

**原则**: 使用随机测试数据，确保测试独立性。

**实现**:
```python
# tests/factories/test_data_factory.py
import random
import string
from faker import Faker

fake = Faker('zh_CN')

class TestDataFactory:
    """测试数据生成器"""

    @staticmethod
    def random_phone_number():
        """生成随机手机号"""
        return f"1{random.choice([3, 5, 7, 8, 9])}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}{random.randint(0, 9)}"

    @staticmethod
    def random_nickname():
        """生成随机昵称"""
        return fake.user_name()

    @staticmethod
    def random_name():
        """生成随机姓名"""
        return fake.name()

    @staticmethod
    def random_address():
        """生成随机地址"""
        return fake.address()

    @staticmethod
    def random_description():
        """生成随机描述"""
        return fake.text(max_nb_chars=200)

    @staticmethod
    def create_user_entity():
        """创建用户实体"""
        from app.domain.entities.user_entity import UserEntity
        from app.domain.value_objects.role import Role, RoleType

        return UserEntity(
            nickname=TestDataFactory.random_nickname(),
            phone_number=TestDataFactory.random_phone_number(),
            role=Role(RoleType.USER),
            status=1
        )

    @staticmethod
    def create_community_entity():
        """创建社区实体"""
        from app.domain.entities.community_entity import CommunityEntity

        return CommunityEntity(
            name=fake.company(),
            description=TestDataFactory.random_description(),
            address=TestDataFactory.random_address()
        )
```

### 测试数据清理

**原则**: 每个测试后清理数据，避免测试间干扰。

**实现**:
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="function")
def db_session():
    """创建内存数据库会话"""
    engine = create_engine("sqlite:///:memory:")
    Session = sessionmaker(bind=engine)
    session = Session()

    # 创建所有表
    from database.flask_models import Base
    Base.metadata.create_all(engine)

    yield session

    # 清理
    session.rollback()
    session.close()
    engine.dispose()
```

---

## CI/CD 集成

### GitHub Actions 配置

**文件**: `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run unit tests
        run: |
          cd backend
          make ut
      - name: Upload coverage reports
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run integration tests
        run: |
          cd backend
          make it

  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run E2E tests
        run: |
          cd backend
          pytest tests/e2e/ -v

  performance-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.12
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd backend
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      - name: Run performance tests
        run: |
          cd backend
          pytest tests/performance/ -v --benchmark-only
```

### 本地测试命令

**Makefile**:
```makefile
# Makefile
.PHONY: test test-unit test-integration test-e2e test-performance test-all test-coverage

test-unit:
	@echo "Running unit tests..."
	ENV_TYPE=unit pytest tests/unit/ -v --cov=src/app --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-integration:
	@echo "Running integration tests..."
	ENV_TYPE=unit pytest tests/integration/ -v --cov=src/app --cov-report=html --cov-report=term-missing --cov-fail-under=70

test-e2e:
	@echo "Running E2E tests..."
	ENV_TYPE=unit pytest tests/e2e/ -v

test-performance:
	@echo "Running performance tests..."
	ENV_TYPE=unit pytest tests/performance/ -v --benchmark-only

test-all:
	@echo "Running all tests..."
	ENV_TYPE=unit pytest tests/ -v --cov=src/app --cov-report=html --cov-report=term-missing --cov-fail-under=80

test-coverage:
	@echo "Generating coverage report..."
	ENV_TYPE=unit pytest tests/ -v --cov=src/app --cov-report=html --cov-report=term-missing
	@echo "Coverage report generated in htmlcov/index.html"
```

---

## 测试执行计划

### 每日测试

**时间**: 每天 00:00 UTC

**内容**:
- 运行所有单元测试
- 运行所有集成测试
- 生成测试覆盖率报告
- 发送测试结果通知

**命令**:
```bash
make test-all
```

### 每周测试

**时间**: 每周日 00:00 UTC

**内容**:
- 运行所有测试（单元、集成、E2E）
- 运行性能测试
- 生成测试报告
- 分析测试趋势

**命令**:
```bash
make test-all
make test-performance
```

### 发布前测试

**时间**: 每次发布前

**内容**:
- 运行所有测试
- 运行性能测试
- 运行安全测试
- 生成完整测试报告

**命令**:
```bash
make test-all
make test-performance
# 安全测试
```

---

## 测试报告和监控

### 测试覆盖率报告

**生成命令**:
```bash
make test-coverage
```

**查看报告**:
```bash
open htmlcov/index.html
```

**要求**:
- 代码覆盖率 ≥ 80%
- 分支覆盖率 ≥ 70%
- 行覆盖率 ≥ 85%

### 性能测试报告

**生成命令**:
```bash
pytest tests/performance/ -v --benchmark-only --benchmark-json=benchmark.json
```

**查看报告**:
```bash
# 使用 pytest-benchmark 的 HTML 报告
pytest tests/performance/ -v --benchmark-only --benchmark-html=benchmark.html
open benchmark.html
```

**要求**:
- API 响应时间 < 500ms（P95）
- 数据库查询时间 < 100ms（P95）
- 内存使用 < 500MB

### 测试趋势监控

**工具**:
- Codecov: 测试覆盖率趋势
- GitHub Actions: 测试通过率趋势
- Grafana: 性能指标趋势

**告警规则**:
- 测试覆盖率下降 > 5%
- 测试失败率 > 5%
- 性能下降 > 20%

---

## 附录

### A. 测试最佳实践

1. **AAA 模式**
   - Arrange: 准备测试数据
   - Act: 执行被测试的方法
   - Assert: 验证结果

2. **测试命名**
   - 使用描述性的测试名称
   - 格式: `test_<功能>_<场景>_<预期结果>`

3. **测试独立性**
   - 每个测试独立运行
   - 不依赖其他测试
   - 使用测试数据生成器

4. **测试可读性**
   - 清晰的测试结构
   - 适当的注释
   - 使用测试工具和辅助函数

### B. 测试模板

**UseCase 测试模板**:
```python
class Test<UseCaseName>:
    """<UseCaseName> 测试"""

    @pytest.fixture
    def use_case(self):
        """创建 UseCase 实例"""
        return <UseCaseName>()

    def test_<场景>_success(self, use_case):
        """测试<场景>成功"""
        # Arrange
        # 准备测试数据

        # Act
        # 执行被测试的方法

        # Assert
        # 验证结果

    def test_<场景>_failure(self, use_case):
        """测试<场景>失败"""
        # Arrange
        # 准备测试数据

        # Act
        # 执行被测试的方法

        # Assert
        # 验证结果
```

**Entity 测试模板**:
```python
class Test<EntityName>:
    """<EntityName> 测试"""

    @pytest.fixture
    def entity(self):
        """创建实体实例"""
        return <EntityName>(...)

    def test_<方法>_success(self, entity):
        """测试<方法>成功"""
        # Arrange
        # 准备测试数据

        # Act
        # 执行被测试的方法

        # Assert
        # 验证结果
```

### C. 测试检查清单

**单元测试检查清单**:
- [ ] 测试覆盖所有公共方法
- [ ] 测试覆盖所有异常情况
- [ ] 测试覆盖所有边界条件
- [ ] 使用 Mock 和 Stub
- [ ] 测试独立运行

**集成测试检查清单**:
- [ ] 测试覆盖所有 API 端点
- [ ] 测试覆盖所有错误场景
- [ ] 测试覆盖所有权限检查
- [ ] 使用真实数据库
- [ ] 测试独立运行

**E2E 测试检查清单**:
- [ ] 测试覆盖所有业务流程
- [ ] 测试覆盖所有关键路径
- [ ] 测试覆盖所有异常流程
- [ ] 使用真实 API
- [ ] 测试独立运行

---

**文档版本**: v1.0
**最后更新**: 2026-01-15
**维护者**: 开发团队