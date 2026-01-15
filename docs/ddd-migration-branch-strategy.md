# DDD 迁移分支策略

## 概述

本文档定义了 DDD 迁移过程中的 Git 分支策略，确保迁移过程可控、可回滚，并保持代码质量。

## 分支结构

### 主分支

- **main/master**: 生产环境分支，始终保持稳定状态
- **develop/dev**: 开发环境分支，集成最新的开发功能

### 迁移分支

```
main/master (生产)
    ↑
    │ 合并
    │
develop/dev (开发)
    ↑
    │ 合并
    │
feature/ddd-migration-phase-0  ← 准备工作
    ↑
    │ 合并
    │
feature/ddd-migration-phase-1  ← 认证模块迁移
    ↑
    │ 合并
    │
feature/ddd-migration-phase-2  ← 用户管理模块迁移
    ↑
    │ 合并
    │
... (其他阶段)
```

## 分支命名规范

### 功能分支

```
feature/ddd-migration-phase-{N}
```

其中 `{N}` 是阶段编号（0-9）。

示例：
- `feature/ddd-migration-phase-0` - 准备工作
- `feature/ddd-migration-phase-1` - 认证模块迁移
- `feature/ddd-migration-phase-2` - 用户管理模块迁移

### 修复分支

```
fix/ddd-migration-{issue}-{description}
```

示例：
- `fix/ddd-migration-123-auth-login-failure`

### 热修复分支

```
hotfix/{description}
```

仅用于生产环境的紧急修复。

## 工作流程

### 阶段 0：准备工作

```bash
# 1. 从 develop 创建阶段 0 分支
git checkout develop
git pull origin develop
git checkout -b feature/ddd-migration-phase-0

# 2. 完成准备工作
# - 编写 UseCase 测试
# - 设置 CI/CD
# - 准备迁移环境

# 3. 提交代码
git add .
git commit -m "feat: 完成 DDD 迁移阶段 0 准备工作"

# 4. 推送到远程
git push origin feature/ddd-migration-phase-0

# 5. 创建 Pull Request
# - 从 feature/ddd-migration-phase-0 到 develop
# - 要求代码审查
# - 要求所有测试通过
```

### 阶段 N：模块迁移（N ≥ 1）

```bash
# 1. 从 develop 创建阶段 N 分支
git checkout develop
git pull origin develop
git checkout -b feature/ddd-migration-phase-{N}

# 2. 完成模块迁移
# - 重构路由
# - 启用聚合根
# - 发布领域事件
# - 编写测试

# 3. 提交代码
git add .
git commit -m "feat: 完成 DDD 迁移阶段 {N} - {模块名称}"

# 4. 推送到远程
git push origin feature/ddd-migration-phase-{N}

# 5. 创建 Pull Request
# - 从 feature/ddd-migration-phase-{N} 到 develop
# - 要求代码审查
# - 要求所有测试通过
# - 要求性能测试通过

# 6. 合并到 develop
# - 使用 squash merge
# - 删除特性分支
```

### 合并到主分支

```bash
# 1. 等待所有阶段完成
# 2. 从 develop 创建发布分支
git checkout develop
git pull origin develop
git checkout -b release/ddd-migration-v1.0

# 3. 进行最终测试
# - 运行所有测试
# - 性能测试
# - 安全测试

# 4. 合并到 main/master
git checkout main
git merge release/ddd-migration-v1.0
git tag -a v1.0.0 -m "DDD 迁移完成"
git push origin main --tags

# 5. 合并到 develop
git checkout develop
git merge release/ddd-migration-v1.0
git push origin develop

# 6. 删除发布分支
git branch -d release/ddd-migration-v1.0
```

## Pull Request 要求

### 必需的检查

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 代码覆盖率 ≥ 80%
- [ ] 代码审查通过（至少 2 人）
- [ ] 性能测试通过（响应时间无明显下降）
- [ ] 安全扫描通过
- [ ] API 契约验证通过

### PR 描述模板

```markdown
## DDD 迁移阶段 {N}

### 变更内容

- [ ] 重构 {模块名称} 路由
- [ ] 启用 {聚合根名称}
- [ ] 发布 {领域事件名称}
- [ ] 编写测试

### 影响范围

- 修改的文件：{文件列表}
- 影响的模块：{模块列表}
- API 变更：{API 变更列表}

### 测试结果

- 单元测试：✅ 通过
- 集成测试：✅ 通过
- 性能测试：✅ 通过
- 代码覆盖率：{覆盖率}%

### 相关任务

- TaskMaster: {任务 ID}
- Issue: {Issue 编号}

### 审查要点

- [ ] 代码符合 DDD 原则
- [ ] 测试覆盖完整
- [ ] 性能无明显下降
- [ ] 文档已更新
```

## 回滚策略

### 快速回滚

如果某个阶段迁移后发现问题，可以快速回滚：

```bash
# 1. 回退到上一个稳定的提交
git revert <commit-hash>

# 2. 推送到远程
git push origin develop

# 3. 重新运行测试
```

### 完整回滚

如果需要回滚整个迁移：

```bash
# 1. 创建回滚分支
git checkout develop
git checkout -b rollback/ddd-migration

# 2. 回退到迁移前的状态
git revert <migration-start-commit>..<migration-end-commit>

# 3. 推送到远程
git push origin rollback/ddd-migration

# 4. 创建 PR 并合并
```

## 分支保护规则

### main/master 分支

- 禁止直接推送
- 要求 PR 审查（至少 2 人）
- 要求 CI/CD 通过
- 要求状态检查通过

### develop/dev 分支

- 禁止直接推送
- 要求 PR 审查（至少 1 人）
- 要求 CI/CD 通过
- 要求状态检查通过

## 清理策略

### 定期清理

- 每周清理已合并的特性分支
- 每月清理过期的修复分支
- 每季度清理未使用的标签

### 自动清理

```bash
# 清理已合并的本地分支
git branch --merged | grep -v "\*" | xargs git branch -d

# 清理已合并的远程分支
git remote prune origin
```

## 最佳实践

1. **小步快跑**：每个阶段尽可能小，便于审查和回滚
2. **频繁提交**：每个功能完成后立即提交
3. **充分测试**：每个阶段都要有完整的测试
4. **代码审查**：所有 PR 都需要经过代码审查
5. **文档更新**：及时更新相关文档
6. **性能监控**：持续监控性能指标
7. **安全检查**：定期进行安全扫描

## 注意事项

1. **不要在 main/master 上直接开发**
2. **不要合并未经测试的代码**
3. **不要删除未合并的分支**
4. **不要强制推送（force push）**
5. **不要跳过代码审查**

## 工具支持

### Git Hooks

- pre-commit: 代码格式化和检查
- commit-msg: 提交信息格式检查
- pre-push: 运行测试

### CI/CD 集成

- 自动运行测试
- 自动生成覆盖率报告
- 自动部署到测试环境

## 联系方式

如有问题，请联系：
- 技术负责人：{姓名}
- DevOps 团队：{邮箱}
- 项目经理：{姓名}

---

**文档版本**: 1.0
**最后更新**: 2026-01-15
**维护者**: DDD 迁移团队