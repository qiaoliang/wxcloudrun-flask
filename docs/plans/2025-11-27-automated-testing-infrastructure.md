# Automated Testing Infrastructure Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Establish comprehensive automated testing infrastructure with unit, integration, and API tests for the Flask application.

**Architecture:** Implement pytest-based testing framework with fixtures for database, application context, and API testing. Create separate test modules for each component of the Flask application.

**Tech Stack:** pytest, pytest-flask, factory-boy (for test data), coverage.py (for test coverage)

---

### Task 1: Set up testing dependencies

**Files:**
- Modify: `requirements.txt`
- Create: `requirements-test.txt`

**Step 1: Add testing dependencies to requirements-test.txt**

```txt
pytest==7.4.3
pytest-flask==1.2.0
pytest-cov==4.1.0
factory-boy==3.3.0
Faker==19.13.0
```

**Step 2: Run test to verify it fails**

Run: `pip install -r requirements-test.txt`
Expected: FAIL with "requirements-test.txt file not found"

**Step 3: Write minimal implementation**

Create the file with the content from Step 1.

**Step 4: Run test to verify it passes**

Run: `pip install -r requirements-test.txt`
Expected: PASS

**Step 5: Commit**

```bash
git add requirements-test.txt
git commit -m "feat: add testing dependencies"
```

### Task 2: Create basic test directory structure

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

Create empty files to establish the test structure.

**Step 2: Run test to verify it fails**

Run: `pytest tests/`
Expected: FAIL with "tests directory not found"

**Step 3: Write minimal implementation**

```python
# tests/__init__.py
# Empty file to make tests a Python package
```

```python
# tests/conftest.py
import pytest
from run import app
from wxcloudrun import db

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Use in-memory database for testing
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/`
Expected: PASS (no tests to run but no errors)

**Step 5: Commit**

```bash
git add tests/__init__.py tests/conftest.py
git commit -m "feat: add basic test structure"
```

### Task 3: Create basic API tests for counter endpoints

**Files:**
- Create: `tests/test_api.py`

**Step 1: Write the failing test**

```python
def test_get_count_initial_value():
    """Test getting initial count value."""
    pass

def test_post_count_inc():
    """Test incrementing count."""
    pass

def test_post_count_clear():
    """Test clearing count."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_api.py -v`
Expected: FAIL with "tests/test_api.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_api.py
def test_get_count_initial_value(client):
    """Test getting initial count value."""
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 0  # Initial count should be 0


def test_post_count_inc(client):
    """Test incrementing count."""
    # First increment
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 1  # Should be 1 after first increment
    
    # Second increment
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 2  # Should be 2 after second increment


def test_post_count_clear(client):
    """Test clearing count."""
    # Increment first to set a value
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    
    # Clear the count
    response = client.post('/api/count', json={'action': 'clear'})
    assert response.status_code == 200
    
    # Verify count is back to 0
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_api.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_api.py
git commit -m "feat: add API tests for counter endpoints"
```

### Task 4: Create tests for database operations

**Files:**
- Create: `tests/test_dao.py`

**Step 1: Write the failing test**

```python
def test_query_counterbyid():
    """Test querying counter by ID."""
    pass

def test_insert_counter():
    """Test inserting a counter."""
    pass

def test_update_counterbyid():
    """Test updating counter by ID."""
    pass

