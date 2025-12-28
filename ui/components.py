"""UI基础组件模块

包含可复用的自定义组件
"""

import logging
from PyQt6.QtCore import (Qt, QPropertyAnimation, QEasingCurve, pyqtSignal)
from PyQt6.QtGui import QPainter, QColor, QBrush
from PyQt6.QtWidgets import QWidget

from utils import load_svg_icon, scale_icon_for_display

logger = logging.getLogger(__name__)

# 尝试从 PyQt6.QtCore 导入 pyqtProperty，如果失败则使用 Property
try:
    from PyQt6.QtCore import pyqtProperty
except ImportError:
    from PyQt6.QtCore import Property as pyqtProperty


class VersionCardWidget(QWidget):
    """版本卡片小部件，支持悬停事件处理"""

    def __init__(self, parent=None, on_hover_change=None):
        super().__init__(parent)
        self._on_hover_change = on_hover_change
        self._is_version = False
        self._is_favorited = False
        self._bookmark_btn = None
        self._edit_btn = None
        self._normal_style = ""
        self._hover_style = ""

    def set_bookmark_info(self, bookmark_btn, is_favorited):
        """设置收藏按钮和收藏状态"""
        self._bookmark_btn = bookmark_btn
        self._is_favorited = is_favorited

    def set_edit_button(self, edit_btn):
        """设置编辑按钮"""
        self._edit_btn = edit_btn

    def set_styles(self, normal_style, hover_style):
        """设置悬停样式"""
        self._normal_style = normal_style
        self._hover_style = hover_style

    def enterEvent(self, event):
        """鼠标进入事件"""
        self.setStyleSheet(self._hover_style)
        if self._bookmark_btn and not self._is_favorited:
            # 未收藏的版本悬停时显示收藏图标
            from PyQt6.QtGui import QIcon
            bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self._get_dpi_scale())
            if bookmark_pixmap:
                scaled_pixmap = scale_icon_for_display(bookmark_pixmap, 16, self._get_dpi_scale())
                self._bookmark_btn.setIcon(QIcon(scaled_pixmap))
        if self._edit_btn:
            # 悬停时显示编辑按钮
            self._edit_btn.show()
        if self._on_hover_change:
            self._on_hover_change(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self.setStyleSheet(self._normal_style)
        if self._bookmark_btn and not self._is_favorited:
            # 未收藏的版本离开时隐藏收藏图标
            from PyQt6.QtGui import QIcon
            self._bookmark_btn.setIcon(QIcon())
        if self._edit_btn:
            # 离开时隐藏编辑按钮
            self._edit_btn.hide()
        if self._on_hover_change:
            self._on_hover_change(False)
        super().leaveEvent(event)

    def _get_dpi_scale(self):
        """获取DPI缩放比例"""
        window = self.window()
        if window:
            return getattr(window, 'dpi_scale', 1.0)
        return 1.0


class ToggleSwitch(QWidget):
    """自定义切换开关组件"""

    def __init__(self, parent=None, checked=False, dpi_scale=1.0):
        super().__init__(parent)
        self._checked = checked
        self._slider_position = 0.0 if not checked else 1.0
        self.dpi_scale = dpi_scale
        self.setFixedSize(int(40 * dpi_scale), int(22 * dpi_scale))
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._animation = None
        self._callback = None

    @pyqtProperty(float)
    def sliderPosition(self):
        return self._slider_position

    @sliderPosition.setter
    def sliderPosition(self, position):
        self._slider_position = position
        self.update()

    @property
    def checked(self):
        return self._checked

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            target_position = 1.0 if checked else 0.0

            if self._animation:
                self._animation.stop()
            self._animation = QPropertyAnimation(self, b"sliderPosition")
            self._animation.setDuration(200)
            self._animation.setEasingCurve(QEasingCurve.Type.InOutQuad)
            self._animation.setStartValue(self._slider_position)
            self._animation.setEndValue(target_position)
            self._animation.start()
            self.update()

    def mousePressEvent(self, event):
        self.setChecked(not self._checked)
        if self._callback:
            self._callback(self._checked)

    def setCallback(self, callback):
        self._callback = callback

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 计算尺寸
        w = self.width()
        h = self.height()
        track_height = h * 0.75
        track_width = w * 0.9
        knob_size = h * 0.85
        track_y = (h - track_height) / 2
        track_x = (w - track_width) / 2

        # 绘制轨道
        track_color = QColor(102, 132, 255) if self._checked else QColor(120, 120, 120)
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(
            int(track_x), int(track_y), int(track_width), int(track_height),
            int(track_height / 2), int(track_height / 2)
        )

        # 绘制滑块
        knob_x = track_x + self._slider_position * (track_width - knob_size)
        knob_y = (h - knob_size) / 2
        if self._checked:
            painter.setBrush(QBrush(QColor(255, 255, 255)))
        else:
            painter.setBrush(QBrush(QColor(200, 200, 200)))
        painter.drawEllipse(int(knob_x), int(knob_y), int(knob_size), int(knob_size))
