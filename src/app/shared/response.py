"""
响应格式模块
统一API响应格式
"""
import json
from flask import Response


def make_succ_empty_response(msg='success'):
    """创建成功空响应"""
    data = json.dumps({'code': 1, 'data': {}, 'msg': msg})
    return Response(data, mimetype='application/json')


def make_succ_response(data, msg='success'):
    """创建成功响应"""
    data = json.dumps({'code': 1, 'data': data, 'msg': msg})
    return Response(data, mimetype='application/json')


def make_err_response(data={}, msg='error'):
    """创建错误响应"""
    data = json.dumps({'code': 0, 'data': data, 'msg': msg})
    return Response(data, mimetype='application/json')