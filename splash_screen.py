"""启动画面"""

import os
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QApplication, QWidget, QHBoxLayout, QLabel


class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(179, 179)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool  # 避免在任务栏中显示
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowModality(Qt.WindowModality.ApplicationModal)

        # 居中显示
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2
        self.move(x, y)

        # 获取 icon.png 的正确路径
        # 优先从当前工作目录读取（打包后 exe 同级目录），其次从 _MEIPASS 读取
        icon_path = None
        # 尝试从当前工作目录读取
        cwd_icon = os.path.join(os.getcwd(), 'icon.png')
        if os.path.exists(cwd_icon):
            icon_path = cwd_icon
        # 打包后环境，尝试从 _internal 目录读取
        elif hasattr(sys, '_MEIPASS'):
            temp_icon = os.path.join(sys._MEIPASS, 'icon.png')
            if os.path.exists(temp_icon):
                icon_path = temp_icon
        # 开发环境，从项目根目录读取
        else:
            project_root = os.path.dirname(os.path.abspath(__file__))
            root_icon = os.path.join(project_root, 'icon.png')
            if os.path.exists(root_icon):
                icon_path = root_icon

        # 显示icon
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if icon_path and os.path.exists(icon_path):
            icon_label = QLabel()
            icon_pixmap = QPixmap(icon_path)
            icon_label.setPixmap(icon_pixmap.scaled(179, 179, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
