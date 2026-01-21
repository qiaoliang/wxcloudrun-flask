"""
契约测试辅助函数
提供通用的契约验证逻辑
"""
import yaml
from pathlib import Path


def load_schema(module_name):
    """加载指定模块的 OpenAPI 规范"""
    schema_path = Path(__file__).parent.parent.parent / "api-contract" / f"{module_name}.yaml"
    with open(schema_path, encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_response_structure(response):
    """验证响应符合 StandardResponse 结构"""
    data = response.get_json()
    assert "code" in data, "响应缺少 'code' 字段"
    assert "msg" in data, "响应缺少 'msg' 字段"
    assert "data" in data, "响应缺少 'data' 字段"
    return data


def get_test_user_credentials():
    """获取测试用户凭据"""
    return {
        'phone_number': '13141516171',
        'password': 'F1234567'
    }


def validate_response_fields(data, required_fields):
    """验证响应数据包含必需字段"""
    for field in required_fields:
        assert field in data, f"响应数据缺少字段: {field}"
