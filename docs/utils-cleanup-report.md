# 工具函数审查报告

## 审查日期
2026-01-16

## 审查范围
backend/src/app/shared/utils/
backend/src/app/modules/community/utils.py
backend/src/config/utils.py

## 工具函数分类

### 1. 配置工具类 (config/utils.py)
**文件**: `backend/src/config/utils.py`

**状态**: ✅ **保留** - 纯工具类，无业务逻辑

**功能**:
- 环境类型判断
- 环境配置文件路径获取
- Docker环境检测

**建议**: 
- 保持现状，这是纯配置工具，不需要迁移

---

### 2. 认证工具 (shared/utils/auth.py)
**文件**: `backend/src/app/shared/utils/auth.py`

**状态**: ⚠️ **部分保留** - 包含业务逻辑

**功能**:
- `verify_token()` - JWT token验证
- `require_role()` - 角色权限装饰器
- `require_community_staff()` - 社区工作人员权限装饰器
- `require_community_manager()` - 社区主管权限装饰器
- `require_superadmin()` - 超级管理员权限装饰器
- `check_community_permission()` - 社区权限检查
- `get_current_user()` - 获取当前用户
- `generate_jwt_token()` - 生成JWT token
- `generate_refresh_token()` - 生成refresh token

**问题**:
1. `require_community_staff()` 函数重复定义了两次（第73行和第103行）
2. 包含业务逻辑（权限检查、用户查询）
3. 直接访问数据库（`db.session.get(User, user_id)`）

**建议**:
- **保留**: `verify_token()`, `generate_jwt_token()`, `generate_refresh_token()` - 纯认证工具
- **迁移到UseCase**: `check_community_permission()`, `get_current_user()` - 包含业务逻辑
- **保留装饰器**: `require_role()`, `require_community_staff()`, `require_community_manager()`, `require_superadmin()` - 装饰器模式，适合保留

**清理行动**:
1. 删除重复的 `require_community_staff()` 函数
2. 将 `check_community_permission()` 迁移到 UseCase
3. 将 `get_current_user()` 迁移到 UseCase

---

### 3. 认证辅助函数 (shared/utils/auth_helpers.py)
**文件**: `backend/src/app/shared/utils/auth_helpers.py`

**状态**: ❌ **需要重构** - 包含大量业务逻辑

**功能**:
- `execute_timed_query()` - 带时间监控的查询
- `generate_auth_tokens()` - 生成认证token
- `verify_password()` - 验证密码
- `ensure_user_nickname()` - 确保用户有昵称
- `verify_sms_code_dual_purpose()` - 验证短信验证码
- `assign_user_to_default_community()` - 分配用户到默认社区
- `normalize_and_hash_phone()` - 标准化电话号码并生成hash
- `query_user_by_phone_hash_with_timing()` - 通过phone_hash查询用户

**问题**:
1. `generate_auth_tokens()` - 包含业务逻辑（调用UpdateUserUseCase）
2. `ensure_user_nickname()` - 包含业务逻辑（调用UpdateUserUseCase）
3. `assign_user_to_default_community()` - 包含业务逻辑（查询社区、更新用户）
4. `query_user_by_phone_hash_with_timing()` - 包含业务逻辑（调用GetUserByPhoneHashUseCase）
5. 函数之间有依赖关系，违反单一职责原则

**建议**:
- **保留**: `execute_timed_query()`, `verify_password()`, `verify_sms_code_dual_purpose()`, `normalize_and_hash_phone()` - 纯工具函数
- **迁移到UseCase**: `generate_auth_tokens()`, `ensure_user_nickname()`, `assign_user_to_default_community()`, `query_user_by_phone_hash_with_timing()` - 包含业务逻辑

**清理行动**:
1. 将 `generate_auth_tokens()` 迁移到 `GenerateAuthTokensUseCase`
2. 将 `ensure_user_nickname()` 迁移到 `EnsureUserNicknameUseCase`
3. 将 `assign_user_to_default_community()` 迁移到 `AssignUserToDefaultCommunityUseCase`
4. 将 `query_user_by_phone_hash_with_timing()` 迁移到 `QueryUserByPhoneHashUseCase`
5. 保留纯工具函数

---

### 4. 查询工具 (shared/utils/query.py)
**文件**: `backend/src/app/shared/utils/query.py`

**状态**: ✅ **保留** - 纯查询工具

**功能**:
- `QueryHelper` - 查询辅助类
- `QueryBuilder` - 查询构建器

**建议**: 
- 保持现状，这是纯查询工具，封装SQLAlchemy 2.0 API，不需要迁移

---

### 5. 社区辅助函数 (shared/utils/community_helpers.py)
**文件**: `backend/src/app/shared/utils/community_helpers.py`

**状态**: ❌ **需要重构** - 包含大量业务逻辑

**功能**:
- `CommunityRuleHelper.activate_new_community_rules()` - 激活新社区规则
- `CommunityPermissionHelper.has_community_permission()` - 检查社区权限
- `CommunityRuleQueryHelper.get_rule_detail()` - 获取规则详情
- `CommunityRuleQueryHelper.get_user_community_rules()` - 获取用户社区规则

**问题**:
1. `CommunityRuleHelper.activate_new_community_rules()` - 包含业务逻辑（创建/更新用户规则）
2. `CommunityPermissionHelper.has_community_permission()` - 包含业务逻辑（权限检查）
3. `CommunityRuleQueryHelper.get_rule_detail()` - 包含业务逻辑（查询规则）
4. `CommunityRuleQueryHelper.get_user_community_rules()` - 包含业务逻辑（查询用户规则）
5. 直接访问数据库（`db.session.execute()`）

**建议**:
- **全部迁移到UseCase**: 所有功能都包含业务逻辑

**清理行动**:
1. 将 `CommunityRuleHelper.activate_new_community_rules()` 迁移到 `ActivateCommunityRulesUseCase`
2. 将 `CommunityPermissionHelper.has_community_permission()` 迁移到 `CheckCommunityPermissionUseCase`
3. 将 `CommunityRuleQueryHelper.get_rule_detail()` 迁移到 `GetCommunityRuleDetailUseCase`
4. 将 `CommunityRuleQueryHelper.get_user_community_rules()` 迁移到 `GetUserCommunityRulesUseCase`
5. 删除整个文件

---

### 6. 社区模块工具函数 (modules/community/utils.py)
**文件**: `backend/src/app/modules/community/utils.py`

**状态**: ✅ **已清理** - 只保留一个辅助函数

**功能**:
- `_check_superadmin_permission()` - 检查超级管理员权限

**建议**: 
- 保持现状，这是简单的权限检查辅助函数，适合保留

---

### 7. 异常值计算器 (shared/utils/abnormality_calculator.py)
**文件**: `backend/src/app/shared/utils/abnormality_calculator.py`

**状态**: ⚠️ **已封装** - 已被UpdateAbnormalityValuesUseCase使用

**功能**:
- `AbnormalityCalculator` - 异常值计算器类

**建议**: 
- 保持现状，已被UpdateAbnormalityValuesUseCase封装使用

---

## 优先级排序

### 高优先级（立即处理）
1. **删除重复函数**: `shared/utils/auth.py` 中的 `require_community_staff()` 重复定义
2. **迁移社区辅助函数**: `shared/utils/community_helpers.py` - 包含大量业务逻辑

### 中优先级（近期处理）
3. **重构认证辅助函数**: `shared/utils/auth_helpers.py` - 部分函数需要迁移到UseCase
4. **迁移权限检查函数**: `shared/utils/auth.py` 中的 `check_community_permission()`, `get_current_user()`

### 低优先级（长期优化）
5. **代码优化**: 优化查询工具和认证工具的实现

---

## 清理计划

### 阶段1: 删除重复代码
- [ ] 删除 `shared/utils/auth.py` 中重复的 `require_community_staff()` 函数

### 阶段2: 迁移社区辅助函数
- [ ] 创建 `ActivateCommunityRulesUseCase`
- [ ] 创建 `CheckCommunityPermissionUseCase`
- [ ] 创建 `GetCommunityRuleDetailUseCase`
- [ ] 创建 `GetUserCommunityRulesUseCase`
- [ ] 删除 `shared/utils/community_helpers.py`

### 阶段3: 重构认证辅助函数
- [ ] 创建 `GenerateAuthTokensUseCase`
- [ ] 创建 `EnsureUserNicknameUseCase`
- [ ] 创建 `AssignUserToDefaultCommunityUseCase`
- [ ] 创建 `QueryUserByPhoneHashUseCase`
- [ ] 更新 `shared/utils/auth_helpers.py` 只保留纯工具函数

### 阶段4: 迁移权限检查函数
- [ ] 创建 `CheckCommunityPermissionUseCase`
- [ ] 创建 `GetCurrentUserUseCase`
- [ ] 更新 `shared/utils/auth.py`

---

## 总结

### 保留的工具函数（无需迁移）
1. `config/utils.py` - 环境配置工具
2. `shared/utils/query.py` - 查询工具
3. `shared/utils/auth.py` 中的装饰器函数
4. `shared/utils/auth.py` 中的 `verify_token()`, `generate_jwt_token()`, `generate_refresh_token()`
5. `shared/utils/auth_helpers.py` 中的 `execute_timed_query()`, `verify_password()`, `verify_sms_code_dual_purpose()`, `normalize_and_hash_phone()`
6. `modules/community/utils.py` 中的 `_check_superadmin_permission()`
7. `shared/utils/abnormality_calculator.py` - 已被UseCase封装

### 需要迁移到UseCase的函数
1. `shared/utils/community_helpers.py` - 全部迁移
2. `shared/utils/auth_helpers.py` - 4个函数迁移
3. `shared/utils/auth.py` - 2个函数迁移

### 需要删除的重复代码
1. `shared/utils/auth.py` 中重复的 `require_community_staff()` 函数

---

## 建议

1. **立即执行**: 删除重复代码，确保代码质量
2. **分阶段实施**: 按照优先级分阶段迁移工具函数
3. **保持测试覆盖**: 每次迁移后确保测试通过
4. **文档更新**: 更新相关文档，说明工具函数的使用方式