"""UI构建器"""

from PyQt6.QtWidgets import (QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QLabel,
                             QLineEdit, QSlider, QColorDialog)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor

from widgets import JellyButton, CardButton, ClickableLabel, make_transparent, get_current_font, set_current_font
from styles import STYLE_BTN, STYLE_ICON, SLIDER_STYLE
from utils import load_svg_icon, scale_icon_for_display


class UIBuilder:
    def __init__(self, window):
        self.window = window
        self.dpi_scale = getattr(window, 'dpi_scale', 1.0)

    def _scale_size(self, size):
        return int(size * self.dpi_scale)

    def _get_font_family(self):
        """获取当前字体系列"""
        return get_current_font()

    def create_nav_btn(self, icon, text, handler, page_index=None,
                       icon_path=None, icon_path_active=None):
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
        font_size = int(14 * self.dpi_scale)
        text_lbl.setStyleSheet(f"color:white;background:transparent;font-size:{font_size}px;font-family:'{self._get_font_family()}';")
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
        b = JellyButton(text)
        b.setFixedSize(self._scale_size(32), self._scale_size(32))
        font_size = self._scale_size(16)
        b.setStyleSheet(
            f"QPushButton{{background:transparent;color:white;border:none;border-radius:{self._scale_size(16)}px;font-size:{font_size}px;font-family:'{self._get_font_family()}';}}QPushButton:hover{{background:rgba(255,255,255,0.2);}}")
        b.clicked.connect(handler)
        return b

    def create_bg_card(self, title, desc, selected, handler):
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
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        card.check_label = check_label
        return card

    def create_expandable_menu(self, title, desc, icon_path=None, icon_path_active=None, toggle_handler=None, content_attr="appearance"):
        container = QWidget()
        container.setStyleSheet("background:rgba(255,255,255,0.08);border-radius:8px;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        header = CardButton()
        header.setFixedHeight(self._scale_size(70))
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        if toggle_handler:
            header.clicked.connect(toggle_handler)
        else:
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
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(desc)
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        main_layout.addWidget(header)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        content_widget = QWidget()
        content_widget.setLayout(content_layout)
        content_widget.setStyleSheet("background:transparent;")

        main_layout.addWidget(content_widget)

        setattr(self.window, f"{content_attr}_content_layout", content_layout)
        setattr(self.window, f"{content_attr}_icon_path", icon_path)
        setattr(self.window, f"{content_attr}_icon_path_active", icon_path_active)
        setattr(self.window, f"{content_attr}_icon_label", icon_label)

        return container

    def create_config_page(self):
        """创建设置页面"""
        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        title = QLabel(self.window.language_manager.translate("page_settings"))
        title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:'{self._get_font_family()}';font-weight:bold;")
        pl.addWidget(title)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 滚动内容区域
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(self._scale_size(15))
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 外观设置容器
        self.window.appearance_container = self.create_expandable_menu(
            self.window.language_manager.translate("settings_appearance"),
            self.window.language_manager.translate("settings_appearance_desc"),
            "svg/palette.svg", "svg/palette-fill.svg",
            content_attr="appearance"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.window.appearance_container)

        self.window.appearance_content = self.window.appearance_container.layout().itemAt(1).widget()

        # 模糊背景卡片
        self.window.blur_card = self.create_bg_card(
            self.window.language_manager.translate("background_blur"),
            self.window.language_manager.translate("background_blur_desc"),
            self.window.config.get("background_mode") == "blur",
            lambda: self.window.set_background("blur")
        )
        self.window.appearance_content_layout.addWidget(self.window.blur_card)

        # 透明度滑块
        self._create_opacity_slider()
        self.window.appearance_content_layout.addWidget(self.window.opacity_widget)

        # 纯色背景卡片
        self.window.solid_card = self.create_bg_card(
            self.window.language_manager.translate("background_solid"),
            self.window.language_manager.translate("background_solid_desc"),
            self.window.config.get("background_mode") == "solid",
            lambda: self.window.set_background("solid")
        )
        self.window.appearance_content_layout.addWidget(self.window.solid_card)

        # 颜色选择区域
        self._create_color_picker()
        self.window.appearance_content_layout.addWidget(self.window.color_widget)

        # 图片背景卡片
        self.window.image_card = self.create_bg_card(
            self.window.language_manager.translate("background_image"),
            self.window.language_manager.translate("background_image_desc"),
            self.window.config.get("background_mode") == "image",
            lambda: self.window.set_background("image")
        )
        self.window.appearance_content_layout.addWidget(self.window.image_card)

        # 路径输入区域
        self._create_path_input()
        self.window.appearance_content_layout.addWidget(self.window.path_widget)

        self.window.appearance_content.setVisible(False)

        # 语言设置容器
        self.window.language_container = self.create_expandable_menu(
            self.window.language_manager.translate("settings_language"),
            self.window.language_manager.translate("settings_language_desc"),
            "svg/translate.svg", "svg/file-earmark-font.svg",
            toggle_handler=self.window.toggle_language_menu,
            content_attr="language"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.window.language_container)

        self.window.language_content = self.window.language_container.layout().itemAt(1).widget()

        # 语言卡片（创建但不添加到布局，_create_language_card 会自己添加）
        self._create_language_card()

        self.window.language_content.setVisible(False)

        # 字体设置容器
        self.window.font_container = self.create_expandable_menu(
            self.window.language_manager.translate("settings_font"),
            self.window.language_manager.translate("settings_font_desc"),
            "svg/type.svg", "svg/file-earmark-font.svg",
            toggle_handler=self.window.toggle_font_menu,
            content_attr="font"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.window.font_container)

        self.window.font_content = self.window.font_container.layout().itemAt(1).widget()

        # 选择字体卡片
        self.window.font_select_card = self.create_bg_card(
            self.window.language_manager.translate("font_select"),
            self.window.language_manager.translate("font_select_desc"),
            self.window.config.get("font_mode") == 0,
            lambda: self.window.set_font_mode(0)
        )
        self.window.font_content_layout.addWidget(self.window.font_select_card)

        # 字体选择下拉框区域
        self._create_font_select_widget()
        self.window.font_content_layout.addWidget(self.window.font_select_widget)

        # 自定义字体卡片
        self.window.font_custom_card = self.create_bg_card(
            self.window.language_manager.translate("font_custom"),
            self.window.language_manager.translate("font_custom_desc"),
            self.window.config.get("font_mode") == 1,
            lambda: self.window.set_font_mode(1)
        )
        self.window.font_content_layout.addWidget(self.window.font_custom_card)

        # 自定义字体路径输入区域
        self._create_font_path_widget()
        self.window.font_content_layout.addWidget(self.window.font_path_widget)

        self.window.font_content.setVisible(False)

        return page

    def create_instance_page(self):
        """创建实例页面"""
        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        title = QLabel(self.window.language_manager.translate("page_instances"))
        title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:'{self._get_font_family()}';font-weight:bold;")
        pl.addWidget(title)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 滚动内容区域
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, self._scale_size(10), 0, 0)
        scroll_layout.setSpacing(self._scale_size(15))
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        return page

    def create_download_page(self):
        """创建下载页面"""
        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        title = QLabel(self.window.language_manager.translate("page_downloads"))
        title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:'{self._get_font_family()}';font-weight:bold;")
        pl.addWidget(title)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 滚动内容区域
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, self._scale_size(10), 0, 0)
        scroll_layout.setSpacing(self._scale_size(15))
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        return page

    def _create_opacity_slider(self):
        self.window.opacity_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.opacity_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        opacity_layout = QVBoxLayout(self.window.opacity_widget)
        opacity_layout.setContentsMargins(self._scale_size(35), self._scale_size(8), self._scale_size(15), self._scale_size(8))
        opacity_layout.setSpacing(self._scale_size(4))

        opacity_header_layout = QHBoxLayout()
        opacity_label = QLabel(self.window.language_manager.translate("blur_opacity"))
        opacity_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        opacity_value = QLabel()
        opacity_value.setText(str(int((self.window.config.get("blur_opacity", 150) - 10) / (255 - 10) * 100)) + "%")
        opacity_value.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
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
        self.window.path_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.path_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        path_layout = QHBoxLayout(self.window.path_widget)
        path_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        path_layout.setSpacing(self._scale_size(10))

        path_label = QLabel(self.window.language_manager.translate("bg_image_path"))
        path_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        path_layout.addWidget(path_label)

        self.window.path_input = QLineEdit()
        self.window.path_input.setText(self.window.config.get("background_image_path", ""))
        padding = self._scale_size(6)
        border_radius_input = self._scale_size(4)
        self.window.path_input.setStyleSheet(
            f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';}}")
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

    def _create_color_picker(self):
        self.window.color_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.color_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        color_layout = QHBoxLayout(self.window.color_widget)
        color_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        color_layout.setSpacing(self._scale_size(10))

        color_label = QLabel(self.window.language_manager.translate("bg_color"))
        color_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        color_layout.addWidget(color_label)

        # 颜色预览和输入
        self.window.color_input = QLineEdit()
        self.window.color_input.setText(self.window.config.get("background_color", "#00000000"))
        padding = self._scale_size(6)
        border_radius_input = self._scale_size(4)
        self.window.color_input.setStyleSheet(
            f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';}}")
        self.window.color_input.editingFinished.connect(self.window.on_color_changed)
        color_layout.addWidget(self.window.color_input, 1)

        color_btn = QPushButton()
        color_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        border_radius_btn = self._scale_size(4)

        color_str = self.window.config.get("background_color", "#00000000")
        try:
            from PyQt6.QtGui import QColor
            color = self._parse_color(color_str)
            bg_color = color.name(QColor.NameFormat.HexArgb) if color else "#00000000"
        except:
            bg_color = "#00000000"

        color_btn.setStyleSheet(f"QPushButton{{background:{bg_color};border:1px solid rgba(255,255,255,0.3);border-radius:{border_radius_btn}px;}}QPushButton:hover{{background:{bg_color};border:1px solid rgba(255,255,255,0.5);}}")
        color_btn.clicked.connect(self.window.choose_background_color)
        color_layout.addWidget(color_btn)
        self.window.color_btn = color_btn

        self.window.color_widget.setVisible(self.window.config.get("background_mode") == "solid")

    def _parse_color(self, color_str):
        from PyQt6.QtGui import QColor
        color = QColor(color_str)
        if color.isValid():
            return color
        if len(color_str) == 7 and color_str.startswith('#'):
            return QColor(f"#FF{color_str[1:]}")
        return QColor("#00000000")

    def _create_font_select_widget(self):
        self.window.font_select_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.font_select_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        font_select_layout = QHBoxLayout(self.window.font_select_widget)
        font_select_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        font_select_layout.setSpacing(self._scale_size(10))

        font_select_label = QLabel(self.window.language_manager.translate("font_select_label"))
        font_select_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        font_select_layout.addWidget(font_select_label)

        font_select_layout.addStretch()

        from PyQt6.QtWidgets import QComboBox
        from PyQt6.QtGui import QFontDatabase
        self.window.font_combo = QComboBox()
        self.window.font_combo.setFixedHeight(self._scale_size(32))
        self.window.font_combo.setFixedWidth(self._scale_size(200))
        self.window.font_combo.setMaxVisibleItems(8)
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)

        # 获取当前下拉框透明度（主页透明度 + 20）
        blur_opacity = self.window.config.get("blur_opacity", 150)
        dropdown_opacity_value = min(255, blur_opacity + 20)
        dropdown_opacity_rgba = dropdown_opacity_value / 255.0

        self.window.font_combo.setStyleSheet(
            f"QComboBox{{"
            f"background:rgba(0,0,0,0.3);"
            f"border:1px solid rgba(255,255,255,0.15);"
            f"border-radius:{border_radius}px;"
            f"padding:{padding}px;"
            f"color:rgba(255,255,255,0.95);"
            f"font-size:{self._scale_size(13)}px;"
            f"font-family:'{self._get_font_family()}';"
            f"}}"
            f"QComboBox:hover{{"
            f"background:rgba(0,0,0,0.4);"
            f"border:1px solid rgba(255,255,255,0.25);"
            f"}}"
            f"QComboBox:focus{{"
            f"background:rgba(0,0,0,0.5);"
            f"border:1px solid rgba(100,150,255,0.6);"
            f"}}"
            f"QComboBox:on{{"
            f"padding-top:{padding - 1}px;"
            f"padding-bottom:{padding - 1}px;"
            f"}}"
            f"QComboBox::drop-down{{"
            f"border:none;"
            f"width:28px;"
            f"background:transparent;"
            f"}}"
            # f"QComboBox::down-arrow{{"
            # f"image:url(svg/x-diamond.svg);"
            # f"width:12px;"
            # f"height:12px;"
            # f"}}"
            f"QComboBox QAbstractItemView{{"
            f"background:rgba(0,0,0,{dropdown_opacity_rgba:.2f});"
            f"border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:{border_radius}px;"
            f"selection-background-color:rgba(255,255,255,0.15);"
            f"selection-color:white;"
            f"outline:none;"
            f"padding:{self._scale_size(2)}px;"
            f"}}"
            f"QComboBox QAbstractItemView::item{{"
            f"height:{self._scale_size(28)}px;"
            f"padding:{self._scale_size(6)}px {self._scale_size(8)}px;"
            f"color:rgba(255,255,255,0.85);"
            f"border-radius:{border_radius - 1}px;"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover{{"
            f"background:rgba(255,255,255,0.1);"
            f"}}"
            f"QComboBox QAbstractItemView::item:selected{{"
            f"background:rgba(255,255,255,0.15);"
            f"color:white;"
            f"}}"
            f"QComboBox QScrollBar:vertical{{"
            f"background:rgba(255,255,255,0.05);"
            f"width:8px;"
            f"margin:0px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical{{"
            f"background:rgba(255,255,255,0.3);"
            f"min-height:20px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical:hover{{"
            f"background:rgba(255,255,255,0.5);"
            f"}}"
            f"QComboBox QScrollBar::add-line:vertical,"
            f"QComboBox QScrollBar::sub-line:vertical{{"
            f"border:none;"
            f"background:none;"
            f"}}"
            f"QComboBox QScrollBar::add-page:vertical,"
            f"QComboBox QScrollBar::sub-page:vertical{{"
            f"background:none;"
            f"}}"
        )
        # 获取系统字体
        families = QFontDatabase.families()
        # 过滤一些常见的系统字体
        common_fonts = ["Microsoft YaHei UI", "Microsoft YaHei", "SimSun", "SimHei", "Arial", "Tahoma", "Verdana", "Segoe UI"]
        for font in common_fonts:
            if font in families:
                self.window.font_combo.addItem(font)
        # 添加剩余字体
        for font in families:
            if font not in common_fonts:
                self.window.font_combo.addItem(font)

        # 设置当前字体
        current_font = self.window.config.get("custom_font_family", "Microsoft YaHei UI")
        for i in range(self.window.font_combo.count()):
            if self.window.font_combo.itemText(i) == current_font:
                self.window.font_combo.setCurrentIndex(i)
                break

        # 连接字体选择事件
        self.window.font_combo.currentTextChanged.connect(self.window.on_font_family_changed)

        font_select_layout.addWidget(self.window.font_combo)

        self.window.font_select_widget.setVisible(self.window.config.get("font_mode") == 0)

        return self.window.font_select_widget

    def _create_font_path_widget(self):
        self.window.font_path_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.font_path_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        font_path_layout = QHBoxLayout(self.window.font_path_widget)
        font_path_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        font_path_layout.setSpacing(self._scale_size(10))

        font_path_label = QLabel(self.window.language_manager.translate("font_custom_label"))
        font_path_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        font_path_layout.addWidget(font_path_label)

        self.window.font_path_input = QLineEdit()
        self.window.font_path_input.setText(self.window.config.get("custom_font_path", ""))
        padding = self._scale_size(6)
        border_radius_input = self._scale_size(4)
        self.window.font_path_input.setStyleSheet(
            f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';}}")
        self.window.font_path_input.editingFinished.connect(self.window.on_font_path_changed)
        font_path_layout.addWidget(self.window.font_path_input, 1)

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
        browse_btn.setCallback(self.window.choose_font_file)

        folder_pixmap = load_svg_icon("svg/folder2.svg", self.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.dpi_scale))

        font_path_layout.addWidget(browse_btn)

        self.window.font_path_widget.setVisible(self.window.config.get("font_mode") == 1)

        return self.window.font_path_widget

    def _create_language_card(self):
        language_widget = QWidget()
        language_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{self._scale_size(8)}px;border-bottom-right-radius:{self._scale_size(8)}px;")
        language_layout = QHBoxLayout(language_widget)
        language_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        language_layout.setSpacing(self._scale_size(10))

        language_label = QLabel(self.window.language_manager.translate("settings_language_label"))
        language_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        language_layout.addWidget(language_label)

        language_layout.addStretch()

        from PyQt6.QtWidgets import QComboBox
        self.window.language_combo = QComboBox()
        self.window.language_combo.setFixedHeight(self._scale_size(32))
        self.window.language_combo.setFixedWidth(self._scale_size(150))
        self.window.language_combo.setMaxVisibleItems(5)
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)

        # 获取当前下拉框透明度（主页透明度 + 20）
        blur_opacity = self.window.config.get("blur_opacity", 150)
        dropdown_opacity_value = min(255, blur_opacity + 20)
        dropdown_opacity_rgba = dropdown_opacity_value / 255.0

        self.window.language_combo.setStyleSheet(
            f"QComboBox{{"
            f"background:rgba(0,0,0,0.3);"
            f"border:1px solid rgba(255,255,255,0.15);"
            f"border-radius:{border_radius}px;"
            f"padding:{padding}px;"
            f"color:rgba(255,255,255,0.95);"
            f"font-size:{self._scale_size(13)}px;"
            f"font-family:'{self._get_font_family()}';"
            f"}}"
            f"QComboBox:hover{{"
            f"background:rgba(0,0,0,0.4);"
            f"border:1px solid rgba(255,255,255,0.25);"
            f"}}"
            f"QComboBox:focus{{"
            f"background:rgba(0,0,0,0.5);"
            f"border:1px solid rgba(100,150,255,0.6);"
            f"}}"
            f"QComboBox:on{{"
            f"padding-top:{padding - 1}px;"
            f"padding-bottom:{padding - 1}px;"
            f"}}"
            f"QComboBox::drop-down{{"
            f"border:none;"
            f"width:28px;"
            f"background:transparent;"
            f"}}"
            # f"QComboBox::down-arrow{{"
            # f"image:url(svg/x-diamond.svg);"
            # f"width:12px;"
            # f"height:12px;"
            # f"}}"
            f"QComboBox QAbstractItemView{{"
            f"background:rgba(0,0,0,{dropdown_opacity_rgba:.2f});"
            f"border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:{border_radius}px;"
            f"selection-background-color:rgba(255,255,255,0.15);"
            f"selection-color:white;"
            f"outline:none;"
            f"padding:{self._scale_size(2)}px;"
            f"}}"
            f"QComboBox QAbstractItemView::item{{"
            f"height:{self._scale_size(28)}px;"
            f"padding:{self._scale_size(6)}px {self._scale_size(8)}px;"
            f"color:rgba(255,255,255,0.85);"
            f"border-radius:{border_radius - 1}px;"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover{{"
            f"background:rgba(255,255,255,0.1);"
            f"}}"
            f"QComboBox QAbstractItemView::item:selected{{"
            f"background:rgba(255,255,255,0.15);"
            f"color:white;"
            f"}}"
            f"QComboBox QScrollBar:vertical{{"
            f"background:rgba(255,255,255,0.05);"
            f"width:8px;"
            f"margin:0px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical{{"
            f"background:rgba(255,255,255,0.3);"
            f"min-height:20px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical:hover{{"
            f"background:rgba(255,255,255,0.5);"
            f"}}"
            f"QComboBox QScrollBar::add-line:vertical,"
            f"QComboBox QScrollBar::sub-line:vertical{{"
            f"border:none;"
            f"background:none;"
            f"}}"
            f"QComboBox QScrollBar::add-page:vertical,"
            f"QComboBox QScrollBar::sub-page:vertical{{"
            f"background:none;"
            f"}}"
        )
        # 添加语言选项
        languages = self.window.language_manager.get_all_languages()
        for lang_code, display_name in languages:
            self.window.language_combo.addItem(display_name, lang_code)
        
        # 设置当前语言
        current_lang = self.window.language_manager.get_language()
        for i in range(self.window.language_combo.count()):
            if self.window.language_combo.itemData(i) == current_lang:
                self.window.language_combo.setCurrentIndex(i)
                break
        
        # 连接语言切换事件
        self.window.language_combo.currentIndexChanged.connect(self.window.change_language)

        language_layout.addWidget(self.window.language_combo)

        self.window.language_content_layout.addWidget(language_widget)

        return language_widget
    
    def _update_page_titles(self):
        """更新页面标题"""
        # 主页没有标题，跳过
        
        # 更新实例页面标题
        instance_page = self.window.stack.widget(1)
        if instance_page and instance_page.layout():
            title = instance_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_instances"))
        
        # 更新下载页面标题
        download_page = self.window.stack.widget(2)
        if download_page and download_page.layout():
            title = download_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_downloads"))
        
        # 更新设置页面标题
        settings_page = self.window.stack.widget(3)
        if settings_page and settings_page.layout():
            title = settings_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_settings"))
    
    def _update_settings_page(self):
        """更新设置页面的文本"""
        settings_page = self.window.stack.widget(3)
        if not settings_page or not settings_page.layout():
            return
        
        layout = settings_page.layout()
        
        # 更新外观设置容器
        appearance_header = self.window.appearance_container.layout().itemAt(0).widget()
        if appearance_header and appearance_header.layout():
            header_layout = appearance_header.layout()
            # 查找文本布局
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    # 第一个是标题，第二个是描述
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        title.setText(self.window.language_manager.translate("settings_appearance"))
                        desc.setText(self.window.language_manager.translate("settings_appearance_desc"))
                        break
        
        # 更新背景卡片
        self._update_bg_card(self.window.blur_card, "background_blur", "background_blur_desc")
        self._update_bg_card(self.window.solid_card, "background_solid", "background_solid_desc")
        self._update_bg_card(self.window.image_card, "background_image", "background_image_desc")
        
        # 更新透明度标签
        if hasattr(self.window, 'opacity_widget'):
            opacity_layout = self.window.opacity_widget.layout()
            if opacity_layout and opacity_layout.count() > 0:
                header_layout = opacity_layout.itemAt(0)
                if header_layout and isinstance(header_layout, QHBoxLayout):
                    label = header_layout.itemAt(0).widget()
                    label.setText(self.window.language_manager.translate("blur_opacity"))
        
        # 更新路径标签
        if hasattr(self.window, 'path_widget'):
            path_layout = self.window.path_widget.layout()
            if path_layout and path_layout.count() > 0:
                label = path_layout.itemAt(0).widget()
                label.setText(self.window.language_manager.translate("bg_image_path"))
        
        # 更新颜色标签
        if hasattr(self.window, 'color_widget'):
            color_layout = self.window.color_widget.layout()
            if color_layout and color_layout.count() > 0:
                label = color_layout.itemAt(0).widget()
                label.setText(self.window.language_manager.translate("bg_color"))
        
        # 更新语言设置容器
        language_header = self.window.language_container.layout().itemAt(0).widget()
        if language_header and language_header.layout():
            header_layout = language_header.layout()
            # 查找文本布局
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    # 第一个是标题，第二个是描述
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        if title and hasattr(title, 'setText'):
                            title.setText(self.window.language_manager.translate("settings_language"))
                        if desc and hasattr(desc, 'setText'):
                            desc.setText(self.window.language_manager.translate("settings_language_desc"))
                        break

        # 更新语言标签
        if hasattr(self.window, 'language_content_layout'):
            if self.window.language_content_layout.count() > 0:
                language_widget = self.window.language_content_layout.itemAt(0).widget()
                if language_widget and language_widget.layout():
                    label = language_widget.layout().itemAt(0).widget()
                    if label and hasattr(label, 'setText'):
                        label.setText(self.window.language_manager.translate("settings_language_label"))

        # 更新字体设置容器
        font_header = self.window.font_container.layout().itemAt(0).widget()
        if font_header and font_header.layout():
            header_layout = font_header.layout()
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        if title and hasattr(title, 'setText'):
                            title.setText(self.window.language_manager.translate("settings_font"))
                        if desc and hasattr(desc, 'setText'):
                            desc.setText(self.window.language_manager.translate("settings_font_desc"))
                        break

        # 更新字体卡片
        self._update_bg_card(self.window.font_select_card, "font_select", "font_select_desc")
        self._update_bg_card(self.window.font_custom_card, "font_custom", "font_custom_desc")

        # 更新字体选择标签
        if hasattr(self.window, 'font_select_widget'):
            font_select_layout = self.window.font_select_widget.layout()
            if font_select_layout and font_select_layout.count() > 0:
                label = font_select_layout.itemAt(0).widget()
                if label and hasattr(label, 'setText'):
                    label.setText(self.window.language_manager.translate("font_select_label"))

        # 更新字体路径标签
        if hasattr(self.window, 'font_path_widget'):
            font_path_layout = self.window.font_path_widget.layout()
            if font_path_layout and font_path_layout.count() > 0:
                label = font_path_layout.itemAt(0).widget()
                if label and hasattr(label, 'setText'):
                    label.setText(self.window.language_manager.translate("font_custom_label"))

    def _update_settings_font(self, font_family):
        """更新设置页面的字体"""
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'

        # 更新设置页面标题
        settings_page = self.window.stack.widget(3)
        if settings_page and settings_page.layout():
            title = settings_page.layout().itemAt(0).widget()
            if title:
                title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:{font_family_quoted};font-weight:bold;")

        # 更新其他页面标题（主页没有标题，实例和下载页面的标题在 itemAt(0)）
        for i in [1, 2]:  # 实例页面和下载页面
            page = self.window.stack.widget(i)
            if page and page.layout():
                title = page.layout().itemAt(0).widget()
                if title and hasattr(title, 'setText'):
                    title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:{font_family_quoted};font-weight:bold;")

        # 更新外观设置容器的标题和描述
        if hasattr(self.window, 'appearance_container'):
            self._update_expandable_menu_font(self.window.appearance_container, font_family)

        # 更新语言设置容器的标题和描述
        if hasattr(self.window, 'language_container'):
            self._update_expandable_menu_font(self.window.language_container, font_family)

        # 更新字体设置容器的标题和描述
        if hasattr(self.window, 'font_container'):
            self._update_expandable_menu_font(self.window.font_container, font_family)

        # 更新所有卡片的标题和描述
        if hasattr(self.window, 'blur_card'):
            self._update_bg_card_font(self.window.blur_card, font_family)
        if hasattr(self.window, 'solid_card'):
            self._update_bg_card_font(self.window.solid_card, font_family)
        if hasattr(self.window, 'image_card'):
            self._update_bg_card_font(self.window.image_card, font_family)
        if hasattr(self.window, 'font_select_card'):
            self._update_bg_card_font(self.window.font_select_card, font_family)
        if hasattr(self.window, 'font_custom_card'):
            self._update_bg_card_font(self.window.font_custom_card, font_family)

        # 更新透明度标签
        if hasattr(self.window, 'opacity_widget'):
            opacity_layout = self.window.opacity_widget.layout()
            if opacity_layout and opacity_layout.count() > 0:
                header_layout = opacity_layout.itemAt(0)
                if header_layout and isinstance(header_layout, QHBoxLayout):
                    label = header_layout.itemAt(0).widget()
                    if label:
                        label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                    value_label = header_layout.itemAt(1).widget()
                    if value_label:
                        value_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")

        # 更新路径标签
        if hasattr(self.window, 'path_widget'):
            path_layout = self.window.path_widget.layout()
            if path_layout and path_layout.count() > 0:
                label = path_layout.itemAt(0).widget()
                if label:
                    label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                # 更新输入框（直接从 window 属性获取）
                if hasattr(self.window, 'path_input'):
                    padding = self._scale_size(6)
                    border_radius_input = self._scale_size(4)
                    self.window.path_input.setStyleSheet(
                        f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};}}")

        # 更新颜色标签
        if hasattr(self.window, 'color_widget'):
            color_layout = self.window.color_widget.layout()
            if color_layout and color_layout.count() > 0:
                label = color_layout.itemAt(0).widget()
                if label:
                    label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                # 更新输入框（直接从 window 属性获取）
                if hasattr(self.window, 'color_input'):
                    padding = self._scale_size(6)
                    border_radius_input = self._scale_size(4)
                    self.window.color_input.setStyleSheet(
                        f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};}}")

        # 更新字体选择标签
        if hasattr(self.window, 'font_select_widget'):
            font_select_layout = self.window.font_select_widget.layout()
            if font_select_layout and font_select_layout.count() > 0:
                label = font_select_layout.itemAt(0).widget()
                if label:
                    label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                # 更新 QComboBox 字体（直接从 window 属性获取）
                if hasattr(self.window, 'font_combo'):
                    self._update_combobox_font(self.window.font_combo, font_family_quoted)

        # 更新字体路径标签
        if hasattr(self.window, 'font_path_widget'):
            font_path_layout = self.window.font_path_widget.layout()
            if font_path_layout and font_path_layout.count() > 0:
                label = font_path_layout.itemAt(0).widget()
                if label:
                    label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                # 更新输入框（直接从 window 属性获取）
                if hasattr(self.window, 'font_path_input'):
                    padding = self._scale_size(6)
                    border_radius_input = self._scale_size(4)
                    self.window.font_path_input.setStyleSheet(
                        f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};}}")

        # 更新语言标签
        if hasattr(self.window, 'language_content_layout'):
            if self.window.language_content_layout.count() > 0:
                language_widget = self.window.language_content_layout.itemAt(0).widget()
                if language_widget and language_widget.layout():
                    label = language_widget.layout().itemAt(0).widget()
                    if label:
                        label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};")
                    # 更新语言 QComboBox 字体（直接从 window 属性获取）
                    if hasattr(self.window, 'language_combo'):
                        self._update_combobox_font(self.window.language_combo, font_family_quoted)

    def _update_combobox_font(self, combo_widget, font_family_quoted):
        """更新 QComboBox 的字体"""
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)
        combo_widget.setStyleSheet(
            f"QComboBox{{"
            f"background:rgba(0,0,0,0.3);"
            f"border:1px solid rgba(255,255,255,0.15);"
            f"border-radius:{border_radius}px;"
            f"padding:{padding}px;"
            f"color:rgba(255,255,255,0.95);"
            f"font-size:{self._scale_size(13)}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox:hover{{"
            f"background:rgba(0,0,0,0.4);"
            f"border:1px solid rgba(255,255,255,0.25);"
            f"}}"
            f"QComboBox:focus{{"
            f"background:rgba(0,0,0,0.5);"
            f"border:1px solid rgba(100,150,255,0.6);"
            f"}}"
            f"QComboBox:on{{"
            f"padding-top:{padding - 1}px;"
            f"padding-bottom:{padding - 1}px;"
            f"}}"
            f"QComboBox::drop-down{{"
            f"border:none;"
            f"width:28px;"
            f"background:transparent;"
            f"}}"
            # f"QComboBox::down-arrow{{"
            # f"image:url(svg/x-diamond.svg);"
            # f"width:12px;"
            # f"height:12px;"
            # f"}}"
            f"QComboBox QAbstractItemView{{"
            f"background:rgba(0,0,0,0.5);"
            f"border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:{border_radius}px;"
            f"selection-background-color:rgba(255,255,255,0.15);"
            f"selection-color:white;"
            f"outline:none;"
            f"padding:{self._scale_size(2)}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox QAbstractItemView::item{{"
            f"height:{self._scale_size(28)}px;"
            f"padding:{self._scale_size(6)}px {self._scale_size(8)}px;"
            f"color:rgba(255,255,255,0.85);"
            f"border-radius:{border_radius - 1}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover{{"
            f"background:rgba(255,255,255,0.1);"
            f"}}"
            f"QComboBox QAbstractItemView::item:selected{{"
            f"background:rgba(255,255,255,0.15);"
            f"color:white;"
            f"}}"
            f"QComboBox QScrollBar:vertical{{"
            f"background:rgba(255,255,255,0.05);"
            f"width:8px;"
            f"margin:0px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical{{"
            f"background:rgba(255,255,255,0.3);"
            f"min-height:20px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical:hover{{"
            f"background:rgba(255,255,255,0.5);"
            f"}}"
            f"QComboBox QScrollBar::add-line:vertical,"
            f"QComboBox QScrollBar::sub-line:vertical{{"
            f"border:none;"
            f"background:none;"
            f"}}"
            f"QComboBox QScrollBar::add-page:vertical,"
            f"QComboBox QScrollBar::sub-page:vertical{{"
            f"background:none;"
            f"}}"
        )

    def _update_expandable_menu_font(self, container, font_family):
        """更新可展开菜单的字体"""
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'

        header = container.layout().itemAt(0).widget()
        if header and header.layout():
            header_layout = header.layout()
            # 查找文本布局
            for i in range(header_layout.count()):
                item = header_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    # 第一个是标题，第二个是描述
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        if title and hasattr(title, 'setStyleSheet'):
                            title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:{font_family_quoted};background:transparent;")
                        if desc and hasattr(desc, 'setStyleSheet'):
                            desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:{font_family_quoted};background:transparent;")
                        break

    def _update_bg_card_font(self, card, font_family):
        """更新卡片字体的样式"""
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'

        if not card or not card.layout():
            return

        card_layout = card.layout()
        if card_layout.count() >= 2:
            text_container = card_layout.itemAt(1).layout()
            if text_container and text_container.count() >= 2:
                title = text_container.itemAt(0).widget()
                desc = text_container.itemAt(1).widget()
                if title and hasattr(title, 'setStyleSheet'):
                    title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:{font_family_quoted};background:transparent;")
                if desc and hasattr(desc, 'setStyleSheet'):
                    desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:{font_family_quoted};background:transparent;")

    def _update_bg_card(self, card, title_key, desc_key):
        """更新背景卡片的文本"""
        if not card or not card.layout():
            return

        card_layout = card.layout()
        if card_layout.count() >= 2:
            text_container = card_layout.itemAt(1).layout()
            if text_container and text_container.count() >= 2:
                title = text_container.itemAt(0).widget()
                desc = text_container.itemAt(1).widget()
                if title and hasattr(title, 'setText'):
                    title.setText(self.window.language_manager.translate(title_key))
                if desc and hasattr(desc, 'setText'):
                    desc.setText(self.window.language_manager.translate(desc_key))

    def update_combobox_opacity(self, opacity_rgba):
        """更新下拉框的透明度"""
        # 更新字体选择下拉框
        if hasattr(self.window, 'font_combo'):
            self._update_single_combobox_opacity(self.window.font_combo, opacity_rgba)
        # 更新语言选择下拉框
        if hasattr(self.window, 'language_combo'):
            self._update_single_combobox_opacity(self.window.language_combo, opacity_rgba)

    def _update_single_combobox_opacity(self, combo, opacity_rgba):
        """更新单个下拉框的透明度"""
        # 获取当前字体
        font_family = self._get_font_family()
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'

        padding = self._scale_size(6)
        border_radius = self._scale_size(4)

        combo.setStyleSheet(
            f"QComboBox{{"
            f"background:rgba(0,0,0,0.3);"
            f"border:1px solid rgba(255,255,255,0.15);"
            f"border-radius:{border_radius}px;"
            f"padding:{padding}px;"
            f"color:rgba(255,255,255,0.95);"
            f"font-size:{self._scale_size(13)}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox:hover{{"
            f"background:rgba(0,0,0,0.4);"
            f"border:1px solid rgba(255,255,255,0.25);"
            f"}}"
            f"QComboBox:focus{{"
            f"background:rgba(0,0,0,0.5);"
            f"border:1px solid rgba(100,150,255,0.6);"
            f"}}"
            f"QComboBox:on{{"
            f"padding-top:{padding - 1}px;"
            f"padding-bottom:{padding - 1}px;"
            f"}}"
            f"QComboBox::drop-down{{"
            f"border:none;"
            f"width:28px;"
            f"background:transparent;"
            f"}}"
            # f"QComboBox::down-arrow{{"
            # f"image:url(svg/x-diamond.svg);"
            # f"width:12px;"
            # f"height:12px;"
            # f"}}"
            f"QComboBox QAbstractItemView{{"
            f"background:rgba(0,0,0,{opacity_rgba:.2f});"
            f"border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:{border_radius}px;"
            f"selection-background-color:rgba(255,255,255,0.15);"
            f"selection-color:white;"
            f"outline:none;"
            f"padding:{self._scale_size(2)}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox QAbstractItemView::item{{"
            f"height:{self._scale_size(28)}px;"
            f"padding:{self._scale_size(6)}px {self._scale_size(8)}px;"
            f"color:rgba(255,255,255,0.85);"
            f"border-radius:{border_radius - 1}px;"
            f"font-family:{font_family_quoted};"
            f"}}"
            f"QComboBox QAbstractItemView::item:hover{{"
            f"background:rgba(255,255,255,0.1);"
            f"}}"
            f"QComboBox QAbstractItemView::item:selected{{"
            f"background:rgba(255,255,255,0.15);"
            f"color:white;"
            f"}}"
            f"QComboBox QScrollBar:vertical{{"
            f"background:rgba(255,255,255,0.05);"
            f"width:8px;"
            f"margin:0px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical{{"
            f"background:rgba(255,255,255,0.3);"
            f"min-height:20px;"
            f"border-radius:4px;"
            f"}}"
            f"QComboBox QScrollBar::handle:vertical:hover{{"
            f"background:rgba(255,255,255,0.5);"
            f"}}"
            f"QComboBox QScrollBar::add-line:vertical,"
            f"QComboBox QScrollBar::sub-line:vertical{{"
            f"border:none;"
            f"background:none;"
            f"}}"
            f"QComboBox QScrollBar::add-page:vertical,"
            f"QComboBox QScrollBar::sub-page:vertical{{"
            f"background:none;"
            f"}}"
        )
