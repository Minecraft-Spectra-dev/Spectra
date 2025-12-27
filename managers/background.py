"""背景管理器"""

import os
import logging

from PyQt6.QtCore import QUrl, QSizeF, Qt

logger = logging.getLogger(__name__)
from PyQt6.QtGui import QPixmap
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer
from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem
from PyQt6.QtWidgets import QGraphicsScene, QGraphicsView, QLabel


class BackgroundManager:
    def __init__(self, parent_widget):
        self.parent = parent_widget
        self.current_bg_path = None
        self.current_video_path = None
        self.bg_label_widget = None
        self.solid_bg_widget = None
        self.current_pixmap = None  # 缓存当前加载的图片
        logger.debug("背景管理器初始化完成")

        # 初始化视频组件
        self.video_scene = QGraphicsScene()
        self.video_view = QGraphicsView(self.video_scene, parent_widget)
        self.video_view.setStyleSheet("border:none;background:black;")
        self.video_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setFrameShape(QGraphicsView.Shape.NoFrame)
        # 设置不响应鼠标事件，让鼠标事件穿透到下层控件
        self.video_view.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.video_view.hide()

        self.video_item = QGraphicsVideoItem()
        self.video_scene.addItem(self.video_item)

        self.player = QMediaPlayer(parent_widget)
        self.player.setVideoOutput(self.video_item)
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

    def set_background_image(self, path):
        if not os.path.exists(path):
            return

        # 隐藏纯色背景
        if self.solid_bg_widget:
            self.solid_bg_widget.hide()

        ext = os.path.splitext(path)[1].lower()

        # 视频格式
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
            # 隐藏图片背景标签
            if self.bg_label_widget:
                self.bg_label_widget.hide()

            w, h = self.parent.width(), self.parent.height()

            # 只在首次加载或路径改变时重新加载视频
            if self.current_video_path != path:
                self.player.setSource(QUrl.fromLocalFile(path))
                self.current_video_path = path

            # 确保视频在播放状态（修复切换背景后黑屏问题）
            if self.player.playbackState() != QMediaPlayer.PlaybackState.PlayingState:
                self.player.play()

            # 使用固定 16:9 比例计算
            video_w, video_h = 1920, 1080
            scale = max(w / video_w, h / video_h)
            scaled_w, scaled_h = video_w * scale, video_h * scale

            self.video_view.setGeometry(0, 0, w, h)
            self.video_scene.setSceneRect(0, 0, w, h)
            self.video_item.setSize(QSizeF(scaled_w, scaled_h))
            self.video_item.setPos((w - scaled_w) / 2, (h - scaled_h) / 2)
            self.video_view.lower()
            self.video_view.show()

            self.current_bg_path = path

        else:
            # 停止并隐藏视频
            self.player.stop()
            self.video_view.hide()
            self.current_video_path = None

            # 创建或显示图片背景标签
            if not self.bg_label_widget:
                from PyQt6.QtWidgets import QWidget
                self.bg_label_widget = QLabel(self.parent)
                # 设置不响应鼠标事件，让鼠标事件穿透到下层控件
                self.bg_label_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
                # 立即将图片背景标签放到所有其他控件下方
                for child in self.parent.children():
                    if isinstance(child, QWidget) and child != self.bg_label_widget:
                        self.bg_label_widget.stackUnder(child)
                self.bg_label_widget.lower()

            pixmap = QPixmap(path)
            w, h = self.parent.width(), self.parent.height()

            img_w, img_h = pixmap.width(), pixmap.height()
            scale = max(w / img_w, h / img_h)
            scaled_w, scaled_h = int(img_w * scale), int(img_h * scale)

            scaled_pixmap = pixmap.scaled(scaled_w, scaled_h, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                          Qt.TransformationMode.SmoothTransformation)

            x = (scaled_w - w) // 2
            y = (scaled_h - h) // 2
            cropped = scaled_pixmap.copy(x, y, w, h)

            # 缓存原始图片
            self.current_pixmap = cropped
            self.bg_label_widget.setPixmap(cropped)
            self.bg_label_widget.setGeometry(0, 0, w, h)
            self.bg_label_widget.show()
            self.current_bg_path = path

    def set_solid_color(self, color, opacity=None):
        """设置纯色背景，支持 RGB 格式和透明度控制"""
        from PyQt6.QtGui import QColor

        # 隐藏图片背景和视频
        if self.bg_label_widget:
            self.bg_label_widget.hide()
        self.player.stop()
        self.video_view.hide()

        if not self.solid_bg_widget:
            from PyQt6.QtWidgets import QWidget
            self.solid_bg_widget = QLabel(self.parent)
            # 设置不响应鼠标事件，让鼠标事件穿透到下层控件
            self.solid_bg_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
            # 立即将纯色背景放到所有其他控件下方
            for child in self.parent.children():
                if isinstance(child, QWidget) and child != self.solid_bg_widget:
                    self.solid_bg_widget.stackUnder(child)
            self.solid_bg_widget.lower()

        # 解析颜色（仅使用 RGB 部分）
        qcolor = QColor(color)

        # 计算灰度值（使用人眼感知的加权公式）
        r, g, b, _ = qcolor.getRgb()
        luminance = 0.299 * r + 0.587 * g + 0.114 * b

        # 如果明度超过90，进行缩放
        if luminance > 90:
            scale_factor = 90 / luminance
            qcolor.setRgb(int(r * scale_factor), int(g * scale_factor), int(b * scale_factor), 255)

        # 如果提供了不透明度，则使用该值
        if opacity is not None:
            alpha = int(opacity)
            qcolor.setAlpha(alpha)
        else:
            # 保留原有的 alpha 值
            qcolor.setAlpha(255)

        w, h = self.parent.width(), self.parent.height()
        self.solid_bg_widget.setStyleSheet(f"background:{qcolor.name(QColor.NameFormat.HexArgb)};")
        self.solid_bg_widget.setGeometry(0, 0, w, h)
        self.solid_bg_widget.show()

    def _update_bg_fill_geometry(self, w, h):
        """更新背景填充层的几何位置（保留以兼容）"""
        pass

    def _ensure_widgets_at_bottom(self):
        """确保所有背景控件在所有控件的最底层"""
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtCore import QTimer

        # 使用定时器延迟执行，确保所有布局都完成
        QTimer.singleShot(0, self._do_ensure_widgets_at_bottom)

    def _do_ensure_widgets_at_bottom(self):
        """实际执行确保背景控件在最底层的操作"""
        from PyQt6.QtWidgets import QWidget

        # 收集所有需要放到底层的背景控件
        bg_widgets = []
        if self.bg_label_widget:
            bg_widgets.append(self.bg_label_widget)
        if self.solid_bg_widget:
            bg_widgets.append(self.solid_bg_widget)
        if self.video_view:
            bg_widgets.append(self.video_view)

        # 将所有背景控件放到最底层
        for bg_widget in bg_widgets:
            bg_widget.lower()

        # 将父控件的主布局中的控件提升到上方
        # 主窗口使用 QHBoxLayout，包含 sidebar 和 right_panel
        if hasattr(self.parent, 'sidebar'):
            self.parent.sidebar.raise_()
        if hasattr(self.parent, 'right_panel'):
            self.parent.right_panel.raise_()

    def hide(self):
        if self.bg_label_widget:
            self.bg_label_widget.hide()
        if self.solid_bg_widget:
            self.solid_bg_widget.hide()
        self.player.stop()
        self.video_view.hide()
