# wxcloudrun-flask

[![GitHub license](https://img.shields.io/github/license/WeixinCloud/wxcloudrun-express)](https://github.com/WeixinCloud/wxcloudrun-express)
![GitHub package.json dependency version (prod)](https://img.shields.io/badge/python-3.12.11-green)

## 重要说明：Python 版本要求

**本项目必须使用 Python 3.12 版本**。项目经过专门针对 Python 3.12 环境配置和测试，使用其他版本可能会导致兼容性问题。

## 微信云托管 python Flask 框架模版，实现简单的计数器读写接口，使用云托管 MySQL 读写、记录计数值。

![](https://qcloudimg.tencent-cloud.cn/raw/be22992d297d1b9a1a5365e606276781.png)

## 快速开始

前往 [微信云托管快速开始页面](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/basic/guide.html)，选择相应语言的模板，根据引导完成部署。

## 本地调试

下载代码在本地调试，请参考[微信云托管本地调试指南](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/guide/debug/)

## 实时开发

代码变动时，不需要重新构建和启动容器，即可查看变动后的效果。请参考[微信云托管实时开发指南](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/guide/debug/dev.html)

## Dockerfile 最佳实践

请参考[如何提高项目构建效率](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/scene/build/speed.html)

获取当前计数

#### 请求参数

无

#### 响应结果

-   `code`：状态码 (1 为成功，0 为失败)
-   `data`：当前计数值
-   `msg`：响应消息

##### 响应结果示例

```json
{
    "code": 1,
    "data": 42,
    "msg": "success"
}
```

#### 调用示例

```
curl https://<云托管服务域名>/api/count
```

### `POST /api/count`

更新计数，自增或者清零

#### 请求参数

-   `action`：`string` 类型，枚举值
    -   等于 `"inc"` 时，表示计数加一
    -   等于 `"clear"` 时，表示计数重置（清零）

##### 请求参数示例

```
{
  "action": "inc"
}
```

#### 响应结果

-   `code`：状态码 (1 为成功，0 为失败)
-   `data`：当前计数值
-   `msg`：响应消息

##### 响应结果示例

```json
{
    "code": 1,
    "data": 43,
    "msg": "success"
}
```

### 生产模式运行

如果需要运行生产模式（不使用本地挂载，使用构建的镜像）：

```bash
# 启动生产模式服务
docker-compose up --build

# 或在后台运行
docker-compose up --build -d
```

## 数据库配置

本项目支持两种数据库环境：

### 生产环境

-   使用 MySQL 数据库
-   角色和状态字段使用整数类型存储
-   所有时间字段都使用 `db.DateTime` 类型，以确保在 SQLite 和 MySQL 中都有良好的支持
-   通过环境变量配置数据库连接信息

### 测试环境

-   角色和状态字段同样使用整数类型存储（与生产环境保持一致）
-   时间字段同样使用 `db.DateTime` 类型，确保跨数据库兼容性
-   在运行测试时自动设置 `FLASK_ENV=testing` 或 `PYTEST_CURRENT_TEST` 环境变量

## 数据库迁移

项目现在使用 Flask-Migrate 进行数据库迁移管理，替代了原有的 init_db.sql 脚本和 views.py 中的 add_verification_fields() 函数。

### 初始化迁移环境

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 安装依赖（包含Flask-Migrate）
pip install -r requirements.txt

# 初始化数据库表
python run_migrations.py init

# 为当前数据库结构创建初始迁移
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 日常迁移操作

```bash
# 当修改模型后，生成新的迁移脚本
flask db migrate -m "描述性迁移信息"

# 应用迁移到数据库
flask db upgrade

# 查看当前迁移状态
flask db current

# 回滚到上一个版本
flask db downgrade
```
