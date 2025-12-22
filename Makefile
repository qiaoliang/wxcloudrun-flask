# Makefile for backend testing

.PHONY: help test-integration ut test-all clean setup e2e

# 默认目标
help:
	@echo "可用的测试命令:"
	@echo "  make setup        - 设置测试环境"
	@echo "  make ut    - 运行单元测试"
	@echo "  make ut-s TEST=<test> - 运行单个单元测试用例"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-migration - 运行数据库迁移测试"
	@echo "  make e2e     - 运行E2E测试（需要Docker）"
	@echo "  make e2e-single TEST=<test> - 运行单个E2E测试用例"
	@echo "  make test-all     - 运行所有测试"
	@echo "  make test-coverage - 生成测试覆盖率报告"
	@echo "  make clean        - 清理测试文件"
	@echo "  make test-failed  - 运行之前失败的测试"
	@echo ""
	@echo "迁移测试专用命令:"
	@echo "  make test-migration-method METHOD=<method> - 运行特定测试方法"
	@echo "  make test-migration-performance - 运行性能测试"
	@echo ""
	@echo "示例:"
	@echo "  make ut            # 运行单元测试"
	@echo "  make ut VERBOSE=1  # 详细输出"
	@echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py  # 运行单个单元测试文件"
	@echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py::TestCommunityCheckinRuleService  # 运行单个测试类"
	@echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py::TestCommunityCheckinRuleService::test_create_rule  # 运行单个测试函数"
	@echo "  make test-integration     # 运行集成测试"
	@echo "  make test-integration VERBOSE=1  # 详细输出"
	@echo "  make test-migration       # 运行迁移测试"
	@echo "  make test-migration VERBOSE=1  # 详细输出"
	@echo "  make e2e-single TEST=test_multi_community_role_e2e.py  # 运行单个E2E测试文件"
	@echo "  make e2e-single TEST=test_multi_community_role_e2e.py::TestMultiCommunityRole::test_user_can_join_multiple_communities  # 运行单个测试函数"

# 设置测试环境
setup:
	@if [ ! -d "venv_py312" ]; then \
		echo "创建虚拟环境..."; \
		python3.12 -m venv venv_py312; \
	fi
	@echo "激活虚拟环境并安装依赖..."
	@source venv_py312/bin/activate && \
	pip install -r requirements.txt && \
	pip install -r requirements-test.txt
	@echo "环境设置完成"

# 运行集成测试
test-integration: setup
	@echo "运行集成测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest tests/integration/ -v -s; \
	else \
		python -m pytest tests/integration/ -v; \
	fi

# 运行单个集成测试文件
test-registration: setup
	@echo "运行注册流程测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/test_registration_flow.py -v

test-account-merge: setup
	@echo "运行账号合并测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/test_account_merging.py -v

test-login-response: setup
	@echo "运行登录响应测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/test_unified_login_response.py -v

test-migration: setup
	@echo "运行数据库迁移测试..."
	@source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m pytest tests/integration/test_alembic_migration.py -v -s; \
	else \
		PYTHONPATH="$(pwd)/src:$PYTHONPATH" python -m pytest tests/integration/test_alembic_migration.py -v; \
	fi

test-migration-method: setup
	@if [ -z "$(METHOD)" ]; then \
		echo "请指定测试方法，例如: make test-migration-method METHOD=test_complete_migration_path"; \
		exit 1; \
	fi
	@echo "运行迁移测试方法: $(METHOD)"
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/test_database_migration.py -k $(METHOD) -v

test-migration-performance: setup
	@echo "运行迁移性能测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/test_database_migration.py::TestDatabaseMigration::test_migration_performance -v -s

# 运行单元测试
ut: setup
	@echo "运行单元测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest tests/unit/ -v -s; \
	else \
		python -m pytest tests/unit/ -v; \
	fi

# 运行单个单元测试
ut-s: setup
	@if [ -z "$(TEST)" ]; then \
		echo "请指定测试文件、测试类或测试函数，例如:"; \
		echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py"; \
		echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py::TestCommunityCheckinRuleService"; \
		echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py::TestCommunityCheckinRuleService::test_create_rule"; \
		exit 1; \
	fi
	@echo "=== 运行单个单元测试用例 ==="
	@echo "测试: $(TEST)"
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		python -m pytest $(TEST) -v -s; \
	else \
		python -m pytest $(TEST) -v; \
	fi
	@echo "✓ 单个单元测试完成"

# 运行所有测试
test-all: setup
	@echo "运行所有测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/ -v

# 生成测试覆盖率报告
test-coverage: setup
	@echo "生成测试覆盖率报告..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
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
test-failed: setup
	@echo "运行之前失败的测试..."
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/ --lf -v

# 运行特定测试类
test-class: setup
	@if [ -z "$(CLASS)" ]; then \
		echo "请指定测试类，例如: make test-class CLASS=TestAccountMerging"; \
		exit 1; \
	fi
	@echo "运行测试类: $(CLASS)"
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/ -k $(CLASS) -v

# 运行特定测试方法
test-method: setup
	@if [ -z "$(METHOD)" ]; then \
		echo "请指定测试方法，例如: make test-method METHOD=test_account_merge_functionality"; \
		exit 1; \
	fi
	@echo "运行测试方法: $(METHOD)"
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/integration/ -k $(METHOD) -v

# 运行E2E测试
e2e: setup
	@echo "=== 运行E2E测试 ==="
	@echo "注意: 每个测试函数将启动独立的 Flask 进程，使用内存数据库"
	@# 运行E2E测试
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest tests/e2e/ -v
	@echo "✓ E2E测试完成"

# 运行单个E2E测试用例
e2e-single: setup
	@if [ -z "$(TEST)" ]; then \
		echo "请指定测试文件或测试函数，例如:"; \
		echo "  make e2e-single TEST=test_multi_community_role_e2e.py"; \
		echo "  make e2e-single TEST=test_multi_community_role_e2e.py::TestMultiCommunityRole::test_user_can_join_multiple_communities"; \
		exit 1; \
	fi
	@echo "=== 运行单个E2E测试用例 ==="
	@echo "测试: $(TEST)"
	@echo "注意: 测试将启动独立的 Flask 进程，使用内存数据库"
	@export PYTHONPATH="$(pwd)/src:$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	python -m pytest $(TEST) -v
	@echo "✓ 单个E2E测试完成"
