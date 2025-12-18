# 端到端测试套件的编写与执行

本文档用于指导后台 flask 端到端(e2e）的 API 自动化测试用例编写。

### 运行端到端测试套件

在本文件所在目录的父目录下执行命令 `make e2e`，运行端到端的全部测试套件。即：

```bash
cd ..
# 运行所有测试文件
make e2e
# 运行单个测试文件
make e2e-single TEST=test_multi_community_role_e2e.py
# 运行单个测试函数
make e2e-single TEST=test_multi_community_role_e2e.py::TestMultiCommunityRole::test_user_can_join_multiple_communities
```

### 端到端测试代码的位置

后台项目的端到端测试用例全部放与本文件所在目录同级的目录 `tests/e2e` 目录下。即：

```bash
cd ../tests/e2e && ls -al test*.py
```

### e2e 测试的编写要求

为了即保障测试全面，又节省时间，采用混合测试用例模式，

即：关注核心流程 + 快速验证

-   **依赖**: 使用 `test_server` fixture 提供独立测试环境
-   **数据库**: 使用真实数据库（通过 `test_server` 提供的内存数据库）
-   **文件存放**: `backend/tests/e2e`
-   **文件命名**: `test-[the-discription-of-verification-point].py`
