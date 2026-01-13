# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SafeGuard is a backend-service safety monitoring application for elderly care communities:
- **Backend**: Flask 3.1.2 REST API with modular Blueprint architecture
- **Database**: SQLAlchemy 2.0.16 with Alembic migrations
- **Testing**: pytest (backend), Vitest/Playwright (frontend) with intelligent parallel execution

## Quick Start Commands

```bash
cd backend

# Environment setup (Python 3.12 required)
python3.12 -m venv venv_py312
source venv_py312/bin/activate
pip install -r requirements.txt
pip install -r requirements-test.txt

# Run local server
ENV_TYPE=function ./localrun.sh    # Development server on http://localhost:9999

# Testing (must run from backend/ directory)
make setup                 # Initial setup
make ut                    # Smart unit tests (auto-parallel, in-memory DB)
make it                    # Smart integration tests (in-memory DB)
make test-quick            # Quick single-file test
make test-all              # All tests
make test-coverage         # Coverage report
make ut-s TEST=tests/unit/test_xxx.py  # Single unit test file
make it-s TEST=tests/integration/test_xxx.py  # Single integration test file
# Database migrations
cd src
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

## Architecture  Overview

**Modular Blueprint Pattern:**
- 100% route modularization using Flask Blueprints
- Application Factory pattern in `src/app/__init__.py`
- 12 feature modules in `src/app/modules/`:
  - `auth/` - Authentication & JWT tokens
  - `user/` - User management
  - `community/` - Community CRUD operations
  - `checkin/` - Check-in rules & records
  - `supervision/` - Supervisor relationships
  - `events/` - Community events (call_for_help, supporting)
  - `sms/` - SMS verification
  - `share/` - Share links
  - `community_checkin/` - Community check-in rules
  - `user_checkin/` - Personal check-in rules
  - `community_dashboard/` - Community dashboard statistics
  - `misc/` - Utility endpoints

**All blueprints registered with `/api` prefix:**
```python
# From src/app/__init__.py
app.register_blueprint(events_bp, url_prefix='/api')
app.register_blueprint(community_bp, url_prefix='/api')
# ... etc
```

**Service Layer Pattern:**
- Business logic in service classes (e.g., `wxcloudrun/community_event_service.py`)
- Routes in `modules/*/routes.py` are thin - delegate to services
- Use `current_app` instead of global `app` variable
- SQLAlchemy 2.0 APIs only (not 1.x style)

## Testing Architecture

**Backend Smart Testing:**
- `smart_test_runner.py` automatically selects optimal parallel config
- Thread-safe test data generators ensure test isolation
- pytest-xdist for parallel execution (up to 4 workers)
- Three test types: unit, integration, e2e

## Important Development Notes

1. **Use SQLAlchemy 2.0 APIs only** - no 1.x style sessions
2. **Service classes** handle business logic, routes handle validation/delegation
3. **Use `current_app`** not global `app` in Blueprint modules
4. **All tests must run from `backend/` directory**
5. **Database operations** should use context managers: `with db.session.begin():`
6. **Shared utilities** go in `src/app/shared/`, not in Blueprint modules
7. **OpenAPI contract** in `backend/api-contract/openapi.yaml` - validate changes

## Environment Configuration

**ENV_TYPE** environment variable controls the runtime environment:
- `function` - Development environment (SQLite file database)
- `unit` - Unit testing environment (**in-memory database**)
- `uat` - UAT testing environment (SQLite file database)
- `prod` - Production environment (SQLite file database)

**IMPORTANT**: All backend unit and integration tests use in-memory database via `ENV_TYPE=unit`. When writing integration tests:
1. Use the provided test data generation methods to set up test data
2. When adding new data models, analyze whether testdata generator methods are needed first
3. Ensure testdata generator methods are available before writing test cases

## Commit Conventions
Use prefixes from `rules/commit-rule.md`:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation only
- `test:` - Adding/changing tests
- `refactor:` - Code refactoring
- `chore:` - Build/tools changes

## Common Workflows

### Adding a New Backend Feature
1. Define API contract in `backend/api-contract/openapi.yaml`
2. Create service in appropriate `wxcloudrun/*_service.py`
3. Add routes in `src/app/modules/*/routes.py`
4. Write unit tests in `backend/tests/unit/`
5. Write integration tests in `backend/tests/integration/`
6. Run `make ut && make it` to verify

### Writing Integration Tests
When adding integration tests for backend:
1. **Use test data generators** - All tests must use provided random test data generation methods
2. **Check for helpers** - When adding new data models, first analyze if helper methods are needed in test data generation
3. **Ensure isolation** - Each test should use unique data to avoid conflicts
4. **Follow the guide** - Reference `backend/docs/integration-test-writing-guide.md` for detailed patterns


## Related Documentation

- **Code Style Guide**: `docs/code-style-guide.md`
- **Integration Test Guide**: `docs/integration-test-writing-guide.md`
- **API Contract**: `api-contract/openapi.yaml`
- **Testing Rules**: `../rules/test-guide-01-测试用例设计与精简方法指南.md`
- **Commit Rules**: `../rules/commit-rule.md`

## Task Master AI Instructions
**Import Task Master's development workflow commands and guidelines, treat as if import is in the main CLAUDE.md file.**
@./.taskmaster/CLAUDE.md
