"""
社区数字看板 Blueprint 模块
"""
from flask import Blueprint

community_dashboard_bp = Blueprint('community_dashboard', __name__)

from . import routes
