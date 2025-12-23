# DAO 迁移计划

## 概述

本文档记录了从旧的 `dao.py` 数据访问层迁移到 Flask-SQLAlchemy 架构的详细计划。

## 已完成的迁移

### 1. checkin_rule_service.py 和 checkin_record_service.py ✅
- **完成时间**: 2025-12-23
- **主要更改**:
  - 移除对 `dao.py` 的依赖
  - 将所有 `get_db().get_session()` 替换为 `db.session`
  - 更新 CheckinRecord 模型，添加缺失字段
  - 移除不必要的 expunge 操作
- **测试状态**: 通过

## 待完成的迁移

### 1. wxcloudrun/views/community.py
- **依赖项**: 8处使用 `get_db()`
- **影响范围**: 社区管理相关的API
- **优先级**: 高

### 2. wxcloudrun/views/misc.py
- **依赖项**: Counter CRUD 函数
- **影响范围**: 计数器功能
- **优先级**: 中

### 3. wxcloudrun/views/community_checkin.py
- **依赖项**: 1处使用 `get_db()`
- **影响范围**: 社区打卡功能
- **优先级**: 高

## 迁移步骤

### 第一阶段：views/community_checkin.py
1. 替换 `get_db()` 为 `db.session`
2. 更新权限检查逻辑
3. 测试相关功能

### 第二阶段：views/misc.py
1. 将 Counter CRUD 函数改为直接使用 Flask-SQLAlchemy
2. 更新所有相关调用
3. 测试计数器功能

### 第三阶段：views/community.py
1. 逐个替换 8 处 `get_db()` 调用
2. 更新社区管理逻辑
3. 运行完整测试套件

### 第四阶段：清理
1. 确认无代码使用 dao.py
2. 删除 dao.py 文件
3. 更新文档

## 风险评估

- **低风险**: 已有迁移经验
- **测试覆盖**: 现有测试可以验证功能
- **回滚计划**: 保留 dao.py 直到所有迁移完成

## 注意事项

1. 每个文件迁移后必须运行相关测试
2. 保持功能完全一致，只改变实现方式
3. 注意事务处理和会话管理
4. 更新相关文档和注释