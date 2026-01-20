# API 整洁性迁移的实施计划

> 使用命令 `executing-plans`，实现这个计划。

**Goal:** 清理重复、不一致和废弃的 API，将 API 数量从 100+ 减少到约 70 个，提高可维护性和用户体验。

**Architecture:** 采用渐进式迁移策略，通过 deprecation 机制确保向后兼容性，分阶段删除旧 API。

**Tech Stack:** Flask 3.1.2, SQLAlchemy 2.0.16, pytest, Flask-RESTful 设计模式

---

## 前置条件

### 环境准备

1. **创建专用的 git worktree**（如果尚未创建）:
   ```bash
   cd /Users/qiaoliang/working/code/safeGuard/backend
   git worktree add .worktree/feature/api-cleanup feature/api-cleanup
   cd .worktree/feature/api-cleanup
   ```

2. **激活虚拟环境**:
   ```bash
   source venv_py312/bin/activate
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **运行测试确保环境正常**:
   ```bash
   make ut
   make it
   ```

### 需要了解的文档

- `docs/code-style-guide.md` - 代码风格指南
- `docs/integration-test-writing-guide.md` - 集成测试编写指南
- `api-contract/openapi.yaml` - API 契约定义
- `CLAUDE.md` - 项目开发指南

---

## 任务 1: 删除已标记废弃的 API

**目标**: 删除 `POST /api/supervision/invite`，该 API 已在代码中标记为废弃。

### 涉及的文件

- `src/app/modules/supervision/routes.py`
- `tests/integration/test_supervision_comprehensive.py`

### 步骤

1. **检查前端使用情况**:
   ```bash
   cd /Users/qiaoliang/working/code/safeGuard/frontend
   grep -r "supervision/invite" src/
   ```

2. **删除 API 路由**:
   
   文件: `src/app/modules/supervision/routes.py`
   
   删除以下代码块：
   ```python
   # 删除这个路由（大约在第 30-50 行附近）
   @supervision_bp.route('/invite', methods=['POST'])
   @require_auth
   def invite_supervisor():
       """邀请监督者（已弃用，请使用 invite_supervisor_internal）"""
       # ... 整个函数实现
   ```

3. **删除相关的 UseCase**（如果存在）:
   ```bash
   rm src/app/application/use_cases/supervision/invite_supervisor_use_case.py
   ```

4. **更新集成测试**:
   
   文件: `tests/integration/test_supervision_comprehensive.py`
   
   删除或注释掉测试 `test_invite_supervisor` 的调用。

5. **运行测试验证**:
   ```bash
   cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
   make it
   ```

6. **提交更改**:
   ```bash
   git add -A
   git commit -m "refactor: 删除已废弃的 POST /api/supervision/invite API

- 删除已标记为废弃的 API 端点
- 删除相关的 UseCase 实现
- 更新集成测试
- 所有测试通过"
   ```

### 预期输出

- 测试全部通过
- 前端没有使用该 API（如果有使用，需要先更新前端）

---

## 任务 2: 合并社区列表 API（优先级2）

**目标**: 将 6 个社区列表 API 合并为 2 个，统一接口设计。

### 涉及的文件

- `src/app/modules/community/community_basic.py`
- `src/app/application/use_cases/community/get_all_communities_use_case.py`
- `src/app/application/use_cases/community/get_available_communities_use_case.py`
- `src/app/application/use_cases/community/get_managed_communities_use_case.py`
- `tests/integration/test_community_crud.py`
- `tests/integration/test_community_applications.py`

### 步骤

#### 步骤 1: 修改 GetAllCommunitiesUseCase

文件: `src/app/application/use_cases/community/get_all_communities_use_case.py`

添加 `type` 和 `limit` 参数支持：

```python
def _validate(self, params: dict) -> UseCaseResult:
    """验证参数"""
    # 添加 type 参数验证
    community_type = params.get('type', 'all')
    if community_type not in ['all', 'available', 'managed']:
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='type参数必须是 all、available 或 managed'
        )
    
    # 添加 limit 参数验证
    limit = params.get('limit', 100)
    try:
        limit = int(limit)
        if limit < 1 or limit > 1000:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='limit参数必须在1-1000之间'
            )
    except (ValueError, TypeError):
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='limit参数必须是整数'
        )
    
    # ... 其他验证逻辑
```

在 `_execute` 方法中添加类型过滤逻辑：

```python
def _execute(self, params: dict) -> UseCaseResult:
    """执行获取社区列表"""
    community_type = params.get('type', 'all')
    limit = params.get('limit', 100)
    
    # 根据类型获取不同的社区列表
    if community_type == 'all':
        # 超级管理员获取所有社区
        communities = self.community_repository.find_all(limit=limit)
    elif community_type == 'available':
        # 普通用户获取可加入社区
        communities = self.community_repository.find_available(limit=limit)
    elif community_type == 'managed':
        # 获取用户管理的社区
        user_id = params.get('user_id')
        communities = self.community_repository.find_managed_by_user(user_id, limit=limit)
    else:
        communities = []
    
    # ... 返回结果
```

#### 步骤 2: 修改路由

文件: `src/app/modules/community/community_basic.py`

修改路由以支持查询参数：

```python
@community_bp.route('/communities', methods=['GET'])
@require_auth
def get_communities():
    """获取社区列表（统一接口）"""
    from app.application.use_cases.community.get_all_communities_use_case import GetAllCommunitiesUseCase
    
    # 获取查询参数
    community_type = request.args.get('type', 'all')
    limit = request.args.get('limit', 100)
    user_id = g.user.user_id
    
    params = {
        'type': community_type,
        'limit': limit,
        'user_id': user_id
    }
    
    use_case = GetAllCommunitiesUseCase()
    result = use_case.execute(params)
    
    return jsonify(result.to_dict())
```

#### 步骤 3: 标记旧 API 为 deprecated

文件: `src/app/modules/community/community_basic.py`

为旧 API 添加 deprecation 警告：

```python
@community_bp.route('/community/list', methods=['GET'])
@require_auth
def get_community_list():
    """获取社区列表（已废弃）"""
    # 添加 deprecation 警告头
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/communities?type=available instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/communities?type=available instead'
    return response

@community_bp.route('/communities/available', methods=['GET'])
@require_auth
def get_communities_available():
    """获取可加入社区（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/communities?type=available instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/communities?type=available instead'
    return response
```

#### 步骤 4: 更新 GetManagedCommunitiesUseCase

文件: `src/app/application/use_cases/community/get_managed_communities_use_case.py`

修改以支持动态 limit 参数：

```python
def _validate(self, params: dict) -> UseCaseResult:
    """验证参数"""
    user_id = params.get('user_id')
    if not user_id:
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='缺少user_id参数'
        )
    
    # 验证 limit 参数
    limit = params.get('limit', 100)
    try:
        limit = int(limit)
        if limit < 1 or limit > 1000:
            return UseCaseResult(
                status=Status.VALIDATION_ERROR,
                message='limit参数必须在1-1000之间'
            )
    except (ValueError, TypeError):
        return UseCaseResult(
            status=Status.VALIDATION_ERROR,
            message='limit参数必须是整数'
        )
    
    return UseCaseResult(status=Status.SUCCESS, message='验证通过')
```

#### 步骤 5: 标记旧的管理社区 API 为 deprecated

文件: `src/app/modules/community/community_basic.py`

```python
@community_bp.route('/community/communities/manage/list', methods=['GET'])
@require_auth
def get_community_manage_list():
    """获取管理的社区列表（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/user/managed-communities instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/user/managed-communities with limit parameter instead'
    return response
```

#### 步骤 6: 删除未使用的搜索 API

文件: `src/app/modules/community/community_basic.py`

删除以下路由：
```python
# 删除这个未使用的路由
@community_bp.route('/communities/manage/search', methods=['GET'])
@require_auth
def search_manageable_communities():
    """搜索可管理社区（未使用）"""
    # ... 整个函数实现
```

#### 步骤 7: 编写集成测试

文件: `tests/integration/test_community_crud.py`

添加测试用例：

```python
def test_get_communities_with_type_all(admin_user, test_app):
    """测试获取所有社区（超级管理员）"""
    with test_app.app_context():
        # 创建多个测试社区
        for i in range(5):
            community = Community(
                name=f"测试社区{i}",
                status=1
            )
            db.session.add(community)
        db.session.commit()
        
        # 使用新的统一接口
        response = test_app.get('/api/communities?type=all&limit=10')
        assert response.status_code == 200
        data = response.json
        assert 'communities' in data['data']
        assert len(data['data']['communities']) >= 5

def test_get_communities_with_type_available(normal_user, test_app):
    """测试获取可加入社区（普通用户）"""
    with test_app.app_context():
        # 创建可加入的社区
        community1 = Community(name="可加入社区1", status=1)
        community2 = Community(name="私有社区", status=0)
        db.session.add_all([community1, community2])
        db.session.commit()
        
        # 使用新的统一接口
        response = test_app.get('/api/community/list')
        assert response.status_code == 200
        
        # 验证 deprecation 警告
        assert 'Deprecation' in response.headers
        assert 'warning' in response.json

