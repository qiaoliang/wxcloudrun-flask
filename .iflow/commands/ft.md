# run local function tests for backend

执行下面的shell 命令。

```bash
cd ~/working/code/safeGuard/backend
source venv_py312/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt
# 运行后台集成测试
python scripts/function_tests.py
```
