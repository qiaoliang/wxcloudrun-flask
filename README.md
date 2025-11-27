# wxcloudrun-flask
[![GitHub license](https://img.shields.io/github/license/WeixinCloud/wxcloudrun-express)](https://github.com/WeixinCloud/wxcloudrun-express)
![GitHub package.json dependency version (prod)](https://img.shields.io/badge/python-3.12.11-green)

微信云托管 python Flask 框架模版，实现简单的计数器读写接口，使用云托管 MySQL 读写、记录计数值。

![](https://qcloudimg.tencent-cloud.cn/raw/be22992d297d1b9a1a5365e606276781.png)


## 快速开始
前往 [微信云托管快速开始页面](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/basic/guide.html)，选择相应语言的模板，根据引导完成部署。

## 本地调试
下载代码在本地调试，请参考[微信云托管本地调试指南](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/guide/debug/)

## 实时开发
代码变动时，不需要重新构建和启动容器，即可查看变动后的效果。请参考[微信云托管实时开发指南](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/guide/debug/dev.html)

## Dockerfile最佳实践
请参考[如何提高项目构建效率](https://developers.weixin.qq.com/miniprogram/dev/wxcloudrun/src/scene/build/speed.html)

## 目录结构说明

~~~
.
├── Dockerfile dockerfile       dockerfile
├── README.md README.md         README.md文件
├── container.config.json       模板部署「服务设置」初始化配置（二开请忽略）
├── requirements.txt            依赖包文件
├── config.py                   项目的总配置文件  里面包含数据库 web应用 日志等各种配置
├── run.py                      flask项目管理文件 与项目进行交互的命令行工具集的入口
├── venv_py312                  Python 3.12 虚拟环境目录
└── wxcloudrun                  app目录
    ├── __init__.py             python项目必带  模块化思想
    ├── dao.py                  数据库访问模块
    ├── model.py                数据库对应的模型
    ├── response.py             响应结构构造
    ├── templates               模版目录,包含主页index.html文件
    └── views.py                执行响应的代码所在模块  代码逻辑处理主要地点  项目大部分代码在此编写
~~~



## 服务 API 文档

### `GET /api/count`

获取当前计数

#### 请求参数

无

#### 响应结果

- `code`：状态码 (1为成功，0为失败)
- `data`：当前计数值
- `msg`：响应消息

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

- `action`：`string` 类型，枚举值
  - 等于 `"inc"` 时，表示计数加一
  - 等于 `"clear"` 时，表示计数重置（清零）

##### 请求参数示例

```
{
  "action": "inc"
}
```

#### 响应结果

- `code`：状态码 (1为成功，0为失败)
- `data`：当前计数值
- `msg`：响应消息

##### 响应结果示例

```json
{
  "code": 1,
  "data": 43,
  "msg": "success"
}
```

#### 调用示例

```
curl -X POST -H 'content-type: application/json' -d '{"action": "inc"}' https://<云托管服务域名>/api/count
```

## 使用注意
如果不是通过微信云托管控制台部署模板代码，而是自行复制/下载模板代码后，手动新建一个服务并部署，需要在「服务设置」中补全以下环境变量，才可正常使用，否则会引发无法连接数据库，进而导致部署失败。
- MYSQL_ADDRESS
- MYSQL_PASSWORD
- MYSQL_USERNAME
以上三个变量的值请按实际情况填写。如果使用云托管内MySQL，可以在控制台MySQL页面获取相关信息。



## Docker Compose 本地开发模式

使用本地挂载方式的 Docker Compose 进行开发，可以实现代码实时更新，无需重新构建镜像。

### 环境准备

确保已安装 Docker 和 Docker Compose，并配置必要的环境变量：

```bash
# 在项目根目录创建 .env 文件，配置环境变量
echo "MYSQL_PASSWORD=your_mysql_password" >> .env
echo "WX_APPID=your_wechat_appid" >> .env
echo "WX_SECRET=your_wechat_secret" >> .env
echo "TOKEN_SECRET=your_jwt_secret" >> .env
```

### 本地开发模式运行

使用开发配置文件启动服务，该配置会将本地代码目录挂载到容器中，实现代码实时更新：

```bash
# 启动开发模式（本地挂载）
docker-compose -f docker-compose.dev.yml up --build

# 或在后台运行
docker-compose -f docker-compose.dev.yml up --build -d
```

### 本地开发模式停止

```bash
# 停止开发模式服务
docker-compose -f docker-compose.dev.yml down

# 停止并删除挂载的数据卷
docker-compose -f docker-compose.dev.yml down -v
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
- 使用 MySQL 数据库
- 角色和状态字段使用整数类型存储
- 通过环境变量配置数据库连接信息

### 测试环境
- 使用 SQLite 内存数据库
- 角色和状态字段同样使用整数类型存储（与生产环境保持一致）
- 在运行测试时自动设置 `FLASK_ENV=testing` 或 `PYTEST_CURRENT_TEST` 环境变量

### 运行自动化测试

运行测试时，系统会自动使用 SQLite 内存数据库，无需额外配置：

```bash
# 运行所有测试
pytest

# 或使用测试脚本
python scripts/run_tests.py
```

## 运行自动化测试

项目包含全面的自动化测试套件，使用 pytest 框架。

### 环境准备

测试时建议使用 Python 3.12 虚拟环境 `venv_py312`：

```bash
# 激活 Python 3.12 虚拟环境
source venv_py312/bin/activate

# 或者如果使用 Windows
# venv_py312\Scripts\activate
```

### 安装测试依赖

```bash
pip install -r requirements-test.txt
```

### 运行测试

1. **运行所有测试**:

```bash
pytest
```

或使用测试脚本:

```bash
python scripts/run_tests.py
```

2. **运行特定测试文件**:

```bash
pytest tests/test_api.py
```

3. **运行测试并生成覆盖率报告**:

```bash
python scripts/run_tests.py --coverage
```

4. **运行测试并生成 HTML 覆盖率报告**:

```bash
python scripts/run_tests.py --coverage --html-report
```

5. **运行特定测试文件并生成覆盖率报告**:

```bash
python scripts/run_tests.py tests/test_api.py --coverage
```

### 集成测试

项目还提供了一个集成测试脚本，使用 docker-compose 启动开发环境并测试 API 功能：

```bash
# 运行集成测试
python scripts/integration_test.py
```

该脚本会：
- 启动 docker-compose 开发环境
- 等待服务完全启动
- 测试计数器 API 的所有功能（获取计数、自增、清零）
- 自动清理资源

### 测试结构

项目包含以下测试模块：

- `test_api.py`: API接口测试
- `test_dao.py`: 数据访问层测试
- `test_model.py`: 数据模型测试
- `test_response.py`: 响应处理测试
- `test_login.py`: 登录功能测试
- `test_error_handling.py`: 错误处理测试
- `test_integration.py`: 集成测试
- `test_user_profile.py`: 用户信息功能测试
- `conftest.py`: 测试配置和共享fixture
- `integration_test.py`: 完整的集成测试脚本

### 测试配置

- 测试文件位于 `tests/` 目录
- 测试文件命名遵循 `test_*.py` 模式
- 项目使用 pytest 进行测试运行和管理
- 覆盖率检查最低要求为 80%


## License

[MIT](./LICENSE)