def test_get_communities_deprecated_warning(test_app, normal_user):
    """测试废弃 API 的警告头"""
    response = test_app.get('/api/community/list')
    assert response.status_code == 200
    assert response.headers.get('Deprecation') is not None
    assert response.json.get('warning') is not None
```

#### 步骤 8: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 9: 提交更改

```bash
git add -A
git commit -m "refactor: 合并社区列表 API，统一接口设计

- 修改 GetAllCommunitiesUseCase 支持 type 和 limit 参数
- 统一 GET /api/communities 接口，支持 type=all/available/managed
- 标记旧 API 为 deprecated：/api/community/list, /api/communities/available
- 标记旧 API 为 deprecated：/api/community/communities/manage/list
- 删除未使用的 /api/communities/manage/search API
- 添加 deprecation 警告头和响应体警告
- 添加集成测试验证新接口和 deprecation 警告
- 所有测试通过"
```

### 预期输出

- 6 个社区列表 API 合并为 2 个
- 旧 API 返回 deprecation 警告
- 新 API 功能正常
- 所有集成测试通过

---

## 任务 3: 统一 HTTP 方法（优先级2）

**目标**: 将不符合 RESTful 规范的 POST 方法改为正确的 HTTP 方法。

### 涉及的文件

- `src/app/modules/community/community_operations.py`
- `src/app/modules/community/community_members.py`
- `tests/integration/test_community_crud.py`

### 步骤

#### 步骤 1: 修改更新社区 API

文件: `src/app/modules/community/community_operations.py`

将 POST 改为 PUT：

```python
@community_bp.route('/community/<int:community_id>', methods=['PUT'])
@require_auth
@require_role(['super_admin', 'community_admin'])
def update_community(community_id):
    """更新社区信息"""
    # ... 实现保持不变
```

#### 步骤 2: 修改移除用户 API

文件: `src/app/modules/community/community_members.py`

将 POST 改为 DELETE：

```python
@community_bp.route('/community/remove-user', methods=['DELETE'])
@require_auth
def remove_user():
    """移除社区用户（已废弃）"""
    # 添加 deprecation 警告
    response = jsonify({
        "warning": "This API is deprecated, use DELETE /api/communities/<id>/users/<user_id> instead"
    })
    response.headers['Deprecation'] = 'Use DELETE /api/communities/<id>/users/<user_id> instead'
    return response
```

#### 步骤 3: 更新集成测试

文件: `tests/integration/test_community_crud.py`

更新测试以使用新的 HTTP 方法：

```python
def test_update_community_with_put(test_app, admin_user, test_community):
    """测试使用 PUT 方法更新社区"""
    with test_app.app_context():
        update_data = {
            'name': '更新后的社区名称',
            'description': '更新后的描述'
        }
        
        response = test_app.put(f'/api/community/{test_community.community_id}', json=update_data)
        assert response.status_code == 200
        
        # 验证更新成功
        updated_community = db.session.get(Community, test_community.community_id)
        assert updated_community.name == '更新后的社区名称'

def test_remove_user_with_delete(test_app, admin_user, test_user, test_community):
    """测试使用 DELETE 方法移除用户"""
    with test_app.app_context():
        test_user.community_id = test_community.community_id
        db.session.commit()
        
        # 使用新的 DELETE 方法
        response = test_app.delete(
            f'/api/communities/{test_community.community_id}/users/{test_user.user_id}'
        )
        assert response.status_code == 200
        
        # 验证用户已被移除
        updated_user = db.session.get(User, test_user.user_id)
        assert updated_user.community_id is None
```

#### 步骤 4: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 5: 提交更改

```bash
git add -A
git commit -m "refactor: 统一 HTTP 方法，符合 RESTful 规范

