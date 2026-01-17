# DDD 架构合规性审查报告

> **审查日期**: 2026-01-17 16:17
> **审查范围**: 后端代码 DDD 架构合规性
> **审查人员**: Claude Code
> **审查方法**: 代码静态分析 + DDD 原则对照

---

## 执行摘要

本次审查对 SafeGuard 后端项目进行了全面的 DDD(Domain-Driven Design) 架构合规性检查,重点审查了最近一次代码提交(278e653)中引入的路由辅助函数和相关模块。

### 审查结论

**总体评估**: ⚠️ **部分符合 DDD 架构原则**

虽然代码已经从 Service 模式迁移到 UseCase 模式,但在**严格的 DDD 实践**上存在严重缺陷:

| 评估维度 | 得分 | 说明 |
|---------|------|------|
| **分层架构** | 6/10 | 基本分层存在,但边界不清晰 |
| **依赖方向** | 4/10 | 存在严重违规,基础设施层泄露到上层 |
| **领域模型** | 5/10 | 使用了聚合根概念,但混用 ORM 模型 |
| **事务管理** | 7/10 | 有事务上下文管理器,但使用不一致 |
| **单一职责** | 6/10 | Controller 层存在职责混乱 |

**关键发现**:
- 🔴 **6 个严重违反 DDD 架构的问题** (P0 级别)
- 🟡 **2 个中等问题** (P1 级别)
- ✅ **5 个做得好的地方**

---

## 审查方法论

### DDD 原则对照清单

本次审查基于以下 DDD 核心原则:

1. **依赖倒置原则 (DIP)**: 高层模块不应依赖低层模块,两者都应依赖抽象
2. **单一职责原则 (SRP)**: 一个类应该只有一个引起它变化的原因
3. **分层架构**: User Interface → Application → Domain ← Infrastructure
4. **聚合根**: 通过聚合根管理领域对象的一致性边界
5. **仓储模式**: 通过抽象接口访问领域对象,隔离持久化细节
6. **事务边界**: UseCase 定义明确的事务边界

### 审查文件范围

```
src/app/
├── modules/
│   ├── checkin/routes.py          # Controller 层
│   └── supervision/routes.py      # Controller 层
├── application/use_cases/
│   ├── base.py                    # UseCase 基类
│   └── checkin/
│       └── perform_checkin_use_case.py
├── domain/
│   ├── repositories/              # 仓储接口
│   ├── entities/                  # 领域实体
│   ├── aggregates/                # 聚合根
│   └── value_objects/             # 值对象
├── infrastructure/
│   └── persistence/
│       ├── repository_factory.py  # 仓储工厂
│       └── sqlalchemy_*.py        # 仓储实现
└── shared/utils/
    └── route_helpers.py           # 路由辅助函数
```

---

## 🔴 严重问题 (P0)

### 问题 1: UseCase 层直接使用数据库模型而非领域实体

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 整个应用层

**问题描述**:

`src/app/application/use_cases/checkin/perform_checkin_use_case.py:109-118`

```python
# ❌ 违规代码
from database.flask_models import CheckinRecord
new_record = CheckinRecord(
    rule_id=rule_id,
    user_id=user_id,
    checkin_time=checkin_time,
    planned_time=datetime.combine(today, planned_time),
    status=1  # 已打卡
)
updated_record = self.checkin_record_repository.save(new_record)
```

**DDD 违规点**:

1. ❌ **违反依赖倒置原则**: UseCase 直接导入和创建基础设施层的 ORM 模型
2. ❌ **领域层被污染**: 应用层依赖持久化层的具体实现
3. ❌ **违反分层架构**: 应该通过领域实体或聚合根操作,而不是直接创建 ORM 模型

**影响**:

- 领域逻辑无法独立于持久化框架
- 单元测试需要 mock ORM 模型
- 更换数据库框架需要修改 UseCase 代码
- 违反 DDD 的战略设计原则

**正确做法**:

