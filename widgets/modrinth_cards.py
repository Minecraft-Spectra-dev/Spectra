"""Modrinth 搜索结果卡片组件"""

import os
import hashlib
import logging
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QByteArray
from PyQt6.QtGui import QFont, QDesktopServices, QPixmap, QIcon
from PyQt6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget, QFrame)
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QNetworkReply
from utils import load_svg_icon, scale_icon_for_display, normalize_path

logger = logging.getLogger(__name__)


class IconLoaderThread(QThread):
    """图标加载线程"""
    icon_loaded = pyqtSignal(object)  # 使用 object 代替 QPixmap

    def __init__(self, icon_url, size):
        super().__init__()
        self.icon_url = icon_url
        self.size = size

    def run(self):
        try:
            manager = QNetworkAccessManager()
            request = QNetworkRequest(QUrl(self.icon_url))
            request.setRawHeader(b'User-Agent', b'Spectra/1.0 (spectra@modrinth)')

            reply = manager.get(request)

            # 等待请求完成（注意：这仍然会阻塞，但在独立线程中）
            from PyQt6.QtCore import QEventLoop
            loop = QEventLoop()
            reply.finished.connect(loop.quit)
            loop.exec()

            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data()
                self.icon_loaded.emit(data)
            else:
                self.icon_loaded.emit(None)

            reply.deleteLater()
        except Exception:
            self.icon_loaded.emit(None)


class HashCheckThread(QThread):
    """哈希检查线程（异步计算文件哈希）"""
    status_found = pyqtSignal(bool)  # 是否找到匹配的文件
    finished = pyqtSignal()  # 线程完成信号

    # 类级别的信号量，限制并发网络请求数量
    _max_concurrent_requests = 3  # 最多同时进行3个网络请求
    _running_threads = 0
    _thread_lock = None  # 线程锁

    def __init__(self, project_id, target_path):
        super().__init__()
        self.project_id = project_id
        self.target_path = target_path
        self.should_run = True

        # 初始化线程锁（只初始化一次）
        if HashCheckThread._thread_lock is None:
            from threading import Lock
            HashCheckThread._thread_lock = Lock()

    def stop(self):
        """停止线程"""
        self.should_run = False

    def run(self):
        """在后台线程中计算哈希并检查"""
        try:
            # 检查是否已停止
            if not self.should_run:
                self.finished.emit()
                return

            # 等待直到有可用的网络请求槽位（使用更安全的方式）
            import time
            waited_count = 0
            while True:
                with HashCheckThread._thread_lock:
                    if HashCheckThread._running_threads < HashCheckThread._max_concurrent_requests:
                        HashCheckThread._running_threads += 1
                        break

                if not self.should_run:
                    self.finished.emit()
                    return

                time.sleep(0.05)  # 等待50ms
                waited_count += 1
                if waited_count > 200:  # 超过10秒就强制执行
                    logger.warning("Timeout waiting for network slot, proceeding anyway")
                    with HashCheckThread._thread_lock:
                        HashCheckThread._running_threads += 1
                    break

            # 使用同步管理器获取文件哈希（在后台线程中执行，不会阻塞UI）
            from managers.modrinth_manager import ModrinthManager
            manager = ModrinthManager()

            logger.debug(f"Requesting file hashes for project {self.project_id}")
            project_hashes = manager.get_project_file_hashes(self.project_id)

            if not self.should_run:
                self.finished.emit()
                return

            if not project_hashes:
                logger.debug(f"No file hashes found for project {self.project_id}")
                self.finished.emit()
                return

            # 提取所有 SHA1 哈希值
            sha1_hashes = [h.get('sha1') for h in project_hashes if h.get('sha1')]
            if not sha1_hashes:
                logger.debug(f"No SHA1 hashes found for project {self.project_id}")
                self.finished.emit()
                return

            # 检查目标路径是否存在
            if not os.path.exists(self.target_path):
                logger.warning(f"Target path does not exist: {normalize_path(self.target_path)}")
                self.finished.emit()
                return

            logger.debug(f"Checking {len(os.listdir(self.target_path))} files in {normalize_path(self.target_path)}")

            # 遍历本地文件并计算哈希
            zip_files = []
            for filename in os.listdir(self.target_path):
                if not self.should_run:
                    self.finished.emit()
                    return

                filepath = os.path.join(self.target_path, filename)

                # 跳过目录
                if not os.path.isfile(filepath):
                    continue

                # 只检查 .zip 文件（排除 .mrpack）
                if not filename.lower().endswith('.zip'):
                    continue

                zip_files.append(filename)

                try:
                    # 计算本地文件的 SHA1 哈希
                    with open(filepath, 'rb') as f:
                        sha1_hash = hashlib.sha1(f.read()).hexdigest()

                    # 与项目的哈希列表比较
                    if sha1_hash in sha1_hashes:
                        logger.info(f"Found downloaded resource pack {filename} (matched by SHA1: {sha1_hash[:16]}...)")
                        self.status_found.emit(True)
                        self.finished.emit()
                        return
                except Exception as e:
                    logger.warning(f"Failed to calculate hash for {filename}: {e}")
                    continue

            logger.debug(f"Checked {len(zip_files)} .zip files, no match found")

            # 没有找到匹配的文件
            if self.should_run:
                self.status_found.emit(False)

        except Exception as e:
            logger.error(f"Failed to check downloaded status: {e}")
            import traceback
            logger.error(traceback.format_exc())
            if self.should_run:
                self.status_found.emit(False)
        finally:
            # 使用锁来释放槽位
            with HashCheckThread._thread_lock:
                HashCheckThread._running_threads = max(0, HashCheckThread._running_threads - 1)
            self.finished.emit()

    def stop(self):
        """停止线程（非阻塞）"""
        self.should_run = False


