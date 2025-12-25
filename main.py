"""Spectra 主程序入口"""

import os
import sys

# 禁用 FFmpeg 日志输出
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetStdHandle(-12, None)

os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "hwaccel;none"

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, Qt
from splash_screen import SplashScreen
from window import Window


if __name__ == "__main__":
    # 禁用 Qt 的高 DPI 自动缩放，使屏幕显示的物理像素与配置一致
    # 但需要手动处理控件的 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)

    # 创建并显示启动画面
    splash = SplashScreen()
    splash.show()

    # 创建主窗口但不显示
    window = Window()

    # 2秒后关闭启动画面并显示主窗口
    def show_main_window():
        splash.close()
        window.show()
        window.raise_()
        window.activateWindow()

    QTimer.singleShot(2000, show_main_window)

    sys.exit(app.exec())
