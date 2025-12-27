"""路径辅助工具"""

import os
import sys


def get_resource_path(relative_path):
    """获取资源文件的绝对路径（支持开发环境和打包后环境）
    
    在开发环境中，返回项目根目录的相对路径
    在打包后环境中，返回 _MEIPASS 临时目录的相对路径
    对于 config.json 和 lang/ 目录，始终从当前工作目录读取
    
    Args:
        relative_path: 相对路径
        
    Returns:
        str: 资源文件的绝对路径
    """
    # 对于配置文件和语言文件，始终从当前工作目录读取（不从 _MEIPASS 读取）
    if relative_path == "config.json" or relative_path.startswith("lang"):
        base_path = os.getcwd()
    elif hasattr(sys, '_MEIPASS'):
        # 打包后的环境，资源文件在临时目录
        base_path = sys._MEIPASS
    else:
        # 开发环境，使用脚本所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 回退到项目根目录
        base_path = os.path.dirname(base_path)
    
    return os.path.join(base_path, relative_path)