def test_delete_counterbyid():
    """Test deleting counter by ID."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_dao.py -v`
Expected: FAIL with "tests/test_dao.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_dao.py
import pytest
from datetime import datetime
from wxcloudrun.dao import query_counterbyid, insert_counter, update_counterbyid, delete_counterbyid
from wxcloudrun.model import Counters
from wxcloudrun import db


def test_query_counterbyid(client):
    """Test querying counter by ID."""
    # Create a counter
    counter = Counters()
    counter.id = 1
    counter.count = 5
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    insert_counter(counter)
    
    # Query the counter
    result = query_counterbyid(1)
    assert result is not None
    assert result.id == 1
    assert result.count == 5


def test_insert_counter(client):
    """Test inserting a counter."""
    counter = Counters()
    counter.id = 2
    counter.count = 10
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    insert_counter(counter)
    
    # Verify the counter was inserted
    result = query_counterbyid(2)
    assert result is not None
    assert result.id == 2
    assert result.count == 10


def test_update_counterbyid(client):
    """Test updating counter by ID."""
    # First insert a counter
    counter = Counters()
    counter.id = 3
    counter.count = 15
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    insert_counter(counter)
    
    # Update the counter
    counter.count = 20
    counter.updated_at = datetime.now()
    update_counterbyid(counter)
    
    # Verify the counter was updated
    result = query_counterbyid(3)
    assert result is not None
    assert result.id == 3
    assert result.count == 20


def test_delete_counterbyid(client):
    """Test deleting counter by ID."""
    # First insert a counter
    counter = Counters()
    counter.id = 4
    counter.count = 25
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    insert_counter(counter)
    
    # Verify it exists
    result = query_counterbyid(4)
    assert result is not None
    
    # Delete the counter
    delete_counterbyid(4)
    
    # Verify it's deleted
    result = query_counterbyid(4)
    assert result is None
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_dao.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_dao.py
git commit -m "feat: add database operation tests"
```

### Task 5: Create tests for model

**Files:**
- Create: `tests/test_model.py`

**Step 1: Write the failing test**

```python
def test_counter_model_creation():
    """Test creating a Counter model instance."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_model.py -v`
Expected: FAIL with "tests/test_model.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_model.py
import pytest
from datetime import datetime
from wxcloudrun.model import Counters


def test_counter_model_creation(client):
    """Test creating a Counter model instance."""
    counter = Counters()
    counter.id = 1
    counter.count = 42
    counter.created_at = datetime.now()
    counter.updated_at = datetime.now()
    
    assert counter.id == 1
    assert counter.count == 42
    assert counter.created_at is not None
    assert counter.updated_at is not None
    assert counter.__tablename__ == 'Counters'
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_model.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_model.py
git commit -m "feat: add model tests"
```

### Task 6: Create tests for response module

**Files:**
- Create: `tests/test_response.py`

**Step 1: Write the failing test**

```python
def test_make_succ_response():
    """Test successful response creation."""
    pass

def test_make_succ_empty_response():
    """Test successful empty response creation."""
    pass

def test_make_err_response():
    """Test error response creation."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_response.py -v`
Expected: FAIL with "tests/test_response.py file not found or response module not found"

**Step 3: Write minimal implementation**

First, I need to check the response.py file to understand its structure:

```python
# From wxcloudrun/response.py
from flask import jsonify

def make_succ_response(data):
    """
    成功响应
    :param data: 响应数据
    :return: 响应对象
    """
    return jsonify({'code': 0, 'data': data})

def make_succ_empty_response():
    """
    成功响应，无数据
    :return: 响应对象
    """
    return jsonify({'code': 0, 'data': None})

def make_err_response(err_msg, data=None):
    """
    错误响应
    :param err_msg: 错误信息
    :param data: 响应数据
    :return: 响应对象
    """
    if data is None:
        return jsonify({'code': -1, 'errorMsg': err_msg})
    else:
        return jsonify({'code': -1, 'errorMsg': err_msg, 'data': data})
```

Now the test file:

```python
# tests/test_response.py
from wxcloudrun.response import make_succ_response, make_succ_empty_response, make_err_response


def test_make_succ_response():
    """Test successful response creation."""
    response = make_succ_response({'message': 'success'})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert json_data['data'] == {'message': 'success'}


def test_make_succ_empty_response():
    """Test successful empty response creation."""
    response = make_succ_empty_response()
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['code'] == 0
    assert json_data['data'] is None


def test_make_err_response():
    """Test error response creation."""
    response = make_err_response('Something went wrong')
    assert response.status_code == 200  # Error responses still return 200
    json_data = response.get_json()
    assert json_data['code'] == -1
    assert json_data['errorMsg'] == 'Something went wrong'
    
    # Test with data
    response_with_data = make_err_response('Error occurred', {'error_code': 'E001'})
    assert response_with_data.status_code == 200
    json_data_with_data = response_with_data.get_json()
    assert json_data_with_data['code'] == -1
    assert json_data_with_data['errorMsg'] == 'Error occurred'
    assert json_data_with_data['data'] == {'error_code': 'E001'}
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_response.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_response.py
git commit -m "feat: add response module tests"
```

### Task 7: Create tests for login functionality

**Files:**
- Create: `tests/test_login.py`

**Step 1: Write the failing test**

```python
def test_login_endpoint():
    """Test the login endpoint with a mock code."""
    pass

def test_update_user_info_endpoint():
    """Test the update user info endpoint."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_login.py -v`
