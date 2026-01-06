## 项目的目录结构

```
backend/
├── src/                    # 源代码目录
│   ├── app/               # Flask 应用工厂和模块化架构
│   │   ├── __init__.py    # 应用工厂，创建和配置 Flask 应用
│   │   ├── extensions.py  # Flask 扩展管理（SQLAlchemy 等）
│   │   ├── modules/       # Blueprint 模块（11个功能模块）
│   │   │   ├── auth/      # 认证模块
│   │   │   ├── user/      # 用户管理模块
│   │   │   ├── community/ # 社区管理模块
│   │   │   ├── checkin/   # 打卡模块
│   │   │   ├── supervision/ # 监督模块
│   │   │   ├── sms/       # 短信服务模块
│   │   │   ├── share/     # 分享功能模块
│   │   │   ├── events/    # 事件管理模块
│   │   │   ├── community_checkin/ # 社区打卡模块
│   │   │   ├── user_checkin/     # 用户打卡模块
│   │   │   └── misc/      # 杂项功能模块
│   │   └── shared/        # 共享组件
│   │       ├── response.py # 统一响应格式
│   │       ├── decorators.py # 装饰器
│   │       └── utils/     # 工具函数
│   ├── wxcloudrun/        # 核心业务逻辑（业务服务层）
│   │   ├── utils/         # 工具函数
│   │   ├── test_data_generator.py # 线程安全测试数据生成器
│   │   ├── *_service.py   # 业务服务层
│   │   ├── background_tasks.py # 后台任务
│   │   └── wxchat_api.py  # 微信API接口
│   ├── database/          # 数据库相关
│   │   ├── flask_models.py    # Flask-SQLAlchemy 模型
│   │   └── initialization.py  # 数据库初始化
│   ├── alembic/           # 数据库迁移脚本
│   ├── run.py             # 标准应用入口（使用 app.create_app()）
│   ├── config.py          # 配置文件
│   ├── config_manager.py  # 配置管理器
│   ├── smart_test_runner.py # 智能测试运行器
│   └── pytest.ini         # pytest配置文件
├── tests/                 # 测试目录
│   ├── unit/             # 单元测试（22个测试文件）
│   │   ├── conftest.py   # 单元测试配置
│   │   └── *.py         # 单元测试文件
│   ├── integration/      # 集成测试（2个测试文件）
│   │   ├── conftest.py   # 集成测试配置
│   │   └── *.py         # 集成测试文件
│   ├── e2e/              # 端到端测试
│   └── conftest.py        # pytest配置文件
├── api-contract/          # API 文档
├── scripts/              # 构建和部署脚本
├── docs/                 # 保存的项目规范与开发计划相关文档
├── Makefile              # 测试和构建命令
└── venv_py312/          # Python 虚拟环境
```