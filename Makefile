# Makefile for backend testing

.PHONY: help test-integration ut test-all clean setup e2e it its apitest

# 默认目标
help:
	@echo "可用的测试命令:"
	@echo "  make setup        - 设置测试环境"
	@echo "  make ut           - 运行单元测试"
	@echo "  make ut [TEST=<test>] - 运行单元测试（可选指定测试文件）"
	@echo "  make test-integration - 运行集成测试"
	@echo "  make test-migration - 运行数据库迁移测试"
	@echo "  make e2e     - 运行E2E测试（需要Docker）"
	@echo "  make e2e-single TEST=<test> - 运行单个E2E测试用例"
	@echo "  make it            - 运行集成测试"
	@echo "  make it [TEST=<test>] - 运行集成测试（可选指定测试文件）"
	@echo "  make test-all     - 运行所有测试"
	@echo "  make test-coverage - 生成测试覆盖率报告"
	@echo "  make clean        - 清理测试文件"
	@echo "  make test-failed  - 运行之前失败的测试"
	@echo "  make apitest      - 运行API契约测试"
	@echo ""
	@echo "迁移测试专用命令:"
	@echo "  make test-migration-method METHOD=<method> - 运行特定测试方法"
	@echo "  make test-migration-performance - 运行性能测试"
	@echo ""
	@echo "示例:"
	@echo "  make ut            # 运行所有单元测试"
	@echo "  make ut TEST=tests/unit/test_user_service.py  # 运行单个测试文件"
	@echo "  make ut TEST=test_user_service.py              # 相对路径（自动添加 tests/unit/ 前缀）"
	@echo "  make ut VERBOSE=1  # 详细输出"
	@echo ""
	@echo "  make ut-s TEST=tests/unit/test_community_checkin_rule_service.py  # 运行单个单元测试文件（旧命令，仍可用）"
	@echo "  make it            # 运行所有集成测试"
	@echo "  make it TEST=tests/integration/test_user_integration.py  # 运行单个集成测试文件"
	@echo "  make it TEST=test_user_integration.py              # 相对路径（自动添加 tests/integration/ 前缀）"
	@echo "  make it VERBOSE=1  # 详细输出"
	@echo ""
	@echo "  make its TEST=tests/integration/test_user_integration.py  # 运行单个集成测试文件（旧命令，仍可用）"
	@echo "  make test-integration     # 运行集成测试（旧命令，仍可用）"
	@echo "  make test-migration       # 运行迁移测试"
	@echo "  make apitest              # 运行API契约测试"

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

# 运行单元测试（使用智能配置）
# 使用方法:
#   make ut                                    # 运行所有单元测试
#   make ut TEST=tests/unit/test_user_service.py       # 完整路径
#   make ut TEST=test_user_service.py                  # 相对路径
ut: setup
	@echo "运行单元测试..."
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ -z "$(TEST)" ]; then \
		if [ "$(VERBOSE)" = "1" ]; then \
			python smart_test_runner.py tests/unit/ -v; \
		else \
			python smart_test_runner.py tests/unit/; \
		fi \
	else \
		if [ -f "$(TEST)" ]; then \
			echo "运行测试文件: $(TEST)"; \
			if [ "$(VERBOSE)" = "1" ]; then \
				python smart_test_runner.py $(TEST) -v; \
			else \
				python smart_test_runner.py $(TEST); \
			fi \
		elif [ -f "tests/unit/$(TEST)" ]; then \
			echo "运行测试文件: tests/unit/$(TEST)"; \
			if [ "$(VERBOSE)" = "1" ]; then \
				python smart_test_runner.py tests/unit/$(TEST) -v; \
			else \
				python smart_test_runner.py tests/unit/$(TEST); \
			fi \
		else \
			echo "错误: 测试文件不存在: $(TEST)"; \
			echo "请检查文件路径或使用 make help 查看用法"; \
			exit 1; \
		fi \
	fi

# 运行单个单元测试
ut-s: setup
	@if [ -z "$(TEST)" ]; then \
		echo "错误: 请指定测试文件或测试用例，例如: make ut-s TEST=tests/unit/test_user_service.py"; \
		exit 1; \
	fi
	@echo "运行单个单元测试: $(TEST)"
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		python smart_test_runner.py $(TEST) -v; \
	else \
		python smart_test_runner.py $(TEST); \
	fi

