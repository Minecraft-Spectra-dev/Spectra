"""图标工具函数"""

import os
import sys
from PyQt6.QtGui import QPixmap, QColor, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication


def _get_device_pixel_ratio():
    """获取当前设备像素比"""
    screen = QApplication.primaryScreen()
    if screen:
        return screen.devicePixelRatio()
    return 1.0


def load_svg_icon(path, dpi_scale=1.0):
    # 获取 SVG 文件的正确路径
    if hasattr(sys, '_MEIPASS'):
        # 打包后环境，优先从 _internal 读取
        svg_path = os.path.join(sys._MEIPASS, path.replace('\\', os.sep))
        if not os.path.exists(svg_path):
            # 如果 _internal 中不存在，尝试从当前工作目录读取
            svg_path = os.path.join(os.getcwd(), path.replace('\\', os.sep))
    else:
        # 开发环境
        svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", path.replace('\\', os.sep))
        svg_path = os.path.abspath(svg_path)
    if os.path.exists(svg_path):
        icon = QIcon(svg_path)
        if not icon.isNull():
            base_size = 32
            pixmap = icon.pixmap(base_size, base_size)
            if not pixmap.isNull():
                image = pixmap.toImage()
                for y in range(image.height()):
                    for x in range(image.width()):
                        color = image.pixelColor(x, y)
                        if color.alpha() > 0:
                            image.setPixelColor(x, y, QColor(255, 255, 255, color.alpha()))
                result = QPixmap.fromImage(image)
                return result
    return None


def scale_icon_for_display(pixmap, size, dpi_scale=1.0):
    if pixmap.isNull():
        return pixmap
    target_size = int(size * dpi_scale)
    return pixmap.scaled(
        target_size, target_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
