"""图标工具函数"""

import os
from PyQt6.QtGui import QPixmap, QColor, QImage, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtWidgets import QApplication


def _get_device_pixel_ratio():
    """获取当前设备像素比"""
    screen = QApplication.primaryScreen()
    if screen:
        return screen.devicePixelRatio()
    return 1.0


def load_svg_icon(path, dpi_scale=1.0):
    """加载SVG图标为QPixmap，并渲染为白色

    Args:
        path: SVG文件路径
        dpi_scale: DPI缩放比例（默认1.0，保留用于兼容，但不再使用）
    """
    svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", path.replace('\\', os.sep))
    svg_path = os.path.abspath(svg_path)
    if os.path.exists(svg_path):
        # 直接使用 QIcon 加载 SVG，它原生支持矢量缩放
        icon = QIcon(svg_path)
        if not icon.isNull():
            # 使用固定尺寸渲染（32x32），让后续的 scale_icon_for_display 来缩放
            base_size = 32
            pixmap = icon.pixmap(base_size, base_size)
            if not pixmap.isNull():
                # 将 pixmap 转换为 QImage
                image = pixmap.toImage()
                # 遍历每个像素，将非透明像素设置为白色
                for y in range(image.height()):
                    for x in range(image.width()):
                        color = image.pixelColor(x, y)
                        if color.alpha() > 0:
                            image.setPixelColor(x, y, QColor(255, 255, 255, color.alpha()))
                result = QPixmap.fromImage(image)
                return result
    return None


def scale_icon_for_display(pixmap, size, dpi_scale=1.0):
    """为显示缩放图标，正确处理高DPI

    Args:
        pixmap: 原始 pixmap（32x32）
        size: 逻辑像素尺寸（如 20）
        dpi_scale: DPI缩放比例（默认1.0）

    Returns:
        适合显示的 pixmap
    """
    if pixmap.isNull():
        return pixmap
    # 目标尺寸 = 逻辑像素尺寸 * DPI缩放比例
    target_size = int(size * dpi_scale)
    return pixmap.scaled(
        target_size, target_size,
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation
    )
