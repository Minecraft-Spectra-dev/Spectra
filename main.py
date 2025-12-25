import os
import sys

# 禁用 FFmpeg 日志输出
if sys.platform == 'win32':
    import ctypes
    kernel32 = ctypes.windll.kernel32
    kernel32.SetStdHandle(-12, None)  # STD_ERROR_HANDLE

os.environ["QT_LOGGING_RULES"] = "qt.multimedia*=false"

from PyQt6.QtWidgets import QApplication, QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel, QStylePainter, \
    QStyleOptionButton, QStackedWidget, QFileDialog, QLineEdit
from PyQt6.QtCore import Qt, QRect, QPropertyAnimation, QEasingCurve, QUrl, QSizeF
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QCursor
from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
from BlurWindow.blurWindow import blur
import ctypes, sys, json

os.environ["QT_MEDIA_BACKEND"] = "ffmpeg"
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "hwaccel;none"

STYLE_BTN = "QPushButton{background:transparent;border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.2);}"
STYLE_BTN_ACTIVE = "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.1);}"
STYLE_ICON = "color:white;background:transparent;font-size:16px;font-family:'Segoe Fluent Icons';"
STYLE_TEXT = "color:white;background:transparent;font-size:14px;font-family:'微软雅黑';"


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


def make_transparent(widget):
    widget.setStyleSheet("background:transparent;")
    widget.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
    widget.setMouseTracking(True)
    return widget


