"""
路由辅助函数单元测试
"""

import pytest
from unittest.mock import Mock, patch
from flask import Flask
from app.shared.utils.route_helpers import (
    with_validated_user,
    with_user_verification,
    execute_use_case,
    handle_use_case_result,
    get_json_params
)


class TestWithValidatedUser:
    """with_validated_user 装饰器测试"""

    def test_valid_token_adds_user_id(self):
        """测试有效 token 时添加 user_id"""
        app = Flask(__name__)

        with app.test_request_context():
            @with_validated_user
            def test_route(user_id: int):
                return {'user_id': user_id}

            with patch('app.shared.utils.route_helpers.verify_token') as mock_verify:
                mock_verify.return_value = ({'user_id': 123}, None)

                result = test_route()
                assert result['user_id'] == 123

    def test_invalid_token_returns_error(self):
        """测试无效 token 时返回错误"""
        app = Flask(__name__)

        with app.test_request_context():
            @with_validated_user
            def test_route(user_id: int):
                return {'user_id': user_id}

            with patch('app.shared.utils.route_helpers.verify_token') as mock_verify:
                mock_verify.return_value = (None, ({'error': 'invalid'}, 401))

                result = test_route()
                assert result[0]['error'] == 'invalid'


class TestExecuteUseCase:
    """execute_use_case 函数测试"""

    def test_execute_use_case_with_params(self):
        """测试执行 UseCase 并传递参数"""
        mock_use_case_class = Mock()
        mock_use_case_instance = Mock()
        mock_use_case_class.return_value = mock_use_case_instance
        mock_result = Mock()
        mock_use_case_instance.execute.return_value = mock_result

        result = execute_use_case(mock_use_case_class, user_id=123, name='test')

        mock_use_case_instance.execute.assert_called_once_with(user_id=123, name='test')
        assert result == mock_result


class TestHandleUseCaseResult:
    """handle_use_case_result 函数测试"""

    def test_successful_result(self):
        """测试成功结果"""
        from app.shared import make_succ_response

        mock_result = Mock()
        mock_result.is_success = True
        mock_result.data = {'user_id': 123}

        response = handle_use_case_result(mock_result)

        # 验证返回的是 Flask 响应对象
        assert response[1] == 200
        assert response[0].json['data'] == {'user_id': 123}

    def test_failed_result(self):
        """测试失败结果"""
        from app.shared import make_err_response

        mock_result = Mock()
        mock_result.is_success = False
        mock_result.message = '操作失败'

        response = handle_use_case_result(mock_result)

        # 验证返回的是 Flask 响应对象
        assert response[1] == 400
        # 验证响应数据结构
        response_data = response[0].get_json()
        assert 'message' in response_data or 'msg' in response_data
        assert ('操作失败' in response_data.get('message', '') or
                '操作失败' in response_data.get('msg', ''))


class TestGetJsonParams:
    """get_json_params 函数测试"""

    def test_valid_json_params(self):
        """测试有效的 JSON 参数"""
        app = Flask(__name__)

        with app.test_request_context(json={'key': 'value'}):
            params, error = get_json_params()

            assert params == {'key': 'value'}
            assert error is None

    def test_missing_json_body(self):
        """测试缺少 JSON 请求体"""
        app = Flask(__name__)

        with app.test_request_context(json={}, content_type='application/json'):
            params, error = get_json_params()

            assert params is None
            assert error == '缺少请求体参数'

    def test_required_fields_present(self):
        """测试必需字段存在"""
        app = Flask(__name__)

        with app.test_request_context(json={'key': 'value', 'name': 'test'}):
            params, error = get_json_params(required_fields=['key', 'name'])

            assert params == {'key': 'value', 'name': 'test'}
            assert error is None

    def test_required_fields_missing(self):
        """测试必需字段缺失"""
        app = Flask(__name__)

        with app.test_request_context(json={'key': 'value'}):
            params, error = get_json_params(required_fields=['key', 'name'])

            assert params is None
            assert '缺少参数' in error
            assert 'name' in error
