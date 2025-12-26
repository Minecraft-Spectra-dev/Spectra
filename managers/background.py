"""背景管理器"""

import os

from PyQt6.QtCore import QUrl, QSizeF, Qt
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

        # 初始化视频组件
        self.video_scene = QGraphicsScene()
        self.video_view = QGraphicsView(self.video_scene, parent_widget)
        self.video_view.setStyleSheet("border:none;background:black;")
        self.video_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setFrameShape(QGraphicsView.Shape.NoFrame)
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
            self.player.stop()
            self.video_view.hide()
            self.current_video_path = None

            if not self.bg_label_widget:
                self.bg_label_widget = QLabel(self.parent)
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

            self.bg_label_widget.setPixmap(cropped)
            self.bg_label_widget.setGeometry(0, 0, w, h)
            self.bg_label_widget.show()
            self.current_bg_path = path

    def set_solid_color(self, color):
        from PyQt6.QtGui import QColor

        if self.bg_label_widget:
            self.bg_label_widget.hide()
        self.player.stop()
        self.video_view.hide()

        if not self.solid_bg_widget:
            self.solid_bg_widget = QLabel(self.parent)
            self.solid_bg_widget.lower()

        # 解析颜色并限制明度
        qcolor = QColor(color)

        # 计算灰度值（使用人眼感知的加权公式）
        r, g, b, a = qcolor.getRgb()
        luminance = 0.299 * r + 0.587 * g + 0.114 * b

        # 如果明度超过90，进行缩放
        if luminance > 90:
            scale_factor = 90 / luminance
            qcolor.setRgb(int(r * scale_factor), int(g * scale_factor), int(b * scale_factor), a)

        w, h = self.parent.width(), self.parent.height()
        self.solid_bg_widget.setStyleSheet(f"background:{qcolor.name(QColor.NameFormat.HexArgb)};")
        self.solid_bg_widget.setGeometry(0, 0, w, h)
        self.solid_bg_widget.show()

    def hide(self):
        if self.bg_label_widget:
            self.bg_label_widget.hide()
        if self.solid_bg_widget:
            self.solid_bg_widget.hide()
        self.player.stop()
        self.video_view.hide()