```python
# ✅ 符合 DDD 的做法
# 方案 1: 通过聚合根创建
aggregate = CheckinRuleAggregate.from_rule_id(rule_id)
record_entity = aggregate.perform_checkin(user_id, checkin_time)
# 仓储负责将实体转换为持久化模型
updated_record = self.checkin_record_repository.save_entity(record_entity)

# 方案 2: 使用工厂模式
record_entity = CheckinRecordEntity.create(
    rule_id=rule_id,
    user_id=user_id,
    checkin_time=checkin_time
)
self.checkin_record_repository.save(record_entity)
```

**重构建议**:

1. 在 `src/app/domain/entities/checkin_record_entity.py` 中创建领域实体
2. 在仓储接口中定义 `save_entity(entity)` 方法
3. 仓储实现负责实体到 ORM 模型的转换

---

### 问题 2: 仓储返回 ORM 模型而非领域实体

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 领域层被基础设施层污染

**问题描述**:

根据 UseCase 代码推断,仓储层返回的是 SQLAlchemy 模型:

```python
# ❌ 仓储返回 ORM 模型
rule = self.checkin_rule_repository.find_by_id(rule_id)
# rule 是 SQLAlchemy 模型,不是领域实体

if rule.user_id != user_id:  # 直接访问 ORM 模型属性
    return UseCaseResult(...)
```

**DDD 违规点**:

1. ❌ **违反依赖倒置原则**: 领域层和应用层依赖基础设施层的具体实现
2. ❌ **泄漏抽象**: 仓储应该返回领域实体,不应该是 ORM 模型
3. ❌ **违反仓储模式**: 仓储的目的是隔离持久化细节

**影响**:

- 领域逻辑无法独立于数据库框架
- 应用层代码直接依赖 SQLAlchemy
- 领域层无法进行单元测试(需要数据库)
- 违反 DDD 的战术设计原则

**正确做法**:

```python
# ✅ 仓储接口定义领域实体返回类型
class CheckinRuleRepository(ABC):
    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        """
        根据ID查找打卡规则

        Returns:
            Optional[CheckinRuleEntity]: 领域实体,不存在返回 None
        """
        pass

# ✅ 仓储实现返回领域实体
class SQLAlchemyCheckinRuleRepository(CheckinRuleRepository):
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        orm_model = db.session.get(CheckinRule, rule_id)
        if not orm_model:
            return None
        # 转换为领域实体
        return self._to_entity(orm_model)

    def _to_entity(self, orm_model: CheckinRule) -> CheckinRuleEntity:
        return CheckinRuleEntity(
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            # ... 其他属性
        )
```

**重构建议**:

1. 为每个聚合根创建对应的领域实体类
2. 仓储接口的所有方法签名返回领域实体
3. 仓储实现负责 ORM 模型 ↔ 领域实体的转换
4. 更新所有 UseCase 以使用领域实体

---

### 问题 3: Controller 层包含数据转换逻辑

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 违反单一职责原则

**问题描述**:

`src/app/modules/checkin/routes.py:19-41`

```python
# ❌ Controller 层包含领域对象的序列化逻辑
def _rule_to_dict(rule):
    """
    将规则对象转换为字典
    """
    return {
        'rule_id': rule.rule_id,
        'user_id': rule.user_id,
        'community_id': rule.community_id,
        'rule_type': rule.rule_type,
        # ... 数据转换逻辑
    }
```

**DDD 违规点**:

1. ❌ **违反单一职责原则**: Controller 只负责 HTTP 请求/响应,不应处理数据转换
2. ❌ **职责混乱**: 数据序列化逻辑应该在专门的 DTO/Serializer 层
3. ❌ **违反分层架构**: Controller 不应该知道领域对象的结构

**影响**:

- Controller 代码臃肿,难以维护
- 数据转换逻辑无法复用
- 违反关注点分离原则
- 多个 Controller 重复相同转换逻辑

**正确做法**:

```python
# ✅ 创建专门的 DTO 层
# src/app/application/dtos/checkin_rule_dto.py
class CheckinRuleDTO:
    """打卡规则数据传输对象"""

    @staticmethod
    def from_entity(rule: CheckinRuleEntity) -> dict:
        """
        将领域实体转换为字典

        Args:
            rule: 打卡规则领域实体

        Returns:
            dict: API 响应格式
        """
        return {
            'rule_id': rule.rule_id,
            'user_id': rule.user_id,
            'community_id': rule.community_id,
            'rule_type': rule.rule_type,
            'rule_name': rule.rule_name,
            'icon_url': rule.icon_url,
            'frequency_type': rule.frequency_type,
            'time_slot_type': rule.time_slot_type,
            'custom_time': rule.custom_time.isoformat() if rule.custom_time else None,
            'week_days': rule.week_days,
            'custom_start_date': rule.custom_start_date.isoformat() if rule.custom_start_date else None,
            'custom_end_date': rule.custom_end_date.isoformat() if rule.custom_end_date else None,
            'status': rule.status,
            'created_at': rule.created_at.strftime('%Y-%m-%d %H:%M:%S') if rule.created_at else None,
            'updated_at': rule.updated_at.strftime('%Y-%m-%d %H:%M:%S') if rule.updated_at else None
        }

# ✅ Controller 只负责调用 DTO
@checkin_bp.route('/checkin/rules', methods=['GET'])
@with_user_verification
def get_checkin_rules(user_id: int, user: dict):
    result = execute_use_case(GetCheckinRuleUseCase, user_id=user_id, rule_id=None)
    if not result.is_success:
        return make_err_response({}, result.message)

    # 使用 DTO 转换
    rules = result.data.get('rules', [])
    response_data = {
        'rules': [CheckinRuleDTO.from_entity(rule) for rule in rules]
    }
    return make_succ_response(response_data)
```

**重构建议**:

1. 创建 `src/app/application/dtos/` 目录
2. 为每个聚合根创建对应的 DTO 类
3. DTO 负责领域实体 ↔ API 响应格式的转换
4. Controller 只负责调用 DTO 和 UseCase

---

### 问题 4: UseCase 直接操作 ORM 模型属性

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 业务逻辑散落在 UseCase 中

**问题描述**:

`src/app/application/use_cases/checkin/perform_checkin_use_case.py:101-106`

```python
# ❌ 直接修改 ORM 模型状态,没有通过聚合根
for record in today_records:
    if record.status == 0:  # 未打卡
        existing_unchecked = record
        break

if existing_unchecked:
    existing_unchecked.checkin_time = checkin_time  # 直接修改属性
    existing_unchecked.status = 1  # 直接修改属性
    existing_unchecked.updated_at = checkin_time
    updated_record = self.checkin_record_repository.update(existing_unchecked)
```

**DDD 违规点**:

1. ❌ **业务逻辑散落在 UseCase 中**: 状态变更规则应该封装在领域层
2. ❌ **违反封装原则**: 直接修改对象属性,没有通过行为方法
3. ❌ **缺少领域模型**: 没有使用聚合根来管理业务规则

**影响**:

- 业务规则分散,难以维护
- 无法保证业务规则的一致性
- 违反 DDD 的 ubiquitous language 原则
- 缺少领域模型的业务表达力

**正确做法**:

```python
# ✅ 通过聚合根封装业务规则
class CheckinRecordAggregate:
    """打卡记录聚合根"""

    def complete_checkin(self, checkin_time: datetime) -> None:
        """
        完成打卡

        业务规则:
        1. 只能从未打卡状态变更为已打卡
        2. 记录打卡时间和更新时间

        Args:
            checkin_time: 打卡时间

        Raises:
            BusinessRuleError: 如果当前状态不允许完成打卡
        """
        if self._entity.status != CheckinStatus.PENDING:
            raise BusinessRuleError(
                f"无法完成打卡: 当前状态为 {self._entity.status.value}"
            )

        self._entity.checkin_time = checkin_time
        self._entity.status = CheckinStatus.COMPLETED
        self._entity.updated_at = checkin_time

# ✅ UseCase 通过聚合根操作
aggregate = CheckinRecordAggregate.load(record_id)
aggregate.complete_checkin(checkin_time)
self.checkin_record_repository.save_aggregate(aggregate)
```