class ModrinthResultCard(QWidget):
    """Modrinth 搜索结果卡片"""

    def __init__(self, project_data, dpi_scale=1.0, parent=None, on_download=None, download_target_path=None, language_manager=None, text_renderer=None):
        super().__init__(parent)
        self.project_data = project_data
        self.dpi_scale = dpi_scale
        self.on_download = on_download
        self.download_target_path = download_target_path
        self.is_downloaded = False
        self.is_downloading = False
        self.download_btn = None
        self.status_label = None
        self.hash_check_thread = None
        self.language_manager = language_manager
        self.text_renderer = text_renderer
        self.download_progress = 0

        self.setFixedHeight(int(90 * dpi_scale))
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # 卡片容器
        card_layout = QHBoxLayout(self)
        card_layout.setContentsMargins(int(12 * dpi_scale), int(8 * dpi_scale), int(12 * dpi_scale), int(8 * dpi_scale))
        card_layout.setSpacing(int(12 * dpi_scale))

        # 图标/封面
        icon_container = QWidget()
        icon_container.setFixedSize(int(64 * dpi_scale), int(64 * dpi_scale))
        icon_layout = QVBoxLayout(icon_container)
        icon_layout.setContentsMargins(0, 0, 0, 0)

        self.icon_label = QLabel()
        self.icon_label.setFixedSize(int(64 * dpi_scale), int(64 * dpi_scale))
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 先显示默认图标，立即显示卡片
        self._load_default_icon()
        icon_layout.addWidget(self.icon_label)

        # 延迟异步加载真实图标，不阻塞卡片创建
        icon_url = project_data.get('icon_url', '')
        if icon_url:
            # 保存到实例变量，延迟加载
            self._pending_icon_url = icon_url
            # 立即启动线程加载图标，使用 QThread 而不是 QTimer
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._start_load_icon)

        card_layout.addWidget(icon_container, 0, Qt.AlignmentFlag.AlignTop)

        # 信息区域
        info_layout = QVBoxLayout()
        info_layout.setSpacing(int(4 * dpi_scale))
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # 标题
        title_text = project_data.get('title', '')
        if self.language_manager:
            title_text = title_text or self.language_manager.translate("download_unknown_title")
        else:
            title_text = title_text or "Unknown"
        self.title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setFamily("Microsoft YaHei UI")
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setPointSize(int(12 * dpi_scale))
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: white; background: transparent;")
        self.title_label.setWordWrap(True)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(self.title_label)

        # 描述
        description = project_data.get('description', '')
        if len(description) > 80:
            description = description[:80] + '...'
        self.description_label = QLabel(description)
        desc_font = QFont()
        desc_font.setFamily("Microsoft YaHei UI")
        desc_font.setPointSize(int(9 * dpi_scale))
        self.description_label.setFont(desc_font)
        self.description_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); background: transparent;")
        self.description_label.setWordWrap(True)
        self.description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(self.description_label)

        # 统计信息（下载量、关注数等）
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(0)  # 移除间距
        stats_layout.setContentsMargins(0, 0, 0, 0)

        downloads = project_data.get('downloads', 0)
        follows = project_data.get('follows', 0)

        # 定义字体
        stats_font = QFont()
        stats_font.setFamily("Microsoft YaHei UI")
        stats_font.setPointSize(int(8 * self.dpi_scale))

        # 使用图标显示下载量和喜欢数
        stats_layout.setSpacing(int(8 * self.dpi_scale))

        # 下载量图标和标签
        download_pixmap = load_svg_icon("svg/download.svg", self.dpi_scale)
        if download_pixmap:
            download_icon = QLabel()
            download_icon.setFixedSize(int(12 * self.dpi_scale), int(12 * self.dpi_scale))
            download_icon.setPixmap(scale_icon_for_display(download_pixmap, 12, self.dpi_scale))
            stats_layout.addWidget(download_icon)
        else:
            stats_text = QLabel("↓")
            stats_text.setFont(stats_font)
            stats_text.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
            stats_layout.addWidget(stats_text)

        downloads_label = QLabel(self._format_number(downloads))
        downloads_label.setFont(stats_font)
        downloads_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
        stats_layout.addWidget(downloads_label)

        # 关注数图标和标签
        star_pixmap = load_svg_icon("svg/star.svg", self.dpi_scale)
        if star_pixmap:
            star_icon = QLabel()
            star_icon.setFixedSize(int(12 * self.dpi_scale), int(12 * self.dpi_scale))
            star_icon.setPixmap(scale_icon_for_display(star_pixmap, 12, self.dpi_scale))
            stats_layout.addWidget(star_icon)
        else:
            stats_text2 = QLabel("♥")
            stats_text2.setFont(stats_font)
            stats_text2.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
            stats_layout.addWidget(stats_text2)

        follows_label = QLabel(self._format_number(follows))
        follows_label.setFont(stats_font)
        follows_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
        stats_layout.addWidget(follows_label)

        info_layout.addLayout(stats_layout, 0)
        card_layout.addLayout(info_layout, 1)

        # 下载按钮（也作为进度条显示）
        download_btn_text = "Download"
        if self.language_manager:
            download_btn_text = self.language_manager.translate("download_btn")
        download_btn = QPushButton(download_btn_text)
        download_btn.setFixedSize(int(80 * dpi_scale), int(32 * dpi_scale))
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.3);
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 10px;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.2);
                color: rgba(255, 255, 255, 0.5);
            }
        """)
        if on_download:
            # 使用 lambda 并接受 checked 参数
            download_btn.clicked.connect(lambda checked=False: on_download(project_data))

        self.download_btn = download_btn
        card_layout.addWidget(download_btn, 0, Qt.AlignmentFlag.AlignTop)

        # 检查是否已下载（延迟启动，避免阻塞UI）
        if self.download_target_path:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(100, self._start_hash_check)

        # 卡片样式
        self._update_card_style()

        # 不使用透明度效果，避免窗口闪烁
        # self.opacity_effect = QGraphicsOpacityEffect(self)
        # self.opacity_effect.setOpacity(0.9)
        # self.setGraphicsEffect(self.opacity_effect)
    
    def _start_load_icon(self):
        """开始加载图标（由 QTimer 调用）"""
        if hasattr(self, '_pending_icon_url') and self._pending_icon_url:
            self._load_icon_async(self._pending_icon_url)
            delattr(self, '_pending_icon_url')
    
    def _load_icon_async(self, icon_url):
        """异步加载项目图标（使用 QThread）"""
        # 保存线程引用，防止被垃圾回收
        if not hasattr(self, '_icon_loader') or self._icon_loader is None:
            self._icon_loader = None
        self._icon_loader = IconLoaderThread(icon_url, 0)
        # 使用 QueuedConnection 确保在主线程执行
        self._icon_loader.icon_loaded.connect(self._on_icon_loaded, Qt.ConnectionType.QueuedConnection)
        # 设置线程完成后自动删除
        self._icon_loader.finished.connect(self._icon_loader.deleteLater)
        self._icon_loader.start()
    
    def _on_icon_loaded(self, data):
        """图标加载完成回调"""
        if data:
            pixmap = QPixmap()
            pixmap.loadFromData(QByteArray(data))
            
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    int(64 * self.dpi_scale), int(64 * self.dpi_scale),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_label.setPixmap(scaled_pixmap)
    
    def _load_default_icon(self):
        """加载默认图标"""
        try:
            pixmap = load_svg_icon("svg/cube.svg", self.dpi_scale)
            if pixmap:
                scaled_pixmap = pixmap.scaled(
                    int(48 * self.dpi_scale), int(48 * self.dpi_scale),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_label.setPixmap(scaled_pixmap)
        except Exception:
            pass
    
    def _start_hash_check(self):
        """启动哈希检查（异步）"""
        project_id = self.project_data.get('project_id', '')
        if not project_id or not self.download_target_path:
            return

        # 停止之前的哈希检查线程（断开信号连接以避免重复触发）
        old_thread = self.hash_check_thread
        if old_thread and old_thread.isRunning():
            # 设置标志位，让线程自然退出
            old_thread.should_run = False

        # 立即创建新的哈希检查线程（不等待旧线程完成）
        try:
            self.hash_check_thread = HashCheckThread(project_id, self.download_target_path)
            self.hash_check_thread.status_found.connect(self._on_hash_check_result, Qt.ConnectionType.QueuedConnection)
            self.hash_check_thread.finished.connect(self._on_hash_check_finished)
            self.hash_check_thread.start()
        except Exception as e:
            logger.error(f"Failed to start hash check thread: {e}")
            # 恢复旧线程引用
            self.hash_check_thread = old_thread
    
    def _on_hash_check_result(self, is_downloaded):
        """哈希检查完成回调"""
        # 只有当前状态不是"下载中"时才更新
        if not self.is_downloading:
            self._set_downloaded_status(is_downloaded)
    
    def _on_hash_check_finished(self):
        """哈希检查线程完成"""
        sender = self.sender()
        # 只处理来自当前线程的信号
        if sender and sender == self.hash_check_thread:
            self.hash_check_thread.deleteLater()
            self.hash_check_thread = None
    
    def _format_number(self, num):
        """格式化数字（如：1.2k, 1.5M）"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}k"
        return str(num)

    def _set_downloaded_status(self, is_downloaded):
        """设置下载状态"""
        self.is_downloaded = is_downloaded
        if self.download_btn:
            if is_downloaded:
                downloaded_text = "已下载"
                if self.language_manager:
                    downloaded_text = self.language_manager.translate("download_btn_downloaded")
                self.download_btn.setText(downloaded_text)
                self.download_btn.setEnabled(False)
                self.download_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.2);
                        border: none;
                        border-radius: 4px;
                        color: rgba(255, 255, 255, 0.5);
                        font-size: 10px;
                        font-family: 'Microsoft YaHei UI';
                    }
                """)
                self.is_downloading = False  # 下载完成，清除下载中状态
            else:
                download_text = "Download"
                if self.language_manager:
                    download_text = self.language_manager.translate("download_btn")
                self.download_btn.setText(download_text)
                self.download_btn.setEnabled(True)
                self.download_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(255, 255, 255, 0.3);
                        border: none;
                        border-radius: 4px;
                        color: white;
                        font-size: 10px;
                        font-family: 'Microsoft YaHei UI';
                    }
                    QPushButton:hover {
                        background: rgba(255, 255, 255, 0.5);
                    }
                    QPushButton:pressed {
                        background: rgba(255, 255, 255, 0.2);
                    }
                    QPushButton:disabled {
                        background: rgba(255, 255, 255, 0.2);
                        color: rgba(255, 255, 255, 0.5);
                    }
                """)
    
    def set_downloading_status(self, is_downloading):
        """设置下载中状态"""
        self.is_downloading = is_downloading
        self.download_progress = 0  # 重置进度
        if self.download_btn:
            if is_downloading:
                self.download_btn.setText("0%")
                self.download_btn.setEnabled(False)
                self.download_btn.setStyleSheet("""
                    QPushButton {
                        background: rgba(102, 132, 255, 0.4);
                        border: none;
                        border-radius: 4px;
                        color: white;
                        font-size: 10px;
                        font-family: 'Microsoft YaHei UI';
                    }
                """)
            else:
                # 如果不在下载中，恢复到未下载状态
                self._set_downloaded_status(self.is_downloaded)

    def update_download_progress(self, progress):
        """更新下载进度
        Args:
            progress: 进度值 (0-100)
        """
        if self.download_btn and self.is_downloading:
            self.download_progress = progress
            # 根据进度计算背景颜色（从浅蓝到深蓝）
            # 基础颜色: rgba(102, 132, 255, 0.4)
            # 渐变到: rgba(102, 132, 255, 0.9)
            opacity = 0.4 + (progress / 100) * 0.5
            bg_color = f"rgba(102, 132, 255, {opacity:.2f})"
            
            self.download_btn.setText(f"{progress}%")
            self.download_btn.setStyleSheet(f"""
                QPushButton {{
                    background: {bg_color};
                    border: none;
                    border-radius: 4px;
                    color: white;
                    font-size: 10px;
                    font-family: 'Microsoft YaHei UI';
                }}
            """)

    def refresh_download_status(self, new_target_path=None, skip_if_downloading=False):
        """刷新下载状态（用于切换版本时调用）"""
        # 如果正在下载，跳过刷新以避免状态混乱
        if skip_if_downloading and self.is_downloading:
            return

        if new_target_path is not None:
            self.download_target_path = new_target_path

        # 重置状态
        self._set_downloaded_status(False)

        # 重新启动哈希检查
        if self.download_target_path:
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(50, self._start_hash_check)

    def _update_card_style(self):
        """更新卡片样式"""
        self.setStyleSheet(f"""
            ModrinthResultCard {{
                background: rgba(0, 0, 0, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(8 * self.dpi_scale)}px;
            }}
            ModrinthResultCard:hover {{
                background: rgba(0, 0, 0, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        super().leaveEvent(event)
    
    def cleanup(self):
        """清理资源"""
        # 停止哈希检查线程
        if self.hash_check_thread and self.hash_check_thread.isRunning():
            self.hash_check_thread.stop()
            self.hash_check_thread.deleteLater()
            self.hash_check_thread = None
