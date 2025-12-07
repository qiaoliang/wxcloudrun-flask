# Makefile for backend testing

.PHONY: help test-integration test-unit test-all clean setup

# 默认目标
help:
	@echo "可用的测试命令:"
	@echo "  make setup        - 设置测试环境"
	@echo "  make test-unit    - 运行单元测试"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-all     - 运行所有测试"
	@echo "  make test-coverage - 生成测试覆盖率报告"
	@echo "  make clean        - 清理测试文件"
	@echo "  make test-failed  - 运行之前失败的测试"
	@echo ""
	@echo "示例:"
	@echo "  make test-unit            # 运行单元测试"
	@echo "  make test-unit VERBOSE=1  # 详细输出"
	@echo "  make test-integration     # 运行集成测试"
	@echo "  make test-integration VERBOSE=1  # 详细输出"

# 设置测试环境
setup:
	@if [ ! -d "venv_py312" ]; then \
		python3.12 -m venv venv_py312; \
		source venv_py312/bin/activate; \
		pip install -r requirements.txt; \
		echo "虚拟环境设置完成"; \
	else \
		echo "虚拟环境已存在"; \
	fi

# 运行集成测试
test-integration:
	@echo "运行集成测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest tests/integration/ -v -s; \
	else \
		python -m pytest tests/integration/ -v; \
	fi

# 运行单个集成测试文件
test-registration:
	@echo "运行注册流程测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/test_registration_flow.py -v

test-account-merge:
	@echo "运行账号合并测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/test_account_merging.py -v

test-login-response:
	@echo "运行登录响应测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/test_unified_login_response.py -v

# 运行单元测试
test-unit:
	@echo "运行单元测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest tests/unit/ -v -s; \
	else \
		python -m pytest tests/unit/ -v; \
	fi

# 运行所有测试
test-all:
	@echo "运行所有测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/ -v

# 生成测试覆盖率报告
test-coverage:
	@echo "生成测试覆盖率报告..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/ --cov=src --cov-report=html --cov-report=term

# 清理测试文件
clean:
	@echo "清理测试文件..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf .pytest_cache 2>/dev/null || true
	@rm -rf htmlcov 2>/dev/null || true
	@echo "清理完成"

# 仅运行失败的测试（如果之前有失败）
test-failed:
	@echo "运行之前失败的测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/ --lf -v

# 运行特定测试类
test-class:
	@if [ -z "$(CLASS)" ]; then \
		echo "请指定测试类，例如: make test-class CLASS=TestAccountMerging"; \
		exit 1; \
	fi
	@echo "运行测试类: $(CLASS)"
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/ -k $(CLASS) -v

# 运行特定测试方法
test-method:
	@if [ -z "$(METHOD)" ]; then \
		echo "请指定测试方法，例如: make test-method METHOD=test_account_merge_functionality"; \
		exit 1; \
	fi
	@echo "运行测试方法: $(METHOD)"
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate; \
	python -m pytest tests/integration/ -k $(METHOD) -v