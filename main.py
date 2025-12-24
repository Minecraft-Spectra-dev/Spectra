from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QStylePainter, QStyleOptionButton, QStackedWidget
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QIcon, QPainter
from BlurWindow.blurWindow import blur
import ctypes, sys, os


class JellyButton(QPushButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0

    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, s):
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

    def mousePressEvent(self, ev):
        self.anim = QPropertyAnimation(self, b"scale")
        self.anim.setDuration(100)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.92)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
        super().mousePressEvent(ev)

    def mouseReleaseEvent(self, ev):
        self.anim = QPropertyAnimation(self, b"scale")
        self.anim.setDuration(150)
        self.anim.setStartValue(self._scale)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim.start()
        super().mouseReleaseEvent(ev)


class Window(QWidget):
    EDGE = 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Spectra")
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        self.resize(600, 400)
        self.setMinimumSize(400, 300)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)
        blur(self.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 33, ctypes.byref(ctypes.c_int(2)), 4)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 侧边栏
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(40)
        self.sidebar.setStyleSheet("background:rgba(0,0,0,80);")
        self.sidebar.setMouseTracking(True)
        self.sidebar_expanded = False

        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(5, 10, 5, 10)
        sb.setSpacing(5)

        # 标题
        title_widget = QWidget()
        title_widget.setFixedSize(130, 30)
        title_widget.setStyleSheet("background:transparent;")
        title_widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title_layout = QHBoxLayout(title_widget)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)

        title_spacer = QWidget()
        title_spacer.setFixedWidth(35)
        title_layout.addWidget(title_spacer)

        self.title_label = QLabel("Spectra")
        self.title_label.setStyleSheet("color:white;background:transparent;font-size:14px;font-family:'微软雅黑';")
        self.title_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        title_layout.addWidget(self.title_label)
        title_layout.addStretch()

        sb.addWidget(title_widget)

        # 菜单按钮
        self.menu_btn = JellyButton()
        self.menu_btn.setFixedHeight(40)
        self.menu_btn.setMouseTracking(True)
        self.menu_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.2);}")
        self.menu_btn.clicked.connect(self.toggle_sidebar)

        menu_outer = QHBoxLayout(self.menu_btn)
        menu_outer.setContentsMargins(0, 0, 0, 0)
        menu_inner = QWidget()
        menu_inner.setFixedWidth(130)
        menu_inner.setStyleSheet("background:transparent;")
        menu_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        menu_layout = QHBoxLayout(menu_inner)
        menu_layout.setContentsMargins(5, 0, 5, 0)
        menu_layout.setSpacing(12)

        menu_icon = QLabel("\uE700")
        menu_icon.setFixedSize(20, 20)
        menu_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu_icon.setStyleSheet("color:white;background:transparent;font-size:16px;font-family:'Segoe Fluent Icons';")
        menu_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        menu_layout.addWidget(menu_icon)

        self.menu_text = QLabel("菜单")
        self.menu_text.setStyleSheet("color:white;background:transparent;font-size:14px;font-family:'微软雅黑';")
        self.menu_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.menu_text.hide()
        menu_layout.addWidget(self.menu_text)
        menu_layout.addStretch()

        menu_outer.addWidget(menu_inner)
        menu_outer.addStretch()

        sb.addWidget(self.menu_btn)

        # 主页按钮
        self.home_btn = JellyButton()
        self.home_btn.setFixedHeight(40)
        self.home_btn.setMouseTracking(True)
        self.home_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.2);}")
        self.home_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        home_outer = QHBoxLayout(self.home_btn)
        home_outer.setContentsMargins(0, 0, 0, 0)
        home_inner = QWidget()
        home_inner.setFixedWidth(130)
        home_inner.setStyleSheet("background:transparent;")
        home_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        home_layout = QHBoxLayout(home_inner)
        home_layout.setContentsMargins(5, 0, 5, 0)
        home_layout.setSpacing(12)

        home_icon = QLabel("\uE80F")
        home_icon.setFixedSize(20, 20)
        home_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        home_icon.setStyleSheet("color:white;background:transparent;font-size:16px;font-family:'Segoe Fluent Icons';")
        home_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        home_layout.addWidget(home_icon)

        self.home_text = QLabel("主页")
        self.home_text.setStyleSheet("color:white;background:transparent;font-size:14px;font-family:'微软雅黑';")
        self.home_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.home_text.hide()
        home_layout.addWidget(self.home_text)
        home_layout.addStretch()

        home_outer.addWidget(home_inner)
        home_outer.addStretch()

        sb.addWidget(self.home_btn)

        sb.addStretch()

        # 配置按钮
        self.config_btn = JellyButton()
        self.config_btn.setFixedHeight(40)
        self.config_btn.setMouseTracking(True)
        self.config_btn.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.2);}")
        self.config_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        config_outer = QHBoxLayout(self.config_btn)
        config_outer.setContentsMargins(0, 0, 0, 0)
        config_inner = QWidget()
        config_inner.setFixedWidth(130)
        config_inner.setStyleSheet("background:transparent;")
        config_inner.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        config_layout = QHBoxLayout(config_inner)
        config_layout.setContentsMargins(5, 0, 5, 0)
        config_layout.setSpacing(12)

        config_icon = QLabel("\uE713")
        config_icon.setFixedSize(20, 20)
        config_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        config_icon.setStyleSheet("color:white;background:transparent;font-size:16px;font-family:'Segoe Fluent Icons';")
        config_icon.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        config_layout.addWidget(config_icon)

        self.config_text = QLabel("配置")
        self.config_text.setStyleSheet("color:white;background:transparent;font-size:14px;font-family:'微软雅黑';")
        self.config_text.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.config_text.hide()
        config_layout.addWidget(self.config_text)
        config_layout.addStretch()

        config_outer.addWidget(config_inner)
        config_outer.addStretch()

        sb.addWidget(self.config_btn)

        layout.addWidget(self.sidebar)

        # 右侧区域
        right = QWidget()
        right.setStyleSheet("background:rgba(0,0,0,100);")
        right.setMouseTracking(True)
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # 标题栏
        titlebar = QWidget()
        titlebar.setFixedHeight(40)
        titlebar.setStyleSheet("background:transparent;")
        titlebar.setMouseTracking(True)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(0, 0, 8, 0)
        tb.setSpacing(0)
        tb.addStretch()

        for t, s in [("−", self.showMinimized), ("×", self.close)]:
            b = JellyButton(t)
            b.setFixedSize(32, 32)
            b.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
            b.setMouseTracking(True)
            b.setStyleSheet(
                "QPushButton{background:transparent;color:white;border:none;border-radius:16px;font-size:16px;font-family:'微软雅黑';}QPushButton:hover{background:rgba(255,255,255,0.2);}")
            b.clicked.connect(s)
            tb.addWidget(b)

        right_layout.addWidget(titlebar)

        # 内容区（使用 QStackedWidget）
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")

        # 主页
        home_page = QWidget()
        home_page.setStyleSheet("background:transparent;")
        self.stack.addWidget(home_page)

        # 配置页
        config_page = QWidget()
        config_page.setStyleSheet("background:transparent;")
        config_page_layout = QVBoxLayout(config_page)
        config_page_layout.setContentsMargins(20, 10, 20, 20)
        config_page_layout.setSpacing(15)

        config_title = QLabel("应用设置")
        config_title.setStyleSheet("color:white;font-size:20px;font-family:'微软雅黑';font-weight:bold;")
        config_page_layout.addWidget(config_title)

        config_page_layout.addStretch()

        self.stack.addWidget(config_page)

        right_layout.addWidget(self.stack, 1)

        layout.addWidget(right, 1)

        self.drag_pos = None
        self.resize_edge = None

    def toggle_sidebar(self):
        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.anim.setDuration(200)
        self.anim2.setDuration(200)
        self.anim.setEasingCurve(QEasingCurve.Type.InOutQuad)
        self.anim2.setEasingCurve(QEasingCurve.Type.InOutQuad)
        if self.sidebar_expanded:
            self.anim.setStartValue(140)
            self.anim.setEndValue(40)
            self.anim2.setStartValue(140)
            self.anim2.setEndValue(40)
            self.anim.finished.connect(lambda: (self.menu_text.hide(), self.home_text.hide(), self.config_text.hide()))
        else:
            self.anim.setStartValue(40)
            self.anim.setEndValue(140)
            self.anim2.setStartValue(40)
            self.anim2.setEndValue(140)
            self.menu_text.show()
            self.home_text.show()
            self.config_text.show()
        self.anim.start()
        self.anim2.start()
        self.sidebar_expanded = not self.sidebar_expanded

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
            elif ev.position().y() < 40 and ev.position().x() > self.sidebar.width():
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
