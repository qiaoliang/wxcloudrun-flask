"""
已弃用：所有模型已迁移到 database/models.py
此文件保留仅为向后兼容，实际功能已移除
"""

# 注意：此文件中的所有类定义已迁移到 database/models.py
# 请使用 database.models 中的类定义

# 为了防止导入错误，这里提供一个空的 db 对象
class _EmptyDB:
    """空的 db 对象，用于向后兼容"""
    pass

db = _EmptyDB()