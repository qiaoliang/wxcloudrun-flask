import json

from flask import jsonify


def make_succ_empty_response(msg='success'):
    return jsonify({'code': 1, 'data': {}, 'msg': msg})


def make_succ_response(data, msg='success'):
    return jsonify({'code': 1, 'data': data, 'msg': msg})


def make_err_response(data={}, msg='error'):
    return jsonify({'code': 0, 'data': data, 'msg': msg})
