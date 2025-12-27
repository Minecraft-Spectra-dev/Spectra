"""Spectra 主程序入口"""

import os
import sys
from pathlib import Path

# 初始化日志系统（在其他导入之前）
from managers.log_manager import LogManager
log_manager = LogManager(log_dir="logs", level="INFO")
logger = log_manager.get_logger(__name__)

# 禁用 FFmpeg 日志输出
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetStdHandle(-12, None)

os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "hwaccel;none"

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from splash_screen import SplashScreen
from window import Window


if __name__ == "__main__":
    logger.info("Spectra starting...")
    
    # 禁用 Qt 的高 DPI 自动缩放，使屏幕显示的物理像素与配置一致，但需要手动处理控件的 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    logger.info("QApplication created")

    # 创建并显示启动画面
    splash = SplashScreen()
    splash.show()
    logger.info("Splash screen shown")

    # 创建主窗口但不显示
    window = Window()
    logger.info("Main window created")

    # 2秒后关闭启动画面并显示主窗口
    def show_main_window():
        splash.close()
        window.show()
        window.raise_()
        window.activateWindow()
        logger.info("Main window shown")

    QTimer.singleShot(2000, show_main_window)

    logger.info("Starting Qt event loop...")
    sys.exit(app.exec())