Expected: FAIL with "tests/test_login.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_login.py
import pytest
import os
from unittest.mock import patch
import jwt
from wxcloudrun import db


def test_login_endpoint(client):
    """Test the login endpoint with a mock code."""
    # Mock the response from WeChat API
    mock_wx_response = {
        'openid': 'mock_openid_123',
        'session_key': 'mock_session_key_456'
    }
    
    with patch('wxcloudrun.views.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_wx_response
        mock_get.return_value.status_code = 200
        
        # Call the login endpoint
        response = client.post('/api/login', 
                              json={'code': 'test_code_789'},
                              content_type='application/json')
        
        # Check the response
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert 'data' in data
        assert 'token' in data['data']
        
        # Verify that the token can be decoded
        token = data['data']['token']
        decoded = jwt.decode(token, os.environ.get('TOKEN_SECRET', 'your-secret-key'), algorithms=['HS256'])
        assert decoded['openid'] == 'mock_openid_123'
        assert decoded['session_key'] == 'mock_session_key_456'


def test_update_user_info_endpoint(client):
    """Test the update user info endpoint."""
    # First, get a valid token by mocking the login
    mock_wx_response = {
        'openid': 'mock_openid_123',
        'session_key': 'mock_session_key_456'
    }
    
    with patch('wxcloudrun.views.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_wx_response
        mock_get.return_value.status_code = 200
        
        # Get a token
        login_response = client.post('/api/login', 
                                   json={'code': 'test_code_789'},
                                   content_type='application/json')
        token = login_response.get_json()['data']['token']
        
        # Now test update user info with the token
        response = client.post('/api/update_user_info',
                              json={
                                  'token': token,
                                  'avatar_url': 'https://example.com/avatar.jpg',
                                  'nickname': 'Test User'
                              },
                              content_type='application/json')
        
        assert response.status_code == 200
        data = response.get_json()
        assert data['code'] == 0
        assert data['data']['message'] == '用户信息更新成功'


def test_update_user_info_missing_token(client):
    """Test update user info endpoint without token."""
    response = client.post('/api/update_user_info',
                          json={
                              'avatar_url': 'https://example.com/avatar.jpg',
                              'nickname': 'Test User'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == -1
    assert '缺少token参数' in data['errorMsg']


def test_update_user_info_invalid_token(client):
    """Test update user info endpoint with invalid token."""
    response = client.post('/api/update_user_info',
                          json={
                              'token': 'invalid_token',
                              'avatar_url': 'https://example.com/avatar.jpg',
                              'nickname': 'Test User'
                          },
                          content_type='application/json')
    
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == -1
    assert 'token无效' in data['errorMsg']
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_login.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_login.py
git commit -m "feat: add login and user info tests"
```

### Task 8: Create a test configuration and setup CI

**Files:**
- Create: `pytest.ini`
- Modify: `README.md` (add testing instructions)

**Step 1: Write the failing test**

Create pytest configuration.

**Step 2: Run test to verify it fails**

Run: `pytest --version`
Expected: Should work but without specific configuration.

**Step 3: Write minimal implementation**

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -ra 
    --strict-markers
    --strict-config
    --cov=wxcloudrun
    --cov-report=html
    --cov-report=term-missing:skip-covered
    --cov-fail-under=80
```

```markdown
# Update README.md to include testing instructions

## Testing

To run the tests:

```bash
# Install test dependencies
pip install -r requirements-test.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=wxcloudrun --cov-report=html

# Run specific test file
pytest tests/test_api.py
```
```

**Step 4: Run test to verify it passes**

Run: `pytest --collect-only`
Expected: PASS (tests should be discovered)

**Step 5: Commit**

```bash
git add pytest.ini README.md
git commit -m "feat: add pytest configuration and testing docs"
```

### Task 9: Create a test for error handling in views

**Files:**
- Create: `tests/test_error_handling.py`

**Step 1: Write the failing test**

```python
def test_count_missing_action():
    """Test /api/count endpoint with missing action parameter."""
    pass

def test_count_invalid_action():
    """Test /api/count endpoint with invalid action parameter."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_error_handling.py -v`
Expected: FAIL with "tests/test_error_handling.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_error_handling.py
def test_count_missing_action(client):
    """Test /api/count endpoint with missing action parameter."""
    response = client.post('/api/count', json={})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == -1
    assert '缺少action参数' in data['errorMsg']


def test_count_invalid_action(client):
    """Test /api/count endpoint with invalid action parameter."""
    response = client.post('/api/count', json={'action': 'invalid_action'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == -1
    assert 'action参数错误' in data['errorMsg']
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_error_handling.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_error_handling.py
git commit -m "feat: add error handling tests"
```

### Task 10: Create a comprehensive test runner script

**Files:**
- Create: `scripts/run_tests.py`

**Step 1: Write the failing test**

Create a script to run tests with various options.

**Step 2: Run test to verify it fails**

Run: `python scripts/run_tests.py`
Expected: FAIL with "scripts/run_tests.py file not found"

**Step 3: Write minimal implementation**

```python
#!/usr/bin/env python
"""
Test runner script for the Flask application.

This script provides various options for running tests:
- Run all tests
- Run with coverage
- Run specific test files
- Generate coverage reports
"""

import sys
import subprocess
import argparse


def run_tests(test_path=None, with_coverage=False, html_report=False, min_coverage=80):
    """
    Run tests with optional coverage.
    
    Args:
        test_path (str): Path to specific test file or directory
        with_coverage (bool): Whether to run with coverage
        html_report (bool): Whether to generate HTML coverage report
        min_coverage (int): Minimum required coverage percentage
    """
    cmd = [sys.executable, '-m', 'pytest']
    
    if test_path:
        cmd.append(test_path)
    else:
        cmd.append('tests/')
    
    if with_coverage:
        cmd.extend([
            '--cov=wxcloudrun',
            f'--cov-fail-under={min_coverage}'
        ])
        
        if html_report:
            cmd.extend(['--cov-report=html', '--cov-report=term-missing'])
        else:
            cmd.extend(['--cov-report=term-missing'])
    
    # Add verbose output by default
    cmd.append('-v')
    
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def main():
    parser = argparse.ArgumentParser(description='Test runner for Flask application')
    parser.add_argument('test_path', nargs='?', help='Specific test file or directory to run')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage')
    parser.add_argument('--html-report', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--min-coverage', type=int, default=80, help='Minimum required coverage percentage')
    
    args = parser.parse_args()
    
    return run_tests(
        test_path=args.test_path,
        with_coverage=args.coverage,
        html_report=args.html_report,
        min_coverage=args.min_coverage
    )


if __name__ == '__main__':
    sys.exit(main())
```

**Step 4: Run test to verify it passes**

Run: `python scripts/run_tests.py --help`
Expected: PASS (shows help message)

**Step 5: Commit**

```bash
git add scripts/run_tests.py
git commit -m "feat: add test runner script"
```

### Task 11: Create integration tests for complete workflows

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the failing test**

```python
def test_complete_counter_workflow():
    """Test a complete workflow: get initial value, increment, get updated value, clear."""
    pass
```

**Step 2: Run test to verify it fails**

Run: `pytest tests/test_integration.py -v`
Expected: FAIL with "tests/test_integration.py file not found"

**Step 3: Write minimal implementation**

```python
# tests/test_integration.py
def test_complete_counter_workflow(client):
    """Test a complete workflow: get initial value, increment, get updated value, clear."""
    # 1. Get initial count (should be 0)
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 0
    
    # 2. Increment the count
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 1
    
    # 3. Get the updated count
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 1
    
    # 4. Increment again
    response = client.post('/api/count', json={'action': 'inc'})
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 2
    
    # 5. Clear the count
    response = client.post('/api/count', json={'action': 'clear'})
    assert response.status_code == 200
    
    # 6. Verify count is back to 0
    response = client.get('/api/count')
    assert response.status_code == 200
    data = response.get_json()
    assert data['code'] == 0
    assert data['data'] == 0
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/test_integration.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add integration tests"
```

### Task 12: Update README with comprehensive testing documentation

**Files:**
- Modify: `README.md`

**Step 1: Write the failing test**

Update the README with comprehensive testing documentation.

**Step 2: Run test to verify it fails**

Run: `pytest tests/`
Expected: Tests should run but README documentation is missing.

**Step 3: Write minimal implementation**

Add to README.md after the existing content:

```markdown
## Testing

This project uses pytest for testing. The test suite includes unit tests, integration tests, and API tests.

### Running Tests

#### Install Test Dependencies
```bash
pip install -r requirements-test.txt
```

#### Run All Tests
```bash
pytest
```

#### Run Tests with Coverage
```bash
pytest --cov=wxcloudrun --cov-report=html
# This will generate an HTML coverage report in the htmlcov/ directory
```

#### Run Specific Test File
```bash
pytest tests/test_api.py
```

#### Run Tests with Verbose Output
```bash
pytest -v
```

#### Run Tests and Generate Coverage Report
```bash
python scripts/run_tests.py --coverage --html-report
```

### Test Structure

The tests are organized as follows:

- `tests/test_api.py`: API endpoint tests for counter functionality
- `tests/test_dao.py`: Database access object tests
- `tests/test_model.py`: Model tests
- `tests/test_response.py`: Response utility function tests
- `tests/test_login.py`: Login and user info endpoint tests
- `tests/test_error_handling.py`: Error handling tests
- `tests/test_integration.py`: Integration tests for complete workflows

### Adding New Tests

When adding new functionality:

1. Create appropriate test files in the `tests/` directory
2. Follow the naming convention `test_<module_name>.py`
3. Write both positive and negative test cases
4. Ensure test coverage remains above 80%
5. Run the full test suite before committing changes
```

**Step 4: Run test to verify it passes**

Run: `pytest tests/`
Expected: PASS (with updated documentation)

**Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add comprehensive testing documentation"
```

### Task 13: Final verification and cleanup

**Files:**
- Run: All tests

**Step 1: Write the failing test**

Run a full test suite to verify everything works.

**Step 2: Run test to verify it fails**

Run: `pytest tests/ --cov=wxcloudrun --cov-report=term-missing`
Expected: All tests should pass and coverage should be adequate.

**Step 3: Write minimal implementation**

Run the complete test suite to ensure all tests pass.

**Step 4: Run test to verify it passes**

Run: `pytest tests/ --cov=wxcloudrun --cov-report=term-missing`
Expected: PASS (all tests pass with good coverage)

**Step 5: Commit**

```bash
git add .
git commit -m "feat: complete automated testing infrastructure"
```