**重构建议**:

1. 为每个聚合根创建对应的 Aggregate 类
2. 在 Aggregate 中封装业务规则和行为
3. UseCase 通过 Aggregate 的行为方法修改状态
4. 禁止直接修改领域对象的属性

---

### 问题 5: 事务边界不清晰

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 数据一致性风险

**问题描述**:

路由层没有明确的事务边界控制:

```python
# ❌ UseCase 没有显式的事务管理
result = execute_use_case(PerformCheckinUseCase, rule_id=rule_id, user_id=user_id)
# UseCase 内部可能有多个仓储操作,但没有事务保证
```

**DDD 违规点**:

1. ❌ **缺少事务边界**: UseCase 应该定义明确的事务边界
2. ❌ **一致性风险**: 多个仓储操作应该在同一个事务中
3. ❌ **原子性无法保证**: 操作失败时无法回滚

**影响**:

- 数据一致性风险
- 部分更新可能导致数据不一致
- 违反 ACID 原则
- 难以定位和修复数据问题

**正确做法**:

```python
# ✅ UseCase 定义明确的事务边界
class PerformCheckinUseCase(BaseUseCase):
    @transaction  # 使用事务装饰器
    def execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        """
        执行打卡用例

        事务边界: 整个打卡操作在一个事务中
        """
        # 1. 查询规则
        rule = self.checkin_rule_repository.find_by_id(rule_id)
        if not rule:
            return UseCaseResult.fail('打卡规则不存在', UseCaseStatus.NOT_FOUND)

        # 2. 验证权限
        if rule.user_id != user_id:
            return UseCaseResult.fail('无权限操作此打卡规则', UseCaseStatus.FORBIDDEN)

        # 3. 创建打卡记录
        aggregate = CheckinRuleAggregate(rule)
        record = aggregate.perform_checkin(user_id, datetime.now())

        # 4. 保存(在同一个事务中)
        self.checkin_record_repository.save(record)

        # 5. 发布领域事件(事务成功后)
        self.event_publisher.publish(CheckinCompletedEvent(
            record_id=record.record_id,
            user_id=user_id,
            rule_id=rule_id
        ))

        return UseCaseResult.success(data={
            'record_id': record.record_id,
            'checkin_time': record.checkin_time
        })
```

**重构建议**:

1. 为所有 UseCase 添加 `@transaction` 装饰器
2. 定义明确的事务边界
3. 领域事件在事务成功后发布
4. 使用事务上下文管理器确保一致性

---

### 问题 6: 路由层存在重复代码和未使用辅助函数

**严重程度**: 🔴 **Critical**
**优先级**: **P0**
**影响范围**: 代码重复和维护困难

**问题描述**:

`src/app/modules/checkin/routes.py:102-152`

```python
# ❌ 已有 @with_user_verification 装饰器但未使用
@checkin_bp.route('/checkin/miss', methods=['POST'])
def report_miss_checkin():
    # 重复的用户验证逻辑
    decoded, error_response = verify_token()
    if error_response:
        return error_response

    # 重复的用户存在性验证
    user_id = decoded.get('user_id')
    from app.application.use_cases.user import GetUserByIdUseCase
    get_user_use_case = GetUserByIdUseCase()
    user_result = get_user_use_case.execute(user_id=user_id)
    # ... 更多重复代码
```

**DDD 违规点**:

1. ❌ **违反 DRY 原则**: 相同的验证逻辑在多个路由中重复
2. ❌ **代码冗余**: 已有辅助函数但未使用
3. ❌ **维护困难**: 修改验证逻辑需要修改多处

**影响**:

- 代码重复,维护成本高
- 容易出现不一致的行为
- 违反 DRY 原则

**正确做法**:

```python
# ✅ 使用已有的辅助函数
@checkin_bp.route('/checkin/miss', methods=['POST'])
@with_user_verification  # 自动验证 token 和用户存在性
def report_miss_checkin(user_id: int, user: dict):
    # 使用 get_json_params 辅助函数
    params, error_msg = get_json_params(required_fields=['rule_id'])
    if error_msg:
        return make_err_response({}, error_msg)

    rule_id = params.get('rule_id')

    # 执行 UseCase
    result = execute_use_case(
        ReportMissCheckinUseCase,
        rule_id=rule_id,
        user_id=user_id
    )

    if not result.is_success:
        return make_err_response({}, result.message)

    return make_succ_response(result.data)
```

**重构建议**:

1. 审查所有路由函数,统一使用 `@with_user_verification` 装饰器
2. 统一使用 `get_json_params` 辅助函数
3. 统一使用 `execute_use_case` 和 `handle_use_case_result` 辅助函数
4. 删除重复的验证逻辑代码

---

## 🟡 中等问题 (P1)

### 问题 7: 领域事件发布机制不完善

**严重程度**: 🟡 **Medium**
**优先级**: **P1**
**影响范围**: 事件可靠性

**问题描述**:

`src/app/application/use_cases/checkin/perform_checkin_use_case.py:121-143`

```python
# ⚠️ 领域事件发布失败被静默处理
try:
    # 创建聚合根
    rule_entity = CheckinRuleEntity(...)
    aggregate = CheckinRuleAggregate(rule_entity)
    aggregate.complete_checkin(updated_record.record_id, checkin_time)
    self.logger.info(f'发布打卡完成事件: record_id={updated_record.record_id}')
except Exception as e:
    self.logger.warning(f'发布领域事件失败（不影响打卡结果）: {str(e)}')
```

**问题**:

1. ⚠️ **事件发布失败被静默处理**: 可能导致业务流程中断
2. ⚠️ **没有事件持久化机制**: 事件丢失后无法恢复
3. ⚠️ **事件发布应该在事务成功后**: 当前实现在事务内

**正确做法**:

```python
# ✅ 使用事件总线保证事件可靠发布
class PerformCheckinUseCase(BaseUseCase):
    def __init__(self):
        super().__init__()
        self.event_bus = EventBus()  # 事件总线

    @transaction
    def execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        # ... 业务逻辑 ...

        # 事务成功后发布事件
        self.event_bus.publish(
            CheckinCompletedEvent(
                record_id=record.record_id,
                user_id=user_id,
                rule_id=rule_id,
                timestamp=datetime.now()
            )
        )

        return UseCaseResult.success(data=...)
```

**重构建议**:

1. 实现事件总线机制
2. 事件持久化到 Outbox 表
3. 后台任务负责事件可靠投递
4. 事件发布在事务成功后进行

---

### 问题 8: 辅助函数 `execute_use_case` 过度抽象

**严重程度**: 🟡 **Medium**
**优先级**: **P1**
**影响范围**: 代码可读性

**问题描述**:

`src/app/shared/utils/route_helpers.py:85-97`

```python
# ⚠️ 过度抽象,降低了代码可读性
def execute_use_case(use_case_class: type, *args, **kwargs) -> Any:
    use_case = use_case_class()
    return use_case.execute(*args, **kwargs)
```

**问题**:

1. ⚠️ **过度抽象**: 隐藏了 UseCase 的依赖关系
2. ⚠️ **降低可读性**: 不符合 DDD 的明确分层原则
3. ⚠️ **调试困难**: 无法直观看到 UseCase 的实例化过程

**建议**:

```python
# ✅ 直接实例化 UseCase,更加清晰
@checkin_bp.route('/checkin/miss', methods=['POST'])
@with_user_verification
def report_miss_checkin(user_id: int, user: dict):
    use_case = ReportMissCheckinUseCase()  # 显式实例化
    result = use_case.execute(rule_id=rule_id, user_id=user_id)

    if not result.is_success:
        return make_err_response({}, result.message)

    return make_succ_response(result.data)
```

**重构建议**:

1. 评估 `execute_use_case` 的实际价值
2. 如果为了统一异常处理,考虑使用装饰器
3. 优先考虑代码可读性而非过度抽象

