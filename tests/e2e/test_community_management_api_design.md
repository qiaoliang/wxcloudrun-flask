# 社区管理API E2E测试设计文档

**创建日期**: 2025-12-12  
**测试类型**: 端到端测试（E2E）  
**测试模式**: 混合模式（核心流程 + 快速验证）

---

## 1. 测试文件信息

- **文件路径**: `backend/tests/e2e/test_community_management_api.py`
- **依赖**: 使用 `test_server` fixture 提供独立测试环境
- **数据库**: 使用真实数据库（通过 `test_server` 提供的内存数据库）

---

## 2. 测试类设计

### 2.1 TestCommunityStaffManagement (核心流程)

**目标**: 测试完整的工作人员管理流程

#### 测试方法：

1. **test_complete_staff_management_workflow**
   - 场景：完整的工作人员管理流程
   - 步骤：
     1. 超级管理员登录
     2. 创建测试社区
     3. 创建两个测试用户（主管候选、专员候选）
     4. 添加主管
     5. 验证主管列表
     6. 添加专员
     7. 验证完整列表（包含主管和专员）
     8. 移除专员
     9. 验证移除后的列表
   - 断言：
     - 每步操作返回 code=1
     - 列表数据正确
     - 角色分配正确

2. **test_manager_uniqueness_constraint**
   - 场景：验证主管唯一性约束
   - 步骤：
     1. 创建社区并添加一个主管
     2. 尝试添加第二个主管
   - 断言：
     - 第二次添加失败，code=0
     - 错误信息包含"主管只能添加一个"

3. **test_duplicate_staff_prevention**
   - 场景：防止重复添加工作人员
   - 步骤：
     1. 添加用户为专员
     2. 再次添加相同用户
   - 断言：
     - 返回部分成功
     - failed 数组包含该用户及原因

4. **test_staff_list_sorting**
   - 场景：测试工作人员列表排序
   - 步骤：
     1. 添加多个工作人员
     2. 分别使用 sort_by=name, role, time 获取列表
   - 断言：
     - 列表顺序符合排序规则

5. **test_staff_management_permissions**
   - 场景：测试权限控制
   - 步骤：
     1. super_admin 添加工作人员 → 成功
     2. community_manager 添加工作人员 → 成功
     3. community_staff 添加工作人员 → 失败
     4. 普通用户添加工作人员 → 失败
   - 断言：
     - 权限验证正确

---

### 2.2 TestCommunityUserManagement (核心流程)

**目标**: 测试完整的社区用户管理流程

#### 测试方法：

1. **test_complete_user_management_workflow**
   - 场景：完整的用户管理流程
   - 步骤：
     1. 创建社区
     2. 创建3个测试用户
     3. 批量添加用户到社区
     4. 获取用户列表（第1页）
     5. 验证用户数据（含打卡信息字段）
     6. 移除一个用户
     7. 验证移除后的列表
   - 断言：
     - 批量添加成功
     - 列表数据包含 unchecked_count 和 unchecked_items
     - 分页数据正确

2. **test_batch_add_users_with_limit**
   - 场景：测试批量添加限制
   - 步骤：
     1. 尝试添加51个用户ID（超过限制）
   - 断言：
     - 返回 code=0
     - 错误信息包含"最多只能添加50个用户"

3. **test_user_list_pagination**
   - 场景：测试分页功能
   - 步骤：
     1. 添加25个用户
     2. 获取第1页（page_size=20）
     3. 获取第2页
   - 断言：
     - 第1页返回20条，has_more=true
     - 第2页返回5条，has_more=false

4. **test_duplicate_user_prevention**
   - 场景：防止重复添加用户
   - 步骤：
     1. 添加用户到社区
     2. 再次添加相同用户
   - 断言：
     - 返回部分成功
     - failed 数组包含该用户及"用户已在社区"

5. **test_user_management_permissions**
   - 场景：测试权限控制
   - 步骤：
     1. super_admin 添加用户 → 成功
     2. community_manager 添加用户 → 成功
     3. community_staff 添加用户 → 成功
     4. 普通用户添加用户 → 失败
   - 断言：
     - 权限验证正确

---

### 2.3 TestSpecialCommunityLogic (核心流程)

