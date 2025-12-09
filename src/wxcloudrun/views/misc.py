"""
其他功能视图模块
包含计数器、环境配置、首页等功能
"""

import logging
from datetime import datetime
from flask import render_template, request, Response
from wxcloudrun import app
from wxcloudrun.response import make_succ_response, make_err_response, make_succ_empty_response
from wxcloudrun.dao import query_counterbyid, delete_counterbyid, insert_counter, update_counterbyid
from wxcloudrun.model import Counters
from config_manager import analyze_all_configs, detect_external_systems_status

app_logger = logging.getLogger('log')


@app.route('/')
def index():
    """
    :return: 返回index页面
    """
    app.logger.info("主页访问")
    return render_template('index.html')


@app.route('/env')
def env_viewer():
    """
    :return: 返回环境配置查看器页面
    """
    app.logger.info("环境配置查看器页面访问")
    try:
        with open('static/env_viewer.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "环境配置查看器页面未找到", 404


@app.route('/api/count', methods=['POST'])
def count():
    """
    :return:计数结果/清除结果
    """

    # 获取请求体参数
    params = request.get_json()
    app.logger.info(f"接收到计数器POST请求，参数: {params}")

    # 检查action参数
    if 'action' not in params:
        app.logger.warning("请求中缺少action参数")
        return make_err_response('缺少action参数')

    # 按照不同的action的值，进行不同的操作
    action = params['action']
    app.logger.info(f"执行操作: {action}")

    # 执行自增操作
    if action == 'inc':
        app.logger.info("开始执行计数器自增操作")
        counter = query_counterbyid(1)
        app.logger.info(f"查询到的计数器: {counter.count if counter else 'None'}")

        if counter is None:
            app.logger.info("计数器不存在，创建新的计数器，值设为1")
            counter = Counters()
            counter.id = 1
            counter.count = 1
            counter.created_at = datetime.now()
            counter.updated_at = datetime.now()
            insert_counter(counter)
            app.logger.info("新计数器已插入数据库")
        else:
            app.logger.info(f"计数器存在，当前值: {counter.count}，即将递增")
            counter.count += 1
            app.logger.info(f"递增后值: {counter.count}")
            counter.updated_at = datetime.now()
            update_counterbyid(counter)
            app.logger.info("计数器已更新")

        app.logger.info(f"返回计数值: {counter.count}")
        return make_succ_response(counter.count)

    # 执行清0操作
    elif action == 'clear':
        app.logger.info("执行清零操作")
        delete_counterbyid(1)
        app.logger.info("计数器已清零")
        return make_succ_empty_response()

    # action参数错误
    else:
        app.logger.warning(f"无效的action参数: {action}")
        return make_err_response('action参数错误')


@app.route('/api/count', methods=['GET'])
def get_count():
    """
    :return: 计数的值
    """
    app.logger.info("接收到计数器GET请求")
    counter = query_counterbyid(1)
    count_value = 0 if counter is None else counter.count
    app.logger.info(f"查询到的计数器值: {count_value}")
    return make_succ_response(count_value)


@app.route('/api/get_envs', methods=['GET'])
def get_envs():
    """
    获取环境配置信息
    :return: 环境配置详细信息（支持JSON和TOML格式）
    """
    app.logger.info("接收到环境配置GET请求")

    try:
        # 获取配置分析结果
        config_analysis = analyze_all_configs()

        # 获取外部系统状态
        external_systems = detect_external_systems_status()

        # 检查请求的格式
        accept_header = request.headers.get('Accept', '')
        format_param = request.args.get('format', '').lower()

        # 如果请求text/plain或format=txt，返回TOML格式
        if 'text/plain' in accept_header or format_param == 'txt' or format_param == 'toml':
            return _format_envs_as_toml(config_analysis, external_systems)

        # 默认返回JSON格式
        response_data = {
            **config_analysis,
            'timestamp': datetime.now().isoformat() + 'Z',
            'external_systems': external_systems
        }

        app.logger.info("成功获取环境配置信息")
        return make_succ_response(response_data)

    except Exception as e:
        app.logger.error(f"获取环境配置信息失败: {str(e)}")
        return make_err_response(f"获取环境配置信息失败: {str(e)}")


def _format_envs_as_toml(config_analysis, external_systems):
    """
    将环境配置信息格式化为TOML风格的文本格式
    """
    lines = []

    # 添加头部信息
    lines.append("# 安全守护应用环境配置信息")
    lines.append(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")

    # 基础信息
    lines.append("[基础信息]")
    lines.append(f"环境类型 = \"{config_analysis['environment']}\"")
    lines.append(f"配置文件 = \"{config_analysis['config_source']}\"")
    lines.append("")

    # 环境变量
    lines.append("[环境变量]")
    variables = config_analysis['variables']

    # 按名称排序
    for var_name in sorted(variables.keys()):
        var_info = variables[var_name]
        value = var_info['effective_value']
        data_type = var_info['data_type']

        # 根据数据类型格式化值
        if data_type == 'null' or value == '':
            formatted_value = 'null'
        elif data_type == 'boolean':
            formatted_value = value.lower() if value.lower() in [
                'true', 'false'] else value
        elif data_type in ['integer', 'float']:
            formatted_value = value
        else:
            # 字符串类型需要加引号
            formatted_value = f'"{value}"'

        # 添加注释信息
        comment = f"  # 数据类型: {data_type}"
        if var_info['is_sensitive']:
            comment += " [敏感信息]"

        lines.append(f"{var_name} = {formatted_value}{comment}")

    lines.append("")

    # 外部系统状态
    lines.append("[外部系统状态]")
    for system_name, system_info in external_systems.items():
        lines.append(f"# {system_info['name']}")
        lines.append(f"{system_name}.is_mock = {system_info['is_mock']}")
        lines.append(f"{system_name}.status = \"{system_info['status']}\"")

        # 添加配置信息
        if 'config' in system_info:
            lines.append(f"{system_name}.配置 = {{")
            for key, value in system_info['config'].items():
                if value is None:
                    formatted_value = 'null'
                elif isinstance(value, bool):
                    formatted_value = str(value).lower()
                elif isinstance(value, (int, float)):
                    formatted_value = str(value)
                else:
                    formatted_value = f'"{value}"'
                lines.append(f"  {key} = {formatted_value}")
            lines.append("}")
        lines.append("")

    # 添加结尾
    lines.append("# 配置信息结束")

    toml_content = "\n".join(lines)
    return Response(toml_content, mimetype='text/plain; charset=utf-8')