---

## ✅ 做得好的地方

1. ✅ **UseCase 基类设计合理**: `BaseUseCase` 提供了良好的模板方法模式
2. ✅ **`UseCaseResult` 统一了返回值**: 符合 CQRS 模式
3. ✅ **仓储接口抽象**: 领域层定义了仓储接口
4. ✅ **聚合根概念应用**: 使用了 `CheckinRuleAggregate` 封装业务逻辑
5. ✅ **移除了 UseCase 之间的相互调用**: 符合单一职责原则

---

## 改进优先级建议

| 优先级 | 问题 | 影响范围 | 预计工作量 | 建议 |
|-------|------|---------|-----------|------|
| **P0** | UseCase 直接使用 ORM 模型 | 整个应用层 | 3-5 天 | 立即修复 |
| **P0** | 仓储返回 ORM 模型 | 领域层被污染 | 3-5 天 | 立即修复 |
| **P1** | Controller 层数据转换逻辑 | 违反单一职责 | 2-3 天 | 尽快修复 |
| **P1** | 事务边界不清晰 | 数据一致性 | 2-3 天 | 尽快修复 |
| **P2** | 统一使用辅助函数 | 代码重复 | 1-2 天 | 计划修复 |
| **P2** | 领域事件机制 | 事件可靠性 | 3-4 天 | 计划修复 |

---

## 实施路线图

### 第一阶段 (P0 问题 - 立即开始)

**目标**: 修复最严重的架构违规,建立 DDD 基础

**任务**:
1. 创建完整的领域实体层
2. 重构仓储层返回领域实体
3. 重构 UseCase 使用领域实体
4. 实现实体 ↔ ORM 模型转换

**预计时间**: 1-2 周

**验收标准**:
- 所有 UseCase 不再直接导入 `database.flask_models`
- 仓储接口方法签名全部返回领域实体
- 单元测试可以在不连接数据库的情况下运行

---

### 第二阶段 (P1 问题 - 紧接着)

**目标**: 完善分层架构,提高代码质量

**任务**:
1. 创建 DTO 层,从 Controller 移除数据转换逻辑
2. 为所有 UseCase 添加事务装饰器
3. 统一路由层使用辅助函数

**预计时间**: 1 周

**验收标准**:
- Controller 层不包含数据转换逻辑
- 所有 UseCase 使用 `@transaction` 装饰器
- 路由层代码重复度降低 50%

---

### 第三阶段 (P2 问题 - 长期改进)

**目标**: 完善领域事件机制,提升系统可靠性

**任务**:
1. 实现事件总线机制
2. 实现 Outbox 模式保证事件可靠投递
3. 重构领域事件发布机制

**预计时间**: 2-3 周

**验收标准**:
- 事件发布成功率 >= 99.9%
- 事件持久化到 Outbox 表
- 实现事件重试机制

---

## 参考资料

### DDD 经典书籍

1. **《Domain-Driven Design》** by Eric Evans
   - DDD 奠基之作,必读
   - 重点: 战略设计、战术设计、 ubiquitous language

2. **《Implementing Domain-Driven Design》** by Vaughn Vernon
   - DDD 实践指南
   - 重点: 聚合根设计、仓储模式、领域事件

### DDD 相关文章

