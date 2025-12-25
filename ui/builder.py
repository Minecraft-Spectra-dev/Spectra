"""UI构建器"""

from PyQt6.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
                             QStackedWidget, QLineEdit, QSlider)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap

from widgets import JellyButton, CardButton, ClickableLabel, make_transparent
from styles import (STYLE_BTN, STYLE_BTN_ACTIVE, STYLE_ICON, STYLE_TEXT,
                   SLIDER_STYLE)
from utils import load_svg_icon, scale_icon_for_display


class UIBuilder:
    def __init__(self, window):
        self.window = window
        self.dpi_scale = getattr(window, 'dpi_scale', 1.0)

    def _scale_size(self, size):
        """根据DPI缩放尺寸"""
        return int(size * self.dpi_scale)

    def create_nav_btn(self, icon, text, handler, page_index=None,
                       icon_path=None, icon_path_active=None):
        """创建导航按钮"""
        container = QWidget()
        container.setFixedHeight(self._scale_size(40))
        container.setStyleSheet("background:transparent;")
        container.setMouseTracking(True)
        cl = QHBoxLayout(container)
        cl.setContentsMargins(0, 0, 0, 0)
        cl.setSpacing(0)

        btn = JellyButton()
        btn.setFixedHeight(self._scale_size(40))
        btn.setStyleSheet(STYLE_BTN)
        btn.clicked.connect(handler)

        outer = QHBoxLayout(btn)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        indicator = QWidget()
        indicator.setFixedSize(self._scale_size(3), self._scale_size(18))
        indicator.setStyleSheet("background:transparent;border-radius:1px;")
        indicator.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        outer.addWidget(indicator, 0, Qt.AlignmentFlag.AlignVCenter)
        if page_index is not None:
            self.window.nav_indicators.append((page_index, indicator, btn, icon_path, icon_path_active, container))

        inner = make_transparent(QWidget())
        inner.setFixedWidth(self._scale_size(125))
        il = QHBoxLayout(inner)
        il.setContentsMargins(self._scale_size(7), 0, self._scale_size(5), 0)
        il.setSpacing(self._scale_size(12))

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(self._scale_size(20), self._scale_size(20))
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("background:transparent;")
        icon_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        icon_lbl.setMouseTracking(True)
        icon_lbl.setObjectName("nav_icon")

        if isinstance(icon, QPixmap):
            icon_lbl.setPixmap(scale_icon_for_display(icon, 20, self.dpi_scale))
        else:
            icon_lbl.setText(icon)
            icon_lbl.setStyleSheet(STYLE_ICON)

        il.addWidget(icon_lbl)

        text_lbl = QLabel(text)
        # 根据DPI缩放字体大小
        font_size = int(14 * self.dpi_scale)
        text_lbl.setStyleSheet(f"color:white;background:transparent;font-size:{font_size}px;font-family:'微软雅黑';")
        text_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_lbl.setMouseTracking(True)
        text_lbl.hide()
        il.addWidget(text_lbl)
        il.addStretch()
        self.window.nav_texts.append(text_lbl)

        outer.addWidget(inner)
        outer.addStretch()
        cl.addWidget(btn)
        return container

    def create_title_btn(self, text, handler):
        """创建标题栏按钮"""
        b = JellyButton(text)
        b.setFixedSize(self._scale_size(32), self._scale_size(32))
        font_size = self._scale_size(16)
        b.setStyleSheet(
            f"QPushButton{{background:transparent;color:white;border:none;border-radius:{self._scale_size(16)}px;font-size:{font_size}px;font-family:'微软雅黑';}}QPushButton:hover{{background:rgba(255,255,255,0.2);}}")
        b.clicked.connect(handler)
        return b

    def create_bg_card(self, title, desc, selected, handler):
        """创建背景选项卡片"""
        card = CardButton()
        card.setFixedHeight(self._scale_size(70))
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(handler)

        style = "background:rgba(255,255,255,0.15);" if selected else "background:rgba(255,255,255,0.05);"
        card.setStyleSheet(
            f"QPushButton{{{style}border:none;border-radius:0px;}}QPushButton:hover{{background:rgba(255,255,255,0.1);}}QPushButton:pressed{{background:rgba(255,255,255,0.05);}}")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        layout.setSpacing(self._scale_size(12))

        check_label = QLabel()
        check_label.setFixedSize(self._scale_size(20), self._scale_size(20))
        check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_label.setStyleSheet("background:transparent;")
        check_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        if selected:
            check_pixmap = load_svg_icon("svg/check-lg.svg", self.dpi_scale)
            if check_pixmap:
                check_label.setPixmap(scale_icon_for_display(check_pixmap, 20, self.dpi_scale))

        layout.addWidget(check_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'微软雅黑';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'微软雅黑';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        card.check_label = check_label
        return card

    def create_expandable_menu(self, title, desc, icon_path=None, icon_path_active=None):
        """创建可展开菜单"""
        container = QWidget()
        container.setStyleSheet("background:rgba(255,255,255,0.08);border-radius:8px;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = CardButton()
        header.setFixedHeight(self._scale_size(70))
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.clicked.connect(self.window.toggle_appearance_menu)

        border_radius = self._scale_size(8)
        header.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;border-top-left-radius:{border_radius}px;border-top-right-radius:{border_radius}px;}}QPushButton:hover{{background:rgba(255,255,255,0.05);}}QPushButton:pressed{{background:rgba(255,255,255,0.02);}}")

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        header_layout.setSpacing(self._scale_size(12))

        icon_label = None
        if icon_path:
            icon_label = QLabel()
            icon_label.setFixedSize(self._scale_size(20), self._scale_size(20))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("background:transparent;")
            icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            icon_label.setObjectName("menu_icon")

            icon_pixmap = load_svg_icon(icon_path, self.dpi_scale)
            if icon_pixmap:
                icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))

            header_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'微软雅黑';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'微软雅黑';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        main_layout.addWidget(header)

        self.window.appearance_content_layout = QVBoxLayout()
        self.window.appearance_content_layout.setContentsMargins(0, 0, 0, 0)
        self.window.appearance_content_layout.setSpacing(0)

        content_widget = QWidget()
        content_widget.setLayout(self.window.appearance_content_layout)
        content_widget.setStyleSheet("background:transparent;")

        main_layout.addWidget(content_widget)

        self.window.appearance_icon_path = icon_path
        self.window.appearance_icon_path_active = icon_path_active
        self.window.appearance_icon_label = icon_label

        return container

    def create_config_page(self):
        """创建设置页面"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        title = QLabel("设置")
        title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:'微软雅黑';font-weight:bold;")
        pl.addWidget(title)

        # 外观设置容器
        self.window.appearance_container = self.create_expandable_menu(
            "外观设置", "背景、主题等外观选项", "svg/palette.svg", "svg/palette-fill.svg"
        )
        pl.addWidget(self.window.appearance_container)

        self.window.appearance_content = self.window.appearance_container.layout().itemAt(1).widget()

        # 模糊背景卡片
        self.window.blur_card = self.create_bg_card(
            "模糊背景", "使用系统窗口模糊效果",
            self.window.config.get("background_mode") == "blur",
            lambda: self.window.set_background("blur")
        )
        self.window.appearance_content_layout.addWidget(self.window.blur_card)

        # 透明度滑块
        self._create_opacity_slider()
        self.window.appearance_content_layout.addWidget(self.window.opacity_widget)

        # 图片背景卡片
        self.window.image_card = self.create_bg_card(
            "图像背景", "使用图像作为背景",
            self.window.config.get("background_mode") == "image",
            lambda: self.window.set_background("image")
        )
        self.window.appearance_content_layout.addWidget(self.window.image_card)

        # 路径输入区域
        self._create_path_input()
        self.window.appearance_content_layout.addWidget(self.window.path_widget)

        # 初始状态
        self.window.appearance_content.setVisible(False)

        pl.addStretch()
        return page

    def create_instance_page(self):
        """创建实例页面"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(20, 10, 20, 20)
        pl.setSpacing(15)

        title = QLabel("实例")
        title.setStyleSheet("color:white;font-size:20px;font-family:'微软雅黑';font-weight:bold;")
        pl.addWidget(title)

        pl.addStretch()
        return page

    def create_download_page(self):
        """创建下载页面"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(20, 10, 20, 20)
        pl.setSpacing(15)

        title = QLabel("下载")
        title.setStyleSheet("color:white;font-size:20px;font-family:'微软雅黑';font-weight:bold;")
        pl.addWidget(title)

        pl.addStretch()
        return page

    def _create_opacity_slider(self):
        """创建透明度滑块"""
        self.window.opacity_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.opacity_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        opacity_layout = QVBoxLayout(self.window.opacity_widget)
        opacity_layout.setContentsMargins(self._scale_size(35), self._scale_size(8), self._scale_size(15), self._scale_size(8))
        opacity_layout.setSpacing(self._scale_size(4))

        opacity_header_layout = QHBoxLayout()
        opacity_label = QLabel("模糊透明度")
        opacity_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'微软雅黑';")
        # 将10-255转换为0-100%显示
        opacity_value = QLabel()
        opacity_value.setText(str(int((self.window.config.get("blur_opacity", 150) - 10) / (255 - 10) * 100)) + "%")
        opacity_value.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'微软雅黑';")
        self.window.opacity_value_label = opacity_value
        opacity_header_layout.addWidget(opacity_label)
        opacity_header_layout.addStretch()
        opacity_header_layout.addWidget(opacity_value)
        opacity_layout.addLayout(opacity_header_layout)

        self.window.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.window.opacity_slider.setRange(10, 255)
        self.window.opacity_slider.setValue(self.window.config.get("blur_opacity", 150))
        self.window.opacity_slider.setStyleSheet(SLIDER_STYLE)
        self.window.opacity_slider.valueChanged.connect(self.window.on_opacity_changed)
        opacity_layout.addWidget(self.window.opacity_slider)

        self.window.opacity_widget.setVisible(self.window.config.get("background_mode") == "blur")

    def _create_path_input(self):
        """创建路径输入"""
        self.window.path_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.path_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        path_layout = QHBoxLayout(self.window.path_widget)
        path_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        path_layout.setSpacing(self._scale_size(10))

        path_label = QLabel("背景图片路径")
        path_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'微软雅黑';")
        path_layout.addWidget(path_label)

        self.window.path_input = QLineEdit()
        self.window.path_input.setText(self.window.config.get("background_image_path", ""))
        padding = self._scale_size(6)
        border_radius_input = self._scale_size(4)
        self.window.path_input.setStyleSheet(
            f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:'微软雅黑';}}")
        self.window.path_input.editingFinished.connect(self.window.on_path_changed)
        path_layout.addWidget(self.window.path_input, 1)

        # 浏览按钮
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        border_radius_btn = self._scale_size(4)
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius_btn}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius_btn}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(self.window.choose_background_image)

        folder_pixmap = load_svg_icon("svg/folder2.svg", self.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.dpi_scale))

        path_layout.addWidget(browse_btn)

        self.window.path_widget.setVisible(self.window.config.get("background_mode") == "image")
