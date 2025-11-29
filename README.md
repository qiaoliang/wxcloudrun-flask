# wxcloudrun-flask
[![GitHub license](https://img.shields.io/github/license/WeixinCloud/wxcloudrun-express)](https://github.com/WeixinCloud/wxcloudrun-express)
![GitHub package.json dependency version (prod)](https://img.shields.io/badge/python-3.12.11-green)

## 重要说明：Python版本要求
**本项目必须使用 Python 3.12 版本**。项目经过专门针对 Python 3.12 环境配置和测试，使用其他版本可能会导致兼容性问题。

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
- 所有时间字段都使用 `db.DateTime` 类型，以确保在 SQLite 和 MySQL 中都有良好的支持
- 通过环境变量配置数据库连接信息

### 测试环境
- 使用 SQLite 内存数据库
- 角色和状态字段同样使用整数类型存储（与生产环境保持一致）
- 时间字段同样使用 `db.DateTime` 类型，确保跨数据库兼容性
- 在运行测试时自动设置 `FLASK_ENV=testing` 或 `PYTEST_CURRENT_TEST` 环境变量

### 运行自动化测试

**重要：请确保使用 Python 3.12 环境运行测试。**

运行测试时，系统会自动使用 SQLite 内存数据库，无需额外配置：

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 运行所有测试
pytest

# 或使用测试脚本
python scripts/run_tests.py
```

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

## 运行测试

项目包含全面的自动化测试套件，使用 pytest 框架。根据测试需求和环境不同，有三种运行方式，通过不同的环境变量配置文件实现：

### 1. 单元测试（使用SQLite）
在单元测试环境中，系统自动使用SQLite内存数据库，无需外部依赖：

```bash
# 激活Python 3.12虚拟环境
source venv_py312/bin/activate

# 安装测试依赖
pip install -r requirements-test.txt

# 创建单元测试环境变量文件（可选，脚本有默认值）
cat > .env.unit << EOF
USE_SQLITE_FOR_TESTING=true  # 启用测试模式，使用SQLite内存数据库
FLASK_ENV=testing            # Flask环境设置
WX_APPID=test_appid          # 微信小程序AppID（测试值会跳过微信API测试）
WX_SECRET=test_secret        # 微信小程序Secret（测试值会跳过微信API测试）
TOKEN_SECRET=test_token      # JWT令牌密钥
EOF

# 运行所有单元测试
pytest

# 或使用单元测试脚本（推荐，会自动加载.env.unit）
python scripts/unit_tests.py

# 生成覆盖率报告
python scripts/unit_tests.py --coverage
```

### 2. 自动集成测试（使用MySQL，跳过微信API测试）
在CI/CD等自动测试环境中，使用MySQL数据库，但跳过需要真实微信凭证的测试：

```bash
# 创建集成测试环境变量文件（可选，脚本有默认值）
cat > .env.integration << EOF
MYSQL_PASSWORD=rootpassword       # MySQL数据库密码
MYSQL_USERNAME=root               # MySQL数据库用户名
MYSQL_ADDRESS=127.0.0.1:3306      # MySQL数据库地址
USE_REAL_WECHAT_CREDENTIALS=false # 是否使用真实微信凭证（false=跳过微信API测试，true=使用真实凭证）
WX_APPID=test_appid               # 微信小程序AppID（当USE_REAL_WECHAT_CREDENTIALS=false时使用）
WX_SECRET=test_secret             # 微信小程序Secret（当USE_REAL_WECHAT_CREDENTIALS=false时使用）
TOKEN_SECRET=test_token           # JWT令牌密钥
RUN_DOCKER_INTEGRATION_TESTS=true # 是否运行Docker集成测试（true=启动Docker环境，false=跳过Docker启动）
EOF

# 运行完整测试流程（单元测试 + 集成测试）
python scripts/run_tests.py
```

### 3. 手动集成测试（使用真实微信凭证）
在手动测试环境中，使用真实微信凭证，不跳过任何测试：

```bash
# 创建手动测试环境变量文件
cat > .env.manual << EOF
MYSQL_PASSWORD=your_mysql_password      # MySQL数据库密码
MYSQL_USERNAME=root                     # MySQL数据库用户名
MYSQL_ADDRESS=127.0.0.1:3306          # MySQL数据库地址
USE_REAL_WECHAT_CREDENTIALS=true        # 是否使用真实微信凭证（true=启用真实微信API测试）
WX_APPID=your_real_appid               # 真实微信小程序AppID
WX_SECRET=your_real_secret             # 真实微信小程序Secret
TOKEN_SECRET=your_real_token_secret    # JWT令牌密钥
RUN_DOCKER_INTEGRATION_TESTS=true      # 是否运行Docker集成测试（true=启动Docker环境）
EOF

# 运行手动集成测试（脚本会自动加载.env.manual文件）
./manual_test.sh
```

### 环境变量说明

以下是在不同测试场景中使用的环境变量及其含义：

#### 数据库相关变量
- `MYSQL_USERNAME`: MySQL数据库用户名（默认: root）
- `MYSQL_PASSWORD`: MySQL数据库密码
- `MYSQL_ADDRESS`: MySQL数据库地址和端口（格式: host:port，默认: 127.0.0.1:3306）
- `USE_SQLITE_FOR_TESTING`: 是否为测试模式（true/false，默认: 根据测试类型自动设置）
- `FLASK_ENV`: Flask环境（testing/production等，默认: 根据测试类型自动设置）
- `USE_REAL_WECHAT_CREDENTIALS`: 是否使用真实微信凭证进行测试（true/false，默认: false）
- `RUN_DOCKER_INTEGRATION_TESTS`: 是否运行Docker集成测试（true/false，默认: false）

#### 微信API相关变量
- `WX_APPID`: 微信小程序AppID
  - 测试环境：使用包含"test"的值会跳过微信API相关测试
  - 手动测试：使用真实值会执行完整的微信API测试
- `WX_SECRET`: 微信小程序Secret
  - 测试环境：使用包含"test"的值会跳过微信API相关测试
  - 手动测试：使用真实值会执行完整的微信API测试
- `TOKEN_SECRET`: JWT令牌签名密钥

#### 脚本相关变量
- `.env.unit`: 单元测试环境变量文件
- `.env.integration`: 自动集成测试环境变量文件
- `.env.manual`: 手动集成测试环境变量文件
- `DOCKER_STARTUP_TIMEOUT`: Docker容器启动超时时间（秒，默认: 180）

### 测试结构

项目包含以下测试模块：

- `tests/test_*.py`: 单元测试（API、DAO、模型、响应、登录等）
- `tests/integration_test_*.py`: 集成测试（使用MySQL，根据环境变量决定是否跳过微信API测试）
- `tests/conftest.py`: 测试配置和共享fixture

### 测试配置

- 测试文件位于 `tests/` 目录
- 项目使用 pytest 进行测试运行和管理
- 脚本会自动加载 `.env.unit` (单元测试) 或 `.env.integration` (集成测试) 文件
- 覆盖率检查最低要求为 80%
- 单元测试自动使用SQLite，集成测试使用MySQL
- 微信API测试根据WX_APPID和WX_SECRET值决定是否跳过


## License

[MIT](./LICENSE)
