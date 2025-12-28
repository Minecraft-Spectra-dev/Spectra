"""自定义按钮组件"""

from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import (QHBoxLayout, QPushButton, QStyleOptionButton,
                             QStylePainter, QVBoxLayout, QWidget)


def make_transparent(widget):
    widget.setStyleSheet("background:transparent;")
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setMouseTracking(True)
    return widget


class JellyButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._scale = 1.0
        self.setMouseTracking(True)

    def getScale(self):
        return self._scale

    def setScale(self, s):
        self._scale = s
        self.update()

    def paintEvent(self, ev):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter.drawControl(self.style().ControlElement.CE_PushButton, opt)

    def _animate(self, end, duration, curve):
        # 停止之前的动画
        if hasattr(self, 'anim') and self.anim is not None:
            self.anim.stop()
            self.anim.deleteLater()
        
        self.anim = QPropertyAnimation()
        self.anim.setDuration(duration)
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(end)
        self.anim.setEasingCurve(curve)
        self.anim.valueChanged.connect(self.setScale)
        self.anim.start()

    def mousePressEvent(self, ev):
        self._animate(0.92, 100, QEasingCurve.Type.OutQuad)
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._animate(1.0, 150, QEasingCurve.Type.OutBack)
        super().mouseReleaseEvent(ev)

    def mouseMoveEvent(self, ev):
        win = self.window()
        if hasattr(win, 'update_cursor'):
            win.update_cursor(ev.globalPosition().toPoint())
        super().mouseMoveEvent(ev)
    
    def deleteLater(self):
        """删除对象时停止动画"""
        if hasattr(self, 'anim') and self.anim is not None:
            self.anim.stop()
            self.anim.deleteLater()
        super().deleteLater()


class CardButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.setMouseTracking(True)

    def getScale(self):
        return self._scale

    def setScale(self, s):
        self._scale = s
        self.update()

    def paintEvent(self, ev):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)
        opt = QStyleOptionButton()
        self.initStyleOption(opt)
        painter.drawControl(self.style().ControlElement.CE_PushButton, opt)

    def _animate(self, end, duration, curve):
        # 停止之前的动画
        if hasattr(self, 'anim') and self.anim is not None:
            self.anim.stop()
            self.anim.deleteLater()
        
        self.anim = QPropertyAnimation()
        self.anim.setDuration(duration)
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(end)
        self.anim.setEasingCurve(curve)
        self.anim.valueChanged.connect(self.setScale)
        self.anim.start()

    def mousePressEvent(self, ev):
        self._animate(0.97, 80, QEasingCurve.Type.Linear)
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        self._animate(1.0, 120, QEasingCurve.Type.Linear)
        super().mouseReleaseEvent(ev)
    
    def deleteLater(self):
        """删除对象时停止动画"""
        if hasattr(self, 'anim') and self.anim is not None:
            self.anim.stop()
            self.anim.deleteLater()
        super().deleteLater()
