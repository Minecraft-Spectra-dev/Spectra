"""Modrinth 搜索结果卡片组件"""

import urllib.request
from PyQt6.QtCore import Qt, QUrl, QThread, pyqtSignal, QByteArray
from PyQt6.QtGui import QFont, QDesktopServices, QPixmap, QIcon
from PyQt6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget, QFrame)
from utils import load_svg_icon, scale_icon_for_display


class IconLoaderThread(QThread):
    """图标加载线程"""
    icon_loaded = pyqtSignal(object)  # 使用 object 代替 QPixmap
    
    def __init__(self, icon_url, size):
        super().__init__()
        self.icon_url = icon_url
        self.size = size
    
    def run(self):
        try:
            req = urllib.request.Request(self.icon_url)
            req.add_header('User-Agent', 'Spectra/1.0 (spectra@modrinth)')
            
            with urllib.request.urlopen(req, timeout=5) as response:
                data = response.read()
                # 传递原始数据而不是 QPixmap，因为 QPixmap 跨线程传递不安全
                self.icon_loaded.emit(data)
        except Exception:
            self.icon_loaded.emit(None)


class ModrinthResultCard(QWidget):
    """Modrinth 搜索结果卡片"""
    
    def __init__(self, project_data, dpi_scale=1.0, parent=None, on_download=None):
        super().__init__(parent)
        self.project_data = project_data
        self.dpi_scale = dpi_scale
        self.on_download = on_download
        
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
        self.title_label = QLabel(project_data.get('title', 'Unknown'))
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
        
        # 下载按钮
        download_btn = QPushButton("Download")
        download_btn.setFixedSize(int(80 * dpi_scale), int(32 * dpi_scale))
        download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        download_btn.setStyleSheet("""
            QPushButton {
                background: rgba(76, 175, 80, 0.8);
                border: none;
                border-radius: 4px;
                color: white;
                font-size: 10px;
                font-family: 'Microsoft YaHei UI';
            }
            QPushButton:hover {
                background: rgba(76, 175, 80, 1);
            }
            QPushButton:pressed {
                background: rgba(76, 175, 80, 0.6);
            }
        """)
        if on_download:
            # 使用 lambda 并接受 checked 参数
            download_btn.clicked.connect(lambda checked=False: on_download(project_data))
        card_layout.addWidget(download_btn, 0, Qt.AlignmentFlag.AlignTop)
        
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
        if not hasattr(self, '_icon_loader'):
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
    
    def _format_number(self, num):
        """格式化数字（如：1.2k, 1.5M）"""
        if num >= 1000000:
            return f"{num / 1000000:.1f}M"
        elif num >= 1000:
            return f"{num / 1000:.1f}k"
        return str(num)
    
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
