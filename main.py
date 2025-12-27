"""Spectra 主程序入口"""

import os
import sys
import time
from pathlib import Path

# 初始化日志系统（在其他导入之前）
from managers.log_manager import LogManager
log_manager = LogManager(log_dir="logs", level="INFO")
logger = log_manager.get_logger(__name__)

# 记录开始时间
_start_time = time.time()

# 禁用 FFmpeg 日志输出
# 注释掉以允许日志输出到控制台
# if sys.platform == 'win32':
#     import ctypes
#     kernel32 = ctypes.windll.kernel32
#     kernel32.SetStdHandle(-12, None)

os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"
os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "hwaccel;none"

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication
from splash_screen import SplashScreen
from window import Window


def show_main_window(window, splash):
    """关闭启动画面并显示主窗口"""
    splash.close()
    window.show()
    window.raise_()
    window.activateWindow()

    # 计算从启动到主窗口显示的总耗时
    total_startup_elapsed = (time.time() - _start_time) * 1000
    logger.info(f"主窗口显示完成 - 启动总耗时: {total_startup_elapsed:.2f}ms")


if __name__ == "__main__":
    logger.info("Spectra starting...")

    # 禁用 Qt 的高 DPI 自动缩放，使屏幕显示的物理像素与配置一致，但需要手动处理控件的 DPI 缩放
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    qapp_start_time = time.time()
    app = QApplication(sys.argv)
    qapp_elapsed = (time.time() - qapp_start_time) * 1000
    logger.info(f"QApplication created - 耗时: {qapp_elapsed:.2f}ms")

    # 创建并显示启动画面
    splash_start_time = time.time()
    splash = SplashScreen()
    splash.show()
    splash_elapsed = (time.time() - splash_start_time) * 1000
    logger.info(f"Splash screen shown - 耗时: {splash_elapsed:.2f}ms")

    # 强制启动画面完成渲染
    QApplication.processEvents()

    # 创建主窗口但不显示
    window_start_time = time.time()
    window = Window()
    window_elapsed = (time.time() - window_start_time) * 1000
    logger.info(f"Main window created - 耗时: {window_elapsed:.2f}ms")

    # 总初始化耗时
    total_elapsed = (time.time() - _start_time) * 1000
    logger.info(f"初始化完成 - 总耗时: {total_elapsed:.2f}ms")

    # 2秒后关闭启动画面并显示主窗口
    QTimer.singleShot(0, lambda: show_main_window(window, splash))

    logger.info("Starting Qt event loop...")
    sys.exit(app.exec())
