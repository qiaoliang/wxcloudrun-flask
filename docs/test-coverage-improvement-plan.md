# 测试覆盖率提升计划

## 当前状态

- **当前覆盖率**: 56%
- **目标覆盖率**: 80%+
- **单元测试**: 546个通过，23个失败
- **集成测试**: 68个通过，10个失败

## 覆盖率低的模块（<50%）

### 优先级1：核心业务逻辑（<30%）

1. **src/app/shared/decorators.py** - 13%覆盖率
   - 需要添加装饰器测试
   - 测试装饰器的各种使用场景

2. **src/app/shared/utils/auth.py** - 9%覆盖率
   - 需要添加认证工具测试
   - 测试JWT生成和验证

3. **src/app/shared/utils/auth_helpers.py** - 13%覆盖率
   - 需要添加认证辅助函数测试
   - 测试各种认证场景

4. **src/app/shared/utils/community_helpers.py** - 27%覆盖率
   - 需要添加社区辅助函数测试
   - 测试规则同步、权限检查等

5. **src/app/infrastructure/persistence/sqlalchemy_community_dashboard_repository.py** - 10%覆盖率
   - 需要添加Repository测试
   - 测试各种查询方法

6. **src/app/infrastructure/persistence/sqlalchemy_counters_repository.py** - 25%覆盖率
   - 需要添加Repository测试
   - 测试计数器操作

7. **src/app/infrastructure/persistence/sqlalchemy_user_community_rule_repository.py** - 24%覆盖率
   - 需要添加Repository测试
   - 测试用户社区规则关联操作

8. **src/app/infrastructure/persistence/sqlalchemy_user_daily_abnormality_repository.py** - 26%覆盖率
   - 需要添加Repository测试
   - 测试用户异常值记录操作

### 优先级2：辅助功能（30-50%）

1. **src/app/infrastructure/persistence/sqlalchemy_community_staff_repository.py** - 42%覆盖率
2. **src/app/infrastructure/persistence/sqlalchemy_supervision_relation_repository.py** - 52%覆盖率
3. **src/app/infrastructure/persistence/sqlalchemy_event_message_repository.py** - 48%覆盖率
4. **src/app/infrastructure/persistence/sqlalchemy_profile_view_log_repository.py** - 29%覆盖率

## 测试提升策略

### 策略1：为Repository添加单元测试
- 使用mock数据库连接
- 测试CRUD操作
- 测试复杂查询

### 策略2：为UseCase添加单元测试
- 使用mock Repository
- 测试业务逻辑
- 测试各种边界情况

### 策略3：为工具函数添加单元测试
- 测试各种输入场景
- 测试边界情况
- 测试错误处理

### 策略4：修复失败的测试
- 分析失败原因
- 修复代码或测试
- 确保测试通过

## 实施步骤

### 阶段1：修复失败的测试（预计提升5%）
1. 修复test_events_use_cases.py中的18个失败测试
2. 修复test_manager_access_community.py中的失败测试
3. 修复test_user_community_rule_switching.py中的5个失败测试

### 阶段2：为Repository添加测试（预计提升10%）
1. 为sqlalchemy_community_dashboard_repository.py添加测试
2. 为sqlalchemy_counters_repository.py添加测试
3. 为sqlalchemy_user_community_rule_repository.py添加测试
4. 为sqlalchemy_user_daily_abnormality_repository.py添加测试

### 阶段3：为工具函数添加测试（预计提升8%）
1. 为decorators.py添加测试
2. 为auth.py添加测试
3. 为auth_helpers.py添加测试
4. 为community_helpers.py添加测试

### 阶段4：为UseCase添加测试（预计提升6%）
1. 为新创建的CommunityEventAggregate添加测试
2. 为新创建的UserCommunityRuleAggregate添加测试

### 阶段5：验证和优化（预计提升5%）
1. 运行完整测试套件
2. 生成覆盖率报告
3. 分析未覆盖的代码
4. 添加额外的测试用例

## 预期结果

- 测试覆盖率从56%提升到80%+
- 所有测试通过
- 代码质量得到保证
- 业务逻辑得到充分验证