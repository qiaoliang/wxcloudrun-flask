import json
from wxcloudrun.response import make_succ_empty_response, make_succ_response, make_err_response


class TestResponse:
    """Test cases for response module functions"""

    def test_make_succ_empty_response_default(self):
        """Test make_succ_empty_response with default message"""
        response = make_succ_empty_response()
        data = json.loads(response.get_data(as_text=True))
        
        assert data['code'] == 1
        assert data['data'] == {}
        assert data['msg'] == 'success'
        assert response.mimetype == 'application/json'

    def test_make_succ_empty_response_custom_msg(self):
        """Test make_succ_empty_response with custom message"""
        response = make_succ_empty_response('custom message')
        data = json.loads(response.get_data(as_text=True))
        
        assert data['code'] == 1
        assert data['data'] == {}
        assert data['msg'] == 'custom message'
        assert response.mimetype == 'application/json'

    def test_make_succ_response_default_msg(self):
        """Test make_succ_response with default message"""
        test_data = {'key': 'value', 'number': 42}
        response = make_succ_response(test_data)
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 1
        assert result['data'] == test_data
        assert result['msg'] == 'success'
        assert response.mimetype == 'application/json'

    def test_make_succ_response_custom_msg(self):
        """Test make_succ_response with custom message"""
        test_data = {'user': 'test', 'id': 123}
        response = make_succ_response(test_data, 'custom success')
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 1
        assert result['data'] == test_data
        assert result['msg'] == 'custom success'
        assert response.mimetype == 'application/json'

    def test_make_err_response_default(self):
        """Test make_err_response with default values"""
        response = make_err_response()
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 0
        assert result['data'] == {}
        assert result['msg'] == 'error'
        assert response.mimetype == 'application/json'

    def test_make_err_response_custom_data_and_msg(self):
        """Test make_err_response with custom data and message"""
        test_data = {'error': 'something went wrong', 'code': 500}
        response = make_err_response(test_data, 'custom error message')
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 0
        assert result['data'] == test_data
        assert result['msg'] == 'custom error message'
        assert response.mimetype == 'application/json'

    def test_make_err_response_custom_data_only(self):
        """Test make_err_response with custom data only"""
        test_data = {'error': 'validation failed'}
        response = make_err_response(test_data)
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 0
        assert result['data'] == test_data
        assert result['msg'] == 'error'
        assert response.mimetype == 'application/json'

    def test_make_err_response_custom_msg_only(self):
        """Test make_err_response with custom message only (using default empty dict)"""
        response = make_err_response(msg='custom error')
        result = json.loads(response.get_data(as_text=True))
        
        assert result['code'] == 0
        assert result['data'] == {}
        assert result['msg'] == 'custom error'
        assert response.mimetype == 'application/json'