**目标**: 测试特殊社区（安卡大家庭、黑屋）的业务逻辑

#### 测试方法：

1. **test_remove_from_default_community_to_blacklist**
   - 场景：从"安卡大家庭"移除 → 自动移至"黑屋"
   - 步骤：
     1. 创建新用户（自动加入安卡大家庭）
     2. 获取"安卡大家庭"的 community_id
     3. 从"安卡大家庭"移除用户
     4. 验证用户当前社区是"黑屋"
   - 断言：
     - 移除成功，moved_to="黑屋"
     - 用户当前社区为"黑屋"

2. **test_remove_from_normal_community_to_default**
   - 场景：从普通社区移除 → 移至"安卡大家庭"（无其他社区时）
   - 步骤：
     1. 创建普通社区
     2. 创建用户并添加到普通社区
     3. 从普通社区移除用户
     4. 验证用户移至"安卡大家庭"
   - 断言：
     - 移除成功，moved_to="安卡大家庭"
     - 用户当前社区为"安卡大家庭"

3. **test_remove_from_one_community_keep_others**
   - 场景：从普通社区移除 → 仅移除（用户还有其他社区时）
   - 步骤：
     1. 创建两个普通社区A和B
     2. 创建用户并添加到两个社区
     3. 从社区A移除用户
     4. 验证用户仍在社区B
   - 断言：
     - 移除成功，moved_to=null
     - 用户当前社区为社区B

4. **test_special_communities_cannot_be_deleted**
   - 场景：特殊社区不可删除
   - 步骤：
     1. 尝试删除"安卡大家庭"
     2. 尝试删除"黑屋"
   - 断言：
     - 两次删除都失败，code=0
     - 错误信息包含"特殊社区"或"不可删除"

5. **test_special_communities_cannot_be_disabled**
   - 场景：特殊社区不可停用
   - 步骤：
     1. 尝试停用"安卡大家庭"
     2. 尝试停用"黑屋"
   - 断言：
     - 两次操作都失败，code=0
     - 错误信息包含"特殊社区"或"不可停用"

---

### 2.4 TestCommunityPermissions (核心流程)

**目标**: 测试完整的权限控制矩阵

#### 测试方法：

1. **test_super_admin_full_access**
   - 场景：super_admin 可执行所有操作
   - 步骤：
     1. 创建社区 → 成功
     2. 更新社区 → 成功
     3. 添加工作人员 → 成功
     4. 添加用户 → 成功
     5. 删除社区 → 成功
   - 断言：
     - 所有操作返回 code=1

2. **test_community_manager_permissions**
   - 场景：community_manager 权限验证
   - 步骤：
     1. 创建社区 → 失败
     2. 添加工作人员 → 成功
     3. 移除工作人员 → 成功
     4. 添加用户 → 成功
     5. 移除用户 → 成功
   - 断言：
     - 权限矩阵正确

3. **test_community_staff_permissions**
   - 场景：community_staff 权限验证
   - 步骤：
     1. 创建社区 → 失败
     2. 添加工作人员 → 失败
     3. 添加用户 → 成功
     4. 移除用户 → 成功
   - 断言：
     - 权限矩阵正确

4. **test_normal_user_no_permissions**
   - 场景：普通用户所有操作被拒绝
   - 步骤：
     1. 获取社区列表 → 失败
     2. 创建社区 → 失败
     3. 添加工作人员 → 失败
     4. 添加用户 → 失败
   - 断言：
     - 所有操作返回 code=0
     - 错误信息包含"权限不足"

---

### 2.5 TestCommunityCRUD (辅助功能 - 快速验证)

**目标**: 快速验证社区CRUD操作

#### 测试方法：

1. **test_create_community_success**
   - 验证创建社区成功场景
   - 包含必填字段和可选字段

2. **test_update_community_info**
   - 验证更新社区信息
   - 测试部分字段更新

3. **test_toggle_community_status**
   - 验证状态切换（active ↔ inactive）

4. **test_delete_community_with_prerequisites**
   - 验证删除前置条件：
     - 必须先停用
     - 社区内无用户

5. **test_create_community_duplicate_name**
   - 验证社区名称重复

6. **test_update_nonexistent_community**
   - 验证更新不存在的社区

---

### 2.6 TestUserSearch (辅助功能 - 快速验证)

**目标**: 快速验证用户搜索功能

#### 测试方法：

1. **test_search_by_nickname**
   - 按昵称搜索用户

2. **test_search_by_phone**
   - 按手机号搜索用户

3. **test_search_empty_keyword**
   - 空关键词验证

4. **test_search_with_community_filter**
   - 搜索时标记已在社区的用户

---

### 2.7 TestEdgeCases (辅助功能 - 快速验证)

**目标**: 快速验证边界条件和错误处理

#### 测试方法：

1. **test_batch_add_exceeds_limit**
   - 批量添加超过50个用户

2. **test_nonexistent_user_id**
   - 操作不存在的用户ID

3. **test_nonexistent_community_id**
   - 操作不存在的社区ID

4. **test_invalid_status_value**
   - 无效的状态值

5. **test_missing_required_parameters**
   - 缺少必填参数

---

## 3. 辅助方法设计

### 3.1 共享辅助方法

所有测试类共享以下辅助方法：

```python
def _get_super_admin_token(self, base_url):
    """获取超级管理员token"""
    # 使用固定的超级管理员账号登录
    
def _create_test_user(self, base_url, phone, nickname, password='Test123456'):
    """创建测试用户"""
    # 注册新用户并返回 token 和 user_id
    
def _create_test_community(self, base_url, admin_headers, name, location='测试地址'):
    """创建测试社区"""
    # 创建社区并返回 community_id
    
def _add_user_to_community(self, base_url, headers, community_id, user_ids):
    """添加用户到社区"""
    # 批量添加用户
    
def _get_default_community_id(self, base_url, admin_headers):
    """获取"安卡大家庭"的ID"""
    # 从社区列表中查找默认社区
    
def _get_blacklist_community_id(self, base_url, admin_headers):
    """获取"黑屋"的ID"""
    # 从社区列表中查找黑屋社区
```

---

## 4. 测试数据约定

### 4.1 测试用户命名

- 超级管理员: `13900007997` (固定，已存在)
- 测试主管: `139000[1-3]xxxx`
- 测试专员: `139000[4-6]xxxx`
- 普通用户: `139000[7-9]xxxx`

### 4.2 测试社区命名

- 格式: `测试社区_<功能描述>_<时间戳>`
- 例如: `测试社区_工作人员管理_1702368000`

---

## 5. 断言策略

### 5.1 标准响应断言

```python
# 成功响应
assert response.status_code == 200
assert response.json().get('code') == 1
assert 'data' in response.json()

# 失败响应
assert response.status_code == 200
assert response.json().get('code') == 0
assert 'msg' in response.json()
assert '预期错误信息' in response.json()['msg']
```

### 5.2 数据完整性断言

```python
# 列表数据
assert 'users' in data or 'staff_members' in data
assert len(data['users']) > 0
assert 'has_more' in data
assert 'current_page' in data

# 用户数据
assert 'user_id' in user
assert 'nickname' in user
assert 'phone_number' in user
```

---

## 6. 执行顺序

测试执行顺序（建议）：

1. TestCommunityCRUD (辅助功能，建立基础数据)
2. TestCommunityPermissions (核心流程，验证权限)
3. TestCommunityStaffManagement (核心流程)
4. TestCommunityUserManagement (核心流程)
5. TestSpecialCommunityLogic (核心流程)
6. TestUserSearch (辅助功能)
7. TestEdgeCases (辅助功能)

---

## 7. 预期测试覆盖率

- **API 端点覆盖**: 100% (所有12个新API)
- **权限场景覆盖**: 100% (4种角色 × 主要操作)
- **业务逻辑覆盖**: 95%+ (核心流程 + 边界条件)
- **错误处理覆盖**: 90%+ (常见错误场景)

---

## 8. 性能考虑

- 每个测试方法独立运行，不依赖其他测试
- 使用 `test_server` fixture 提供隔离的测试环境
- 测试数据自动清理（通过 fixture）
- 预计总执行时间: 2-3分钟

---

**文档版本**: v1.0  
**最后更新**: 2025-12-12