class Window(QWidget):
    EDGE = 8

    def __init__(self):
        super().__init__()
        self.config_file = "config.json"
        self.config = self.load_config()

        self.setWindowTitle("Spectra")
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))
        self.resize(self.config["window_width"], self.config["window_height"])
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
        self.sidebar.setFixedWidth(50)
        self.sidebar.setStyleSheet("background:rgba(0,0,0,80);")
        self.sidebar.setMouseTracking(True)
        self.sidebar_expanded = False
        self.nav_texts = []
        self.nav_indicators = []

        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(2, 10, 5, 10)
        sb.setSpacing(5)

        # 标题
        title = make_transparent(QWidget())
        title.setFixedSize(133, 30)
        tl = QHBoxLayout(title)
        tl.setContentsMargins(48, 0, 0, 0)
        lbl = QLabel("Spectra")
        lbl.setStyleSheet(STYLE_TEXT)
        lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        lbl.setMouseTracking(True)
        tl.addWidget(lbl)
        tl.addStretch()
        sb.addWidget(title)

        # 导航按钮
        sb.addWidget(self.create_nav_btn("\uE700", "菜单", self.toggle_sidebar))
        sb.addWidget(self.create_nav_btn("\uE80F", "主页", lambda: self.switch_page(0), 0))
        sb.addStretch()
        sb.addWidget(self.create_nav_btn("\uE713", "设置", lambda: self.switch_page(1), 1))

        layout.addWidget(self.sidebar)

        # 右侧区域
        self.right_panel = QWidget()
        self.right_panel.setStyleSheet("background:rgba(0,0,0,100);")
        self.right_panel.setMouseTracking(True)
        rl = QVBoxLayout(self.right_panel)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        # 标题栏
        titlebar = QWidget()
        titlebar.setFixedHeight(40)
        titlebar.setStyleSheet("background:transparent;")
        titlebar.setMouseTracking(True)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(0, 0, 8, 0)
        tb.addStretch()
        for t, s in [("−", self.showMinimized), ("×", self.close)]:
            tb.addWidget(self.create_title_btn(t, s))
        rl.addWidget(titlebar)

        # 内容区
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")
        self.stack.addWidget(QWidget())
        self.stack.addWidget(self.create_config_page())
        rl.addWidget(self.stack, 1)

        layout.addWidget(self.right_panel, 1)

        self.drag_pos = None
        self.resize_edge = None
        self.switch_page(0)

        # 初始化视频组件
        from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene
        from PyQt6.QtMultimediaWidgets import QGraphicsVideoItem

        self.video_scene = QGraphicsScene()
        self.video_view = QGraphicsView(self.video_scene, self)
        self.video_view.setStyleSheet("border:none;background:black;")
        self.video_view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.video_view.setFrameShape(QGraphicsView.Shape.NoFrame)
        self.video_view.hide()

        self.video_item = QGraphicsVideoItem()
        self.video_scene.addItem(self.video_item)

        self.player = QMediaPlayer(self)
        self.player.setVideoOutput(self.video_item)
        self.audio_output = QAudioOutput()
        self.audio_output.setVolume(0)
        self.player.setAudioOutput(self.audio_output)
        self.player.setLoops(QMediaPlayer.Loops.Infinite)

        # 定时器轮询光标位置
        from PyQt6.QtCore import QTimer
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(lambda: self.update_cursor(QCursor.pos()))
        self.cursor_timer.start(50)  # 每 50ms 更新一次

        self.show()

        # 应用保存的配置
        if self.config["background_mode"] == "image" and self.config["background_image_path"]:
            if os.path.exists(self.config["background_image_path"]):
                self.set_background_image(self.config["background_image_path"])

    def load_config(self):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                return {
                    "background_mode": config.get("background_mode", "blur"),
                    "background_image_path": config.get("background_image_path", ""),
                    "window_width": config.get("window_width", 900),
                    "window_height": config.get("window_height", 600)
                }
        except:
            return {
                "background_mode": "blur",
                "background_image_path": "",
                "window_width": 900,
                "window_height": 600
            }

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def create_nav_btn(self, icon, text, handler, page_index=None):
        container = QWidget()
        container.setFixedHeight(40)
        container.setStyleSheet("background:transparent;")
        container.setMouseTracking(True)
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        btn = JellyButton()
        btn.setFixedHeight(40)
        btn.setStyleSheet(STYLE_BTN)
        btn.clicked.connect(handler)

        outer = QHBoxLayout(btn)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        indicator = QWidget()
        indicator.setFixedSize(3, 18)
        indicator.setStyleSheet("background:transparent;border-radius:1px;")
        indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        outer.addWidget(indicator, 0, Qt.AlignmentFlag.AlignVCenter)
        if page_index is not None:
            self.nav_indicators.append((page_index, indicator, btn))

        inner = make_transparent(QWidget())
        inner.setFixedWidth(125)
        il = QHBoxLayout(inner)
        il.setContentsMargins(7, 0, 5, 0)
        il.setSpacing(12)

        icon_lbl = QLabel(icon)
        icon_lbl.setFixedSize(20, 20)
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(STYLE_ICON)
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon_lbl.setMouseTracking(True)
        il.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        text_lbl.setStyleSheet(STYLE_TEXT)
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_lbl.setMouseTracking(True)
        text_lbl.hide()
        il.addWidget(text_lbl)
        il.addStretch()
        self.nav_texts.append(text_lbl)

        outer.addWidget(inner)
        outer.addStretch()
        cl.addWidget(btn)
        return container

    def create_title_btn(self, text, handler):
        b = JellyButton(text)
        b.setFixedSize(32, 32)
        b.setStyleSheet(
            "QPushButton{background:transparent;color:white;border:none;border-radius:16px;font-size:16px;font-family:'微软雅黑';}QPushButton:hover{background:rgba(255,255,255,0.2);}")
        b.clicked.connect(handler)
        return b

    def create_config_page(self):
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(20, 10, 20, 20)
        pl.setSpacing(15)

        title = QLabel("设置")
        title.setStyleSheet("color:white;font-size:20px;font-family:'微软雅黑';font-weight:bold;")
        pl.addWidget(title)

        # 外观设置容器（主卡片）
        self.appearance_container, self.appearance_arrow = self.create_expandable_menu("外观设置", "背景、主题等外观选项")
        pl.addWidget(self.appearance_container)

        # 获取内容区域
        self.appearance_content = self.appearance_container.layout().itemAt(1).widget()

        # 背景选项卡片
        self.blur_card = self.create_bg_card("模糊背景", "使用系统窗口模糊效果",
                                             self.config["background_mode"] == "blur",
                                             lambda: self.set_background("blur"))
        self.appearance_content_layout.addWidget(self.blur_card)

        # 图片背景卡片
        self.image_card = self.create_bg_card("图像背景", "使用图像作为背景", self.config["background_mode"] == "image",
                                              lambda: self.set_background("image"))
        self.appearance_content_layout.addWidget(self.image_card)

        # 路径输入区域
        self.path_widget = QWidget()
        self.path_widget.setStyleSheet("background:rgba(255,255,255,0);border-bottom-left-radius:8px;border-bottom-right-radius:8px;")
        path_layout = QHBoxLayout(self.path_widget)
        path_layout.setContentsMargins(35, 12, 15, 12)
        path_layout.setSpacing(10)

        path_label = QLabel("背景图片路径")
        path_label.setStyleSheet("color:rgba(255,255,255,0.8);font-size:13px;font-family:'微软雅黑';")
        path_layout.addWidget(path_label)

        self.path_input = QLineEdit()
        self.path_input.setText(self.config["background_image_path"])
        self.path_input.setStyleSheet(
            "QLineEdit{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:4px;padding:6px;color:white;font-size:13px;font-family:'微软雅黑';}")
        self.path_input.editingFinished.connect(self.on_path_changed)
        path_layout.addWidget(self.path_input, 1)

        browse_btn = JellyButton("📁")
        browse_btn.setFixedSize(32, 32)
        browse_btn.setStyleSheet(
            "QPushButton{background:rgba(255,255,255,0.1);border:none;border-radius:4px;font-size:16px;}QPushButton:hover{background:rgba(255,255,255,0.15);}")
        browse_btn.clicked.connect(self.choose_background_image)
        path_layout.addWidget(browse_btn)

        self.appearance_content_layout.addWidget(self.path_widget)
        self.path_widget.setVisible(self.config["background_mode"] == "image")

        # 初始状态：默认不展开
        self.appearance_content.setVisible(False)
        self.appearance_arrow.setText("▶")

        pl.addStretch()

        return page

    def create_bg_card(self, title, desc, selected, handler):
        card = CardButton()
        card.setFixedHeight(70)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(handler)

        style = "background:rgba(255,255,255,0.15);" if selected else "background:rgba(255,255,255,0.05);"
        card.setStyleSheet(
            f"QPushButton{{{style}border:none;border-radius:0px;}}QPushButton:hover{{background:rgba(255,255,255,0.1);}}QPushButton:pressed{{background:rgba(255,255,255,0.05);}}")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(12)

        radio = QLabel()
        radio.setFixedSize(20, 20)
        if selected:
            radio.setStyleSheet("background:rgba(255,255,255,0.9);border:5px solid #4080ff;border-radius:10px;")
        else:
            radio.setStyleSheet("background:rgba(255,255,255,0.8);border:1px solid rgba(0,0,0,0.3);border-radius:10px;")
        radio.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        layout.addWidget(radio, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color:white;font-size:14px;font-family:'微软雅黑';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.6);font-size:12px;font-family:'微软雅黑';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        card.radio = radio
        return card

    def create_expandable_menu(self, title, desc):
        # 主容器
        container = QWidget()
        container.setStyleSheet("background:rgba(255,255,255,0.08);border-radius:8px;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 标题栏
        header = CardButton()
        header.setFixedHeight(70)
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.clicked.connect(self.toggle_appearance_menu)

        header.setStyleSheet(
            "QPushButton{background:transparent;border:none;border-top-left-radius:8px;border-top-right-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.05);}QPushButton:pressed{background:rgba(255,255,255,0.02);}")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 12, 15, 12)
        header_layout.setSpacing(12)

        # 箭头图标
        arrow = QLabel("▶")
        arrow.setFixedSize(16, 16)
        arrow.setStyleSheet("color:white;background:transparent;font-size:12px;")
        arrow.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.addWidget(arrow, 0, Qt.AlignmentFlag.AlignTop)

        # 标题和描述
        text_layout = QVBoxLayout()
        text_layout.setSpacing(4)
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet("color:white;font-size:14px;font-family:'微软雅黑';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            "color:rgba(255,255,255,0.6);font-size:12px;font-family:'微软雅黑';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # 内容区域
        self.appearance_content_layout = QVBoxLayout()
        self.appearance_content_layout.setContentsMargins(0, 0, 0, 0)
        self.appearance_content_layout.setSpacing(0)

        content_widget = QWidget()
        content_widget.setLayout(self.appearance_content_layout)
        content_widget.setStyleSheet("background:transparent;")

        main_layout.addWidget(content_widget)

        return container, arrow

    def toggle_appearance_menu(self):
        content = self.appearance_container.layout().itemAt(1).widget()
        is_visible = content.isVisible()

        if is_visible:
            content.setVisible(False)
            self.appearance_arrow.setText("▶")
        else:
            content.setVisible(True)
            self.appearance_arrow.setText("▼")

    def toggle_image_card(self):
        if self.path_widget.isVisible():
            return
        self.path_widget.setVisible(True)
        self.set_background("image")
        if self.config["background_image_path"] and os.path.exists(self.config["background_image_path"]):
            self.set_background_image(self.config["background_image_path"])
        else:
            self.choose_background_image()

    def set_background(self, mode):
        self.config["background_mode"] = mode
        self.save_config()

        if mode == "blur":
            self.blur_card.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.05);}")
            self.blur_card.radio.setStyleSheet(
                "background:rgba(255,255,255,0.9);border:5px solid #4080ff;border-radius:10px;")

            self.image_card.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,0.05);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.03);}")
            self.image_card.radio.setStyleSheet(
                "background:rgba(255,255,255,0.8);border:1px solid rgba(0,0,0,0.3);border-radius:10px;")

            self.path_widget.setVisible(False)

            blur(self.winId())
            if hasattr(self, 'bg_label_widget'):
                self.bg_label_widget.hide()
            if hasattr(self, 'video_view'):
                self.player.stop()
                self.video_view.hide()
                if hasattr(self, 'current_video_path'):
                    delattr(self, 'current_video_path')
        elif mode == "image":
            self.blur_card.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,0.05);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.03);}")
            self.blur_card.radio.setStyleSheet(
                "background:rgba(255,255,255,0.8);border:1px solid rgba(0,0,0,0.3);border-radius:10px;")

            self.image_card.setStyleSheet(
                "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.05);}")
            self.image_card.radio.setStyleSheet(
                "background:rgba(255,255,255,0.9);border:5px solid #4080ff;border-radius:10px;")

            self.path_widget.setVisible(True)

            # 应用已保存的背景
            if self.config.get("background_image_path") and os.path.exists(self.config["background_image_path"]):
                self.set_background_image(self.config["background_image_path"])

    def on_path_changed(self):
        path = self.path_input.text().strip()
        if path and os.path.exists(path):
            self.config["background_image_path"] = path
            self.save_config()
            self.set_background_image(path)
        elif not path:
            self.config["background_image_path"] = ""
            self.save_config()

    def choose_background_image(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择背景", "",
                                              "媒体文件 (*.png *.jpg *.jpeg *.bmp *.mp4 *.avi *.mov *.mkv *.webm);;所有文件 (*.*)")
        if file:
            self.config["background_image_path"] = file
            self.save_config()
            self.path_input.setText(file)
            self.set_background_image(file)

    def set_background_image(self, path):
        if not os.path.exists(path):
            return

        ext = os.path.splitext(path)[1].lower()

        # 视频格式
        if ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']:
            if hasattr(self, 'bg_label_widget'):
                self.bg_label_widget.hide()

            w, h = self.width(), self.height()

            # 只在首次加载或路径改变时重新加载视频
            if not hasattr(self, 'current_video_path') or self.current_video_path != path:
                self.player.setSource(QUrl.fromLocalFile(path))
                self.player.play()
                self.current_video_path = path

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

        # 图片格式
        else:
            if hasattr(self, 'video_view'):
                self.player.stop()
                self.video_view.hide()
                if hasattr(self, 'current_video_path'):
                    delattr(self, 'current_video_path')

            if not hasattr(self, 'bg_label_widget'):
                self.bg_label_widget = QLabel(self)
                self.bg_label_widget.lower()

            pixmap = QPixmap(path)
            w, h = self.width(), self.height()

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

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for i, ind, btn in self.nav_indicators:
            if i == index:
                ind.setStyleSheet("background:#a0a0ff;border-radius:1px;")
                btn.setStyleSheet(STYLE_BTN_ACTIVE)
            else:
                ind.setStyleSheet("background:transparent;border-radius:1px;")
                btn.setStyleSheet(STYLE_BTN)

    def toggle_sidebar(self):
        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        for a in (self.anim, self.anim2):
            a.setDuration(200)
            a.setEasingCurve(QEasingCurve.Type.InOutQuad)
            a.setStartValue(140 if self.sidebar_expanded else 50)
            a.setEndValue(50 if self.sidebar_expanded else 140)
        if self.sidebar_expanded:
            self.anim.finished.connect(lambda: [t.hide() for t in self.nav_texts])
        else:
            [t.show() for t in self.nav_texts]
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

    def update_cursor(self, global_pos):
        local_pos = self.mapFromGlobal(global_pos)
        edge = self.get_edge(local_pos)
        cursors = {"t": Qt.CursorShape.SizeVerCursor, "b": Qt.CursorShape.SizeVerCursor,
                   "l": Qt.CursorShape.SizeHorCursor, "r": Qt.CursorShape.SizeHorCursor,
                   "tl": Qt.CursorShape.SizeFDiagCursor, "br": Qt.CursorShape.SizeFDiagCursor,
                   "tr": Qt.CursorShape.SizeBDiagCursor, "bl": Qt.CursorShape.SizeBDiagCursor}
        self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))

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
            self.update_cursor(ev.globalPosition().toPoint())

    def mouseReleaseEvent(self, ev):
        self.drag_pos = None
        self.resize_edge = None

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, 'current_bg_path') and self.current_bg_path:
            self.set_background_image(self.current_bg_path)

        # 保存窗口尺寸
        if hasattr(self, 'config'):
            self.config["window_width"] = self.width()
            self.config["window_height"] = self.height()
            self.save_config()


app = QApplication(sys.argv)
window = Window()
window.show()
sys.exit(app.exec())
