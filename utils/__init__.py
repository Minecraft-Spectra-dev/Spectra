"""工具函数模块"""

from .icons import load_svg_icon, scale_icon_for_display
from .path_helper import get_resource_path

__all__ = ['load_svg_icon', 'scale_icon_for_display', 'get_resource_path']


def normalize_path(path):
    """规范化路径，统一使用反斜杠（Windows 风格）"""
    if not path:
        return path
    return str(path).replace("/", "\\")
