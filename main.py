from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QRect
from BlurWindow.blurWindow import blur
import ctypes, sys


class Window(QWidget):
    EDGE = 8

    def __init__(self):
        super().__init__()
        self.resize(400, 300)
        self.setMinimumSize(200, 150)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        blur(self.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 33, ctypes.byref(ctypes.c_int(2)), 4)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        titlebar = QWidget()
        titlebar.setFixedHeight(40)
        titlebar.setStyleSheet("background:rgba(0,0,0,100);")
        titlebar.setMouseTracking(True)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(12, 0, 8, 0)
        tb.setSpacing(0)

        title = QLabel("示例程序")
        title.setStyleSheet("color:white;background:transparent;")
        title.setMouseTracking(True)
        tb.addWidget(title)
        tb.addStretch()

        for t, s in [("−", self.showMinimized), ("×", self.close)]:
            b = QPushButton(t)
            b.setFixedSize(32, 32)
            b.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            b.setMouseTracking(True)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:white;border:none;border-radius:16px;font-size:16px;}QPushButton:hover{background:rgba(255,255,255,0.2);}")
            b.clicked.connect(s)
            tb.addWidget(b)

        layout.addWidget(titlebar)

        content = QWidget()
        content.setStyleSheet("background:rgba(0,0,0,100);")
        content.setMouseTracking(True)
        cl = QVBoxLayout(content)
        cl.setContentsMargins(20, 20, 20, 20)

        btn = QPushButton("测试按钮")
        btn.setMouseTracking(True)
        btn.setStyleSheet(
            "QPushButton{background:transparent;color:#0078d4;border:2px solid #0078d4;border-radius:8px;padding:15px;font-size:14px;}QPushButton:hover{background:rgba(0,120,212,0.1);}QPushButton:pressed{background:rgba(0,120,212,0.2);}")
        cl.addWidget(btn)

        layout.addWidget(content, 1)
        self.drag_pos = None
        self.resize_edge = None

    def get_edge(self, pos):
        x, y, w, h, e = pos.x(), pos.y(), self.width(), self.height(), self.EDGE
        edge = ""
        if y < e:
            edge += "t"
        elif y > h - e:
            edge += "b"
        if x < e:
            edge += "l"
        elif x > w - e:
            edge += "r"
        return edge

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            edge = self.get_edge(ev.position().toPoint())
            if edge:
                self.resize_edge = edge
                self.resize_start = ev.globalPosition().toPoint()
                self.resize_geo = self.geometry()
            elif ev.position().y() < 40:
                self.drag_pos = ev.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, ev):
        if self.resize_edge:
            diff = ev.globalPosition().toPoint() - self.resize_start
            geo = QRect(self.resize_geo)
            if 't' in self.resize_edge: geo.setTop(geo.top() + diff.y())
            if 'b' in self.resize_edge: geo.setBottom(geo.bottom() + diff.y())
            if 'l' in self.resize_edge: geo.setLeft(geo.left() + diff.x())
            if 'r' in self.resize_edge: geo.setRight(geo.right() + diff.x())
            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
        elif self.drag_pos:
            self.move(ev.globalPosition().toPoint() - self.drag_pos)
        else:
            edge = self.get_edge(ev.position().toPoint())
            cursors = {"t": Qt.CursorShape.SizeVerCursor, "b": Qt.CursorShape.SizeVerCursor,
                       "l": Qt.CursorShape.SizeHorCursor, "r": Qt.CursorShape.SizeHorCursor,
                       "tl": Qt.CursorShape.SizeFDiagCursor, "br": Qt.CursorShape.SizeFDiagCursor,
                       "tr": Qt.CursorShape.SizeBDiagCursor, "bl": Qt.CursorShape.SizeBDiagCursor}
            self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))

    def mouseReleaseEvent(self, ev):
        self.drag_pos = None
        self.resize_edge = None


app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