- 将 POST /api/community/<id> 改为 PUT /api/community/<id>
- 将 POST /api/community/remove-user 改为 DELETE /api/community/remove-user
- 标记旧 API 为 deprecated，添加警告头
- 更新集成测试使用新的 HTTP 方法
- 所有测试通过"
```

### 预期输出

- HTTP 方法统一为 RESTful 规范
- 旧 API 返回 deprecation 警告
- 新 API 功能正常
- 所有集成测试通过

---

## 任务 4: 合并社区用户列表 API（优先级3）

**目标**: 将 3 个社区用户列表 API 合并为 1 个。

### 涉及的文件

- `src/app/modules/community/community_members.py`
- `src/app/application/use_cases/community/list_community_users_use_case.py`
- `tests/integration/test_community_crud.py`

### 步骤

#### 步骤 1: 修改 ListCommunityUsersUseCase

文件: `src/app/application/use_cases/community/list_community_users.py`

添加参数支持：

```python
def _validate(self, params: dict) -> UseCaseResult:
    """验证参数"""
    community_id = params.get('community_id')
    if not community_id:
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='缺少community_id参数'
        )
    
    # 验证可选参数
    role = params.get('role', '')
    keyword = params.get('keyword', '')
    page = params.get('page', 1)
    page_size = params.get('page_size', 20)
    
    try:
        page = int(page)
        page_size = int(page_size)
        if page < 1:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='page参数必须大于0'
            )
        if page_size < 1 or page_size > 100:
            return UseCaseResult(
                status=UseCaseStatus.VALIDATION_ERROR,
                message='page_size参数必须在1-100之间'
            )
    except (ValueError, TypeError):
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='page和page_size参数必须是整数'
        )
    
    return UseCaseResult(status=UseCaseStatus.SUCCESS, message='验证通过')
```

#### 步骤 2: 更新路由

文件: `src/app/modules/community/community_members.py`

更新路由以支持新参数：

```python
@community_bp.route('/communities/<int:community_id>/users', methods=['GET'])
@require_auth
def get_community_users(community_id):
    """获取社区用户列表（统一接口）"""
    from app.application.use_cases.community.list_community_users_use_case import ListCommunityUsersUseCase
    
    # 获取查询参数
    role = request.args.get('role', '')
    keyword = request.args.get('keyword', '')
    page = request.args.get('page', 1)
    page_size = request.args.get('page_size', 20)
    
    params = {
        'community_id': community_id,
        'role': role,
        'keyword': keyword,
        'page': page,
        'page_size': page_size
    }
    
    use_case = ListCommunityUsersUseCase()
    result = use_case.execute(params)
    
    return jsonify(result.to_dict())
```

#### 步骤 3: 标记旧 API 为 deprecated

文件: `src/app/modules/community/community_members.py`

```python
@community_bp.route('/community/users', methods=['GET'])
@require_auth
def get_community_users_old():
    """获取社区用户列表（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/communities/<id>/users with optional role and keyword parameters instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/communities/<id>/users with optional role and keyword parameters instead'
    return response

@community_bp.route('/community/staff/list-enhanced', methods=['GET'])
@require_auth
def get_staff_list_enhanced():
    """获取工作人员列表（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/communities/<id>/users with role=staff parameter instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/community/<id>/users with role=staff parameter instead'
    return response
```

#### 步骤 4: 删除未使用的 API

文件: `src/app/modules/community/community_members.py`

删除 `POST /api/community/add-users` 路由（如果前端未使用）。

#### 步骤 5: 编写集成测试

文件: `tests/integration/test_community_crud.py`

```python
def test_get_community_users_with_role_filter(test_app, admin_user, test_community, test_staff_user):
    """测试获取社区用户列表（按角色过滤）"""
    with test_app.app_context():
        # 添加用户到社区
        test_user.community_id = test_community.community_id
        test_staff_user.community_id = test_community.community_id
        db.session.commit()
        
        # 使用新接口按角色过滤
        response = test_app.get(f'/api/communities/{test_community.community_id}/users?role=staff')
        assert response.status_code == 200
        data = response.json
        users = data['data']['users']
        assert len(users) >= 1
        assert users[0]['role'] == 'staff'

def test_get_community_users_with_keyword(test_app, admin_user, test_community, test_user):
    """测试获取社区用户列表（关键字搜索）"""
    with test_app.app_context():
        test_user.community_id = test_community.community_id
        db.session.commit()
        
        # 使用新接口搜索
        response = test_app.get(f"/api/communities/{test_community.community_id}/users?keyword={test_user.nickname}")
        assert response.status_code == 200
        data = response.json
        users = data['data']['users']
        assert len(users) >= 1
        assert test_user.nickname in users[0]['nickname']
```

#### 步骤 6: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 7: 提交更改

```bash
git add -A
git commit -m "refactor: 合并社区用户列表 API，统一接口设计