# 运行集成测试（使用智能配置）
# 使用方法:
#   make it                                                 # 运行所有集成测试
#   make it TEST=tests/integration/test_user_integration.py      # 完整路径
#   make it TEST=test_user_integration.py                        # 相对路径
it: setup
	@echo "=== 运行集成测试 ==="
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ -z "$(TEST)" ]; then \
		echo "运行所有集成测试用例..."; \
		if [ "$(VERBOSE)" = "1" ]; then \
			python smart_test_runner.py tests/integration/ -v; \
		else \
			python smart_test_runner.py tests/integration/; \
		fi \
	else \
		if [ -f "$(TEST)" ]; then \
			echo "运行测试文件: $(TEST)"; \
			if [ "$(VERBOSE)" = "1" ]; then \
				python smart_test_runner.py $(TEST) -v; \
			else \
				python smart_test_runner.py $(TEST); \
			fi \
		elif [ -f "tests/integration/$(TEST)" ]; then \
			echo "运行测试文件: tests/integration/$(TEST)"; \
			if [ "$(VERBOSE)" = "1" ]; then \
				python smart_test_runner.py tests/integration/$(TEST) -v; \
			else \
				python smart_test_runner.py tests/integration/$(TEST); \
			fi \
		else \
			echo "错误: 测试文件不存在: $(TEST)"; \
			echo "请检查文件路径或使用 make help 查看用法"; \
			exit 1; \
		fi \
	fi
	@echo "✓ 集成测试完成"

# 运行单个集成测试
its: setup
	@if [ -z "$(TEST)" ]; then \
		echo "错误: 请指定测试文件或测试用例，例如: make its TEST=tests/integration/test_user_integration.py"; \
		exit 1; \
	fi
	@echo "运行单个集成测试: $(TEST)"
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	if [ "$(VERBOSE)" = "1" ]; then \
		python smart_test_runner.py $(TEST) -v; \
	else \
		python smart_test_runner.py $(TEST); \
	fi

# 智能测试命令
.PHONY: test-smart test-parallel test-unit-new test-integration-new test-all-new

# 智能测试（根据规模自动选择配置）
test-smart:
	@echo "=== 智能测试执行 ==="
	@source venv_py312/bin/activate && python smart_test_runner.py tests/

# 强制并行测试
test-parallel:
	@echo "=== 并行测试执行 ==="
	@source venv_py312/bin/activate && python smart_test_runner.py tests/ -p --max-workers 4

# 单元测试
test-unit-new:
	@echo "=== 单元测试 ==="
	@source venv_py312/bin/activate && python smart_test_runner.py tests/unit/

# 集成测试
test-integration-new:
	@echo "=== 集成测试 ==="
	@source venv_py312/bin/activate && python smart_test_runner.py tests/integration/

# 快速测试（单个文件）
test-quick:
	@echo "=== 快速测试 ==="
	@source venv_py312/bin/activate && python smart_test_runner.py tests/unit/test_user_search_phone_hash.py

# API契约测试
# 验证前端调用的API与后端返回的数据结构是否一致
apitest: setup
	@echo "=== 运行API契约测试 ==="
	@export PYTHONPATH="$(pwd)/src:$$PYTHONPATH"; \
	source venv_py312/bin/activate && \
	export ENV_TYPE=function; \
	export PHONE_ENCRYPTION_KEY=test_phone_encryption_key_for_contract_tests; \
	if [ -z "$(TEST)" ]; then \
		echo "运行所有API契约测试..."; \
		if [ "$(VERBOSE)" = "1" ]; then \
			pytest tests/contract/test_api_contract.py -v; \
		else \
			pytest tests/contract/test_api_contract.py; \
		fi \
	else \
		echo "运行测试: $(TEST)"; \
		if [ "$(VERBOSE)" = "1" ]; then \
			pytest $(TEST) -v; \
		else \
			pytest $(TEST); \
		fi \
	fi
	@echo "✓ API契约测试完成"
