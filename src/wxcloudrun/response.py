import json

from flask import Response


def make_succ_empty_response(msg='success'):
    data = json.dumps({'code': 1, 'data': {}, 'msg': msg})
    return Response(data, mimetype='application/json')


def make_succ_response(data, msg='success'):
    data = json.dumps({'code': 1, 'data': data, 'msg': msg})
    return Response(data, mimetype='application/json')


def make_err_response(data={}, msg='error'):
    data = json.dumps({'code': 0, 'data': data, 'msg': msg})
    return Response(data, mimetype='application/json')