- 修改 ListCommunityUsersUseCase 支持 role 和 keyword 参数
- 统一 GET /api/communities/<id>/users 接口
- 标记旧 API 为 deprecated：/api/community/users, /api/community/staff/list-enhanced
- 删除未使用的 POST /api/community/add-users API
- 添加 deprecation 警告头和响应体警告
- 添加集成测试验证新接口和参数过滤功能
- 所有测试通过"
```

### 预期输出

- 3 个社区用户列表 API 合并为 1 个
- 支持角色过滤和关键字搜索
- 旧 API 返回 deprecation 警告
- 所有集成测试通过

---

## 任务 5: 合并监督邀请 API（优先级3）

**目标**: 将 4 个监督邀请 API 合并为 2 个，使用 RESTful 路径参数。

### 涉及的文件

- `src/app/modules/supervision/routes.py`
- `src/app/application/use_cases/supervision/invitation_management_use_case.py`
- `tests/integration/test_supervision_comprehensive.py`

### 步骤

#### 步骤 1: 标记旧 API 为 deprecated

文件: `src/app/modules/supervision/routes.py`

```python
@supervision_bp.route('/accept', methods=['POST'])
@require_auth
def accept_invitation():
    """接受监督邀请（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use POST /api/supervision/invitations/<id>/accept instead"
    })
    response.headers['Deprecation'] = 'Use POST /api/supervision/invitations/<id>/accept instead'
    return response

@supervision_bp.route('/reject', methods=['POST'])
@require_auth
def reject_invitation():
    """拒绝监督邀请（已废弃）"""
    response = jsonify({
        "warning": "This policy is deprecated, use POST /api/supervision/invitations/<id>/reject instead"
    })
    response.headers['Deprecation'] = 'Use POST /api/supervision/invitations/<id>/reject instead'
    return response
```

#### 步骤 2: 更新集成测试

文件: `tests/integration/test_supervision_comprehensive.py`

添加测试验证 deprecation 警告：

```python
def test_accept_invitation_deprecated_warning(test_app, normal_user, test_invitation):
    """测试接受邀请的 deprecated 警告"""
    with test_app.app_context():
        test_invitation.status = 1  # pending
        db.session.commit()
        
        # 使用旧 API
        response = test_app.post('/api/supervision/accept', json={
            'relation_id': test_invitation.relation_id
        })
        assert response.status_code == 200
        assert 'Deprecation' in response.headers
        assert 'warning' in response.json
```

#### 步骤 3: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 4: 提交更改

```bash
git add -A
git commit -m "refactor: 标记旧监督邀请 API 为 deprecated

- 标记 POST /api/supervision/accept 为 deprecated
- 标记 POST /api/supervision/reject 为 deprecated
- 添加 deprecation 警告头和响应体警告
- 添加集成测试验证 deprecation 警告
- 所有测试通过"
```

### 预期输出

- 旧 API 返回 deprecation 警告
- 新 API 功能正常
- 所有集成测试通过

---

## 任务 6: 合并社区统计和事件 API（优先级3）

**目标**: 将重复的统计和事件 API 合并到 community_dashboard 模块。

### 涉及的文件

- `src/app/modules/events/routes.py`
- `src/app/modules/community_dashboard/routes.py`
- `tests/integration/test_events_comprehensive.py`

### 步骤

#### 步骤 1: 标记 events 模块的 API 为 deprecated

文件: `src/app/modules/events/routes.py`

```python
@events_bp.route('/communities/<int:community_id>/stats', methods=['GET'])
@require_auth
def get_community_stats():
    """获取社区统计（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/community-dashboard/<id>/stats instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/community-dashboard/<id>/stats instead'
    return response

@events_bp.route('/communities/<int:community_id>/pending-events', methods=['GET'])
@require_auth
def get_pending_events():
    """获取未处理事件（已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/community-dashboard/<id>/pending-events instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/community-dashboard/<id>/pending-events instead'
    return response
```

#### 步骤: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 3: 提交更改

```bash
git add -A
git commit -m "refactor: 标记 events 模块的统计和事件 API 为 deprecated

- 标记 GET /api/communities/<id>/stats 为 deprecated
- 标记 GET /api/communities/<id>/pending-events 为 deprecated
- 指向 community-dashboard 模块的对应 API
- 添加 deprecation 警告头和响应体警告
- 所有测试通过"
```

### 预期输出

- events 模块的 API 返回 deprecation 警告
- community_dashboard 模块的 API 功能正常
- 所有集成测试通过

---

## 任务 7: 合并用户搜索 API（优先级3）

**目标**: 将 2 个用户搜索 API 合并为 1 个。

### 涉及的文件

- `src/app/modules/community/user_search.py`
- `src/app/modules/user/routes.py`
- `tests/integration/test_search_by_phone.py`

### 步骤

#### 步骤 1: 修改用户搜索 UseCase

文件: `src/app/application/use_cases/user/search_users_use_case.py`

添加 `exclude_blackroom` 参数支持：

```python
def _validate(self, params: dict) -> UseCaseResult:
    """验证参数"""
    keyword = params.get('keyword', '')
    if not keyword:
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='缺少keyword参数'
        )
    
    # 验证可选参数
    exclude_blackroom = params.get('exclude_blackroom', 'false')
    if exclude_blackroom not in ['true', 'false']:
        return UseCaseResult(
            status=UseCaseStatus.VALIDATION_ERROR,
            message='exclude_blackroom参数必须是 true 或 false'
        )
    
    return UseCaseResult(status=UseCaseStatus.SUCCESS, message='验证通过')
```

#### 步骤 2: 更新路由

文件: `src/app/modules/user/routes.py`

更新路由以支持新参数：

```python
@user_bp.route('/search', methods=['GET'])
@require_auth
def search_users():
    """搜索用户（统一接口）"""
    from app.application.use_cases.user.search_users_use_case import SearchUsersUseCase
    
    # 获取查询参数
    keyword = request.args.get('keyword', '')
    exclude_blackroom = request.args.get('exclude_blackroom', 'false')
    
    params = {
        'keyword': keyword,
        'exclude_blackroom': exclude_blackroom
    }
    
    use_case = SearchUsersUseCase()
    result = use_case.execute(params)
    
    return jsonify(result.to_dict())
```

#### 步骤 3: 标记旧 API 为 deprecated

文件: `src/app/modules/community/user_search.py`

```python
@community_bp.route('/user/search-all-excluding-blackroom', methods=['GET'])
@require_auth
def search_users_excluding_blackroom():
    """搜索用户（排除黑名单，已废弃）"""
    response = jsonify({
        "warning": "This API is deprecated, use GET /api/user/search?exclude_blackroom=true instead"
    })
    response.headers['Deprecation'] = 'Use GET /api/user/search?exclude_blackroom=true instead'
    return response
```

#### 步骤 4: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 5: 提交更改

```bash
git add -A
git commit -m "refactor: 合并用户搜索 API，统一接口设计

- 修改 SearchUsersUseCase 支持 exclude_blackroom 参数
- 统一 GET /api/user/search 接口
- 标记旧 API 为 deprecated：/api/user/search-all-excluding-blackroom
- 添加 deprecation 警告头和响应体警告
- 所有测试通过"
```

### 预期输出

- 2 个用户搜索 API 合并为 1 个
- 支持排除黑名单功能
- 旧 API 返回 deprecation 警告
- 所有集成测试通过

---

## 任务 8: 删除用户社区验证 API（优先级3）

**目标**: 删除功能重复的 POST /api/user/community/verify API。

### 涉及的文件

- `src/app/modules/user/routes.py`
- `tests/integration/` (如果有相关测试)

### 步骤

#### 步骤 1: 删除 API 路由

文件: `src/app/modules/user/routes.py`

删除以下路由：

```python
# 删除这个重复的 API
@user_bp.route('/community/verify', methods=['POST'])
@require_auth
def verify_user_community():
    """验证用户社区（已删除，功能重复）"""
    # ... 整个函数实现
```

#### 步骤 2: 更新 GET /api/user/community 接口

如果需要，更新 GET /api/user/community 接口以同时支持验证功能。

#### 步骤 3: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 4: 提交更改

```bash
git add -A
git commit - "refactor: 删除重复的用户社区验证 API

- 删除 POST /api/user/community/verify API
- 功能已被 GET /api/user/community 替代
- 所有测试通过"
```

### 预期输出

- 重复的 API 被删除
- GET /api/user/community 功能正常
- 所有集成测试通过

---

## 任务 9: 删除未使用的社区用户列表 API（优先级3）

**目标**: 删除前端未使用的旧版 API。

### 涉及的文件

- `src/app/modules/community/community_members.py`
- `src/app/application/use_cases/community/list_community_users_use_case.py`

### 步骤

#### 步骤 1: 检查前端使用情况

```bash
cd /Users/qiaoliang/working/code/safeGuard/frontend
grep -r "community/users" src/
```

#### 步骤 2: 删除旧版 API

文件: `src/app/modules/community/community_members.py`

删除以下路由：

```python
# 删除未使用的旧版 API
@community_bp.route('/users', methods=['GET'])
@require_auth
def get_community_users_old():
    """获取社区用户列表（已删除）"""
    # ... 整个函数实现
```

#### 步骤 3: 删除相关的 UseCase

```bash
rm src/app/application/use_cases/community/list_community_users_use_case.py
```

#### 步骤 4: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 5: 提交更改

```bash
git add -A
git commit -m "refactor: 删除未使用的社区用户列表 API

- 删除 GET /api/community/users 旧版 API
- 删除相关的 ListCommunityUsersUseCase
- 前端未使用，无向后兼容问题
- 所有测试通过"
```

### 预期输出

- 未使用的 API 被删除
- 新版 API 功能正常
- 所有集成测试通过

---

## 任务 10: 删除未使用的工作人员列表 API（优先级3）

**目标**: 删除前端未使用的工作人员列表 API。

### 涉及的文件

- `src/app/modules/community/community_staff.py`

### 步骤

#### 步骤 1: 检查前端使用情况

```bash
cd /Users/qiaoliang/working/code/safeGuard/frontend
grep -r "staff/list-enhanced" src/
```

#### 步骤 2: 删除 API 路由

文件: `src/app/modules/community/community_staff.py`

删除以下路由：

```python
# 删除未使用的工作人员列表 API
@community_bp.route('/staff/list-enhanced', methods=['GET'])
@require_auth
def get_staff_list_enhanced():
    """获取工作人员列表（已删除）"""
    # ... 整个函数实现
```

#### 步骤 3: 运行测试验证

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 4: 提交更改

```bash
git add -A
git commit -m "refactor: 删除未使用的工作人员列表 API

- 删除 GET /api/community/staff/list-enhanced API
- 前端未使用，无向后兼容问题
- 所有测试通过"
```

### 预期输出

- 未使用的 API 被删除
- 其他 API 功能正常
- 所有集成测试通过

---

## 任务 11: 运行完整测试套件

**目标**: 确保所有更改后系统仍然正常工作。

### 步骤

#### 步骤 1: 运行单元测试

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make ut
```

#### 步骤 2: 运行集成测试

```bash
cd /Users/qialiang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make it
```

#### 步骤 3: 检查是否有失败的测试

如果有失败的测试，修复它们。

#### 步骤 4: 提交最终测试结果

```bash
git add -A
git commit -m "test: 验证 API 清理后的测试套件

- 运行完整的单元测试和集成测试
- 所有测试通过
- API 清理完成，系统功能正常"
```

### 预期输出

- 所有单元测试通过（624 个测试）
- 所有集成测试通过（24 个文件）
- 系统功能正常

---

## 任务 12: 更新 API 文档

**目标**: 更新 API 文档，反映新的 API 结构和 deprecation 信息。

### 涉及的文件

- `api-contract/openapi.yaml`
- `docs/API/` 相关文档

### 步骤

#### 步骤 1: 更新 OpenAPI 规范

文件: `api-contract/openapi.yaml`

更新 API 端点列表，标记 deprecated 的 API：

```yaml
paths:
  /api/communities:
    get:
      summary: 获取社区列表（统一接口）
      parameters:
        - name: type
          in: query
          schema:
            type: string
            enum: [all, available, managed]
            default: all
      responses:
        '200':
          description: 成功返回社区列表
  /api/community/list:
    get:
      deprecated: true
      summary: 获取社区列表（已废弃）
      description: 此 API 已废弃，请使用 GET /api/communities?type=available 代替
      responses:
        '200':
          description: 成功返回警告信息
  # ... 其他 API 定义
```

#### 步骤 2: 创建 API 迁移指南

文件: `docs/API/api-migration-guide.md`

```markdown
# API 迁移指南

本文档描述了从旧 API 迁移到新 API 的步骤。

## 已废弃的 API

### 社区列表 API

| 旧 API | 新 API | 迁移步骤 |
|-------|-------|---------|
| GET /api/community/list | GET /api/communities?type=available | 1. 更新请求 URL<br>2. 移除对响应头的依赖<br>3. 验证功能正常 |
| GET /api/communities/available | GET /api/communities?type=available | 同上 |
| GET /api/user/managed-communities | GET /api/user/managed-communities?limit=100 | 1. 添加 limit 参数<br>2. 验证返回数量 |

### HTTP 方法变更

| 旧 API | 新 API | 迁移步骤 |
|-------|-------|---------|
| POST /api/community/<id> | PUT /api/community/<id> | 1. 更新 HTTP 方法<br>2. 更新请求体格式<br>3. 验证功能正常 |
| POST /api/community/remove-user | DELETE /api/communities/<id>/users/<user_id> | 1. 更新 HTTP 方法<br>2. 更新 URL 格式<br>3. 验证功能正常 |

### 监督邀请 API

| 旧 API | 新 API | 迁移步骤 |
|-------|-------|---------|
| POST /api/supervision/accept | POST /api/supervision/invitations/<id>/accept | 1. 更新 URL 格式<br>2. 将 relation_id 改为 invitation_id<br>3. 验证功能正常 |
| POST /api/supervision/reject | POST /api/supervision/invitations/<id>/reject | 同上 |

## Deprecation 警告

所有废弃的 API 都会在响应头和响应体中返回警告信息：

```
Deprecation: Use /api/new-endpoint instead
```

## 时间线

- **立即**: 标记 API 为 deprecated
- **3-6个月**: 保留兼容性
- **6个月后**: 完全删除废弃的 API
```

#### 步骤 3: 提交文档更新

```bash
git add -A
git commit -m "docs: 更新 API 文档，反映 API 清理结果

- 更新 OpenAPI 规范，标记 deprecated API
- 创建 API 迁移指南
- 记录所有 API 变更
- 文档更新完成"
```

### 预期输出

- API 文档更新完成
- 迁移指南清晰明确
- 开发者可以快速了解 API 变更

---

## 任务 13: 最终验证和提交

**目标**: 确保所有更改都已完成，系统功能正常。

### 步骤

#### 步骤 1: 运行完整测试套件

```bash
cd /Users/qiaoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
make ut && make it
```

#### 步骤: 2: 检查 API 数量

```bash
# 统计 API 数量
find src/app/modules -name "*.py" -exec grep -l "@.*_bp.route" {} \; | wc -l
```

预期：API 数量从 100+ 减少到约 70 个。

#### 步骤 3: 检查 deprecation 警告

运行集成测试，验证所有废弃的 API 都返回正确的警告。

#### 步骤 4: 提交最终结果

```bash
git add -A
git commit -m "feat: 完成 API 整洁性迁移

- 删除已废弃的 API：POST /api/supervision/invite
- 合并社区列表 API：6个 → 2个
- 统一 HTTP 方法：POST → PUT/DELETE
- 合并社区用户列表 API：3个 → 1个
- 合并监督邀请 API：4个 → 2个
- 合并社区统计和事件 API：指向 community_dashboard
- 合并用户搜索 API：2个 → 1个
- 删除用户社区验证 API：功能重复
- 删除未使用的 API：/api/community/users, /api/community/staff/list-enhanced
- 所有 API 添加 deprecation 警告
- 更新 API 文档和迁移指南
- API 数量从 100+ 减少到约 70 个（减少30%）
- 所有测试通过（624个单元测试，24个集成测试）
- 系统功能正常

遵循 RESTful 设计原则，提高 API 可维护性和用户体验"
```

### 预期输出

- API 数量减少约 30%
- 所有测试通过
- 文档更新完成
- 系统功能正常

---

## 验证清单

完成所有任务后，验证以下项目：

- [ ] 所有单元测试通过（624个）
- [ ] 所有集成测试通过（24个文件）
- [ ] 废弃的 API 返回 deprecation 警告
- [ ] 新 API 功能正常
- [ ] API 数量减少到约 70 个
- [ ] API 文档已更新
- [ ] 迁移指南已创建
- [ ] 前端可以继续使用（通过 deprecation 机制）

---

## 执行选项

### 选项 1: 由 Subagent 驱动

使用 `subagent-driven-development` 技能，让 subagent 按照这个计划逐步执行。

### 选项 2: 使用并行会话

在 git worktree 中创建新的会话，然后使用 subagent `executing-plans` 来执行这个计划：

```bash
# 在主会话中
cd /Users/qiaoliang/working/code/safeGuard/backend
git worktree add .worktree/feature/api-cleanup feature/api-cleanup

# 在新会话中
cd /Users/qoliang/working/code/safeGuard/backend/.worktree/feature/api-cleanup
claude
```

然后使用：
```
/executing-plans
```

并选择刚创建的计划文件。

---

## 注意事项

1. **TDD 原则**: 每个任务都应先编写测试，再实现功能
2. **频繁提交**: 每完成一个小任务就提交一次，便于回滚
3. **向后兼容**: 通过 deprecation 机制确保前端可以继续使用
4. **测试覆盖**: 确保所有更改都有相应的测试
5. **文档同步**: 代码和文档同步更新

---

## 相关技能

- @executing-plans - 执行实施计划
- @subagent-driven-development - 由 subagent 驱动开发
- @front-end-tester - 前端测试验证（如果有前端更改）
- @test-analyzer - 测试分析，确保测试覆盖率

---

**计划创建时间**: 2026-01-19 22:45:00  
**预计完成时间**: 2-3 个工作日  
**预计提交次数**: 13 次  
**预计测试数量**: 624 个单元测试 + 24 个集成测试 + 新增测试