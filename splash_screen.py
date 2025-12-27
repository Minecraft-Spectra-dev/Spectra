"""启动画面"""

import os

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

        # 显示icon
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if os.path.exists("icon.png"):
            icon_label = QLabel()
            icon_pixmap = QPixmap("icon.png")
            icon_label.setPixmap(icon_pixmap.scaled(179, 179, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(icon_label)