- [DDD Architecture](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

### 项目相关文档

- 代码风格指南: `docs/code-style-guide.md`
- 集成测试编写指南: `docs/integration-test-writing-guide.md`
- API 契约: `api-contract/openapi.yaml`

---

## 附录: 代码示例

### 完整的 DDD 分层示例

```python
# ==================== 领域层 ====================

# src/app/domain/entities/checkin_rule_entity.py
class CheckinRuleEntity:
    """打卡规则领域实体"""
    def __init__(self, rule_id: int, user_id: int, ...):
        self.rule_id = rule_id
        self.user_id = user_id
        # ... 其他属性

# src/app/domain/aggregates/checkin_rule_aggregate.py
class CheckinRuleAggregate:
    """打卡规则聚合根"""
    def __init__(self, entity: CheckinRuleEntity):
        self._entity = entity
        self._events = []

    def perform_checkin(self, user_id: int, checkin_time: datetime) -> CheckinRecordEntity:
        """执行打卡"""
        # 业务规则验证
        if self._entity.user_id != user_id:
            raise BusinessRuleError("无权限操作此打卡规则")

        # 创建打卡记录
        record = CheckinRecordEntity.create(
            rule_id=self._entity.rule_id,
            user_id=user_id,
            checkin_time=checkin_time
        )

        # 发布领域事件
        self._events.append(CheckinCompletedEvent(
            record_id=record.record_id,
            user_id=user_id,
            rule_id=self._entity.rule_id
        ))

        return record

# src/app/domain/repositories/checkin_rule_repository.py
class CheckinRuleRepository(ABC):
    """打卡规则仓储接口"""
    @abstractmethod
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        pass

# ==================== 应用层 ====================

# src/app/application/use_cases/checkin/perform_checkin_use_case.py
class PerformCheckinUseCase(BaseUseCase):
    """执行打卡用例"""
    def __init__(self):
        super().__init__()
        self.checkin_rule_repository = RepositoryFactory.get_checkin_rule_repository()
        self.checkin_record_repository = RepositoryFactory.get_checkin_record_repository()
        self.event_bus = EventBus()

    @transaction
    def execute(self, rule_id: int, user_id: int) -> UseCaseResult:
        """执行打卡用例"""
        # 查询聚合根
        rule_entity = self.checkin_rule_repository.find_by_id(rule_id)
        if not rule_entity:
            return UseCaseResult.fail('打卡规则不存在', UseCaseStatus.NOT_FOUND)

        # 通过聚合根执行业务逻辑
        aggregate = CheckinRuleAggregate(rule_entity)
        record_entity = aggregate.perform_checkin(user_id, datetime.now())

        # 保存
        self.checkin_record_repository.save_entity(record_entity)

        # 发布领域事件(事务成功后)
        for event in aggregate.get_events():
            self.event_bus.publish(event)

        return UseCaseResult.success(data={
            'record_id': record_entity.record_id
        })

# ==================== 基础设施层 ====================

# src/app/infrastructure/persistence/sqlalchemy_checkin_rule_repository.py
class SQLAlchemyCheckinRuleRepository(CheckinRuleRepository):
    """打卡规则仓储实现"""
    def find_by_id(self, rule_id: int) -> Optional[CheckinRuleEntity]:
        orm_model = db.session.get(CheckinRule, rule_id)
        if not orm_model:
            return None
        return self._to_entity(orm_model)

    def _to_entity(self, orm_model: CheckinRule) -> CheckinRuleEntity:
        return CheckinRuleEntity(
            rule_id=orm_model.rule_id,
            user_id=orm_model.user_id,
            # ... 其他属性
        )

# ==================== 接口层 ====================

# src/app/application/dtos/checkin_rule_dto.py
class CheckinRuleDTO:
    """打卡规则数据传输对象"""
    @staticmethod
    def from_entity(entity: CheckinRuleEntity) -> dict:
        return {
            'rule_id': entity.rule_id,
            'user_id': entity.user_id,
            # ... 其他字段
        }

# src/app/modules/checkin/routes.py
@checkin_bp.route('/checkin', methods=['POST'])
@with_user_verification
def perform_checkin(user_id: int, user: dict):
    """执行打卡接口"""
    params, error_msg = get_json_params(required_fields=['rule_id'])
    if error_msg:
        return make_err_response({}, error_msg)

    use_case = PerformCheckinUseCase()
    result = use_case.execute(rule_id=params['rule_id'], user_id=user_id)

    if not result.is_success:
        return make_err_response({}, result.message)

    return make_succ_response(CheckinRecordDTO.from_entity(result.data))
```

---

**报告生成时间**: 2026-01-17 16:17
**下次审查建议**: 完成第一阶段重构后进行复查
**审查工具版本**: Claude Code with code-simplifier skill
