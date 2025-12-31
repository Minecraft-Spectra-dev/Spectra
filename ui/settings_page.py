"""设置页面模块

提供设置页面的创建功能
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                             QPushButton, QScrollArea, QSlider, QLineEdit)
from PyQt6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsPageBuilder:
    """设置页面构建器"""

    def __init__(self, builder):
        self.builder = builder

    def create_config_page(self):
        """创建设置页面"""
        from PyQt6.QtWidgets import QScrollArea

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(
            self.builder._scale_size(20), self.builder._scale_size(10),
            self.builder._scale_size(20), self.builder._scale_size(20)
        )
        pl.setSpacing(self.builder._scale_size(15))

        title = QLabel()
        title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(20)}px;"
            f"font-family:'{self.builder._get_font_family()}';font-weight:bold;"
        )
        self.builder.text_renderer.register_widget(title, "page_settings", group="settings_page")
        title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(20)}px;"
            f"font-family:'{self.builder._get_font_family()}';font-weight:bold;"
        )
        pl.addWidget(title)

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(self.builder._get_scroll_area_stylesheet())

        # 滚动内容区域
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(self.builder._scale_size(15))
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 外观设置容器
        self.builder.window.appearance_container = self._create_expandable_menu(
            "settings_appearance",
            "settings_appearance_desc",
            "svg/palette.svg", "svg/palette-fill.svg",
            content_attr="appearance"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.builder.window.appearance_container)

        self.builder.window.appearance_content = self.builder.window.appearance_container.layout().itemAt(1).widget()

        # 纯色背景卡片
        self.builder.window.solid_card = self._create_bg_card(
            "background_solid",
            "background_solid_desc",
            self.builder.window.config.get("background_mode") == "blur" or self.builder.window.config.get("background_mode") == "solid",
            lambda: self.builder.window.set_background("solid")
        )
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.solid_card)

        # 颜色选择区域
        self._create_color_picker()
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.color_widget)

        # 不透明度滑块
        self._create_opacity_slider()
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.opacity_widget)

        # 图片背景卡片
        self.builder.window.image_card = self._create_bg_card(
            "background_image",
            "background_image_desc",
            self.builder.window.config.get("background_mode") == "image",
            lambda: self.builder.window.set_background("image")
        )
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.image_card)

        # 路径输入区域
        self._create_path_input()
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.path_widget)

        # 背景模糊开关
        self._create_blur_toggle_option()
        self.builder.window.appearance_content_layout.addWidget(self.builder.window.blur_toggle_widget)

        self.builder.window.appearance_content.setVisible(False)

        # 语言设置容器
        self.builder.window.language_container = self._create_expandable_menu(
            "settings_language",
            "settings_language_desc",
            "svg/translate.svg", "svg/file-earmark-font.svg",
            toggle_handler=self.builder.window.toggle_language_menu,
            content_attr="language"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.builder.window.language_container)

        self.builder.window.language_content = self.builder.window.language_container.layout().itemAt(1).widget()

        # 语言卡片
        self._create_language_card()

        self.builder.window.language_content.setVisible(False)

        # 字体设置容器
        self.builder.window.font_container = self._create_expandable_menu(
            "settings_font",
            "settings_font_desc",
            "svg/type.svg", "svg/file-earmark-font.svg",
            toggle_handler=self.builder.window.toggle_font_menu,
            content_attr="font"
        )
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.builder.window.font_container)

        self.builder.window.font_content = self.builder.window.font_container.layout().itemAt(1).widget()

        # 选择字体卡片
        self.builder.window.font_select_card = self._create_bg_card(
            "font_select",
            "font_select_desc",
            self.builder.window.config.get("font_mode") == 0,
            lambda: self.builder.window.set_font_mode(0)
        )
        self.builder.window.font_content_layout.addWidget(self.builder.window.font_select_card)

        # 字体选择下拉框区域
        self._create_font_select_widget()
        self.builder.window.font_content_layout.addWidget(self.builder.window.font_select_widget)

        # 自定义字体卡片
        self.builder.window.font_custom_card = self._create_bg_card(
            "font_custom",
            "font_custom_desc",
            self.builder.window.config.get("font_mode") == 1,
            lambda: self.builder.window.set_font_mode(1)
        )
        self.builder.window.font_content_layout.addWidget(self.builder.window.font_custom_card)

        # 自定义字体路径输入区域
        self._create_font_path_widget()
        self.builder.window.font_content_layout.addWidget(self.builder.window.font_path_widget)

        self.builder.window.font_content.setVisible(False)

        # 版本隔离选项
        self._create_version_isolation_option()
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.builder.window.version_isolation_widget)

        # 开发控制台选项
        self._create_dev_console_option()
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.builder.window.dev_console_widget)

        return page

    def _create_expandable_menu(self, title_key, desc_key, icon_path=None, icon_path_active=None,
                                  toggle_handler=None, content_attr="appearance"):
        """创建可展开菜单"""
        container = QWidget()
        container.setStyleSheet("background:rgba(255,255,255,0.08);border-radius:8px;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from widgets import CardButton
        from utils import load_svg_icon, scale_icon_for_display

        header = CardButton()
        header.setFixedHeight(self.builder._scale_size(70))
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        if toggle_handler:
            header.clicked.connect(toggle_handler)
        else:
            header.clicked.connect(self.builder.window.toggle_appearance_menu)

        border_radius = self.builder._scale_size(8)
        header.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"border-top-left-radius:{border_radius}px;border-top-right-radius:{border_radius}px;}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.05);}}"
            f"QPushButton:pressed{{background:rgba(255,255,255,0.02);}}"
        )

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        header_layout.setSpacing(self.builder._scale_size(12))

        icon_label = None
        if icon_path:
            icon_label = QLabel()
            icon_label.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setStyleSheet("background:transparent;")
            icon_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
            icon_label.setObjectName("menu_icon")

            icon_pixmap = load_svg_icon(icon_path, self.builder.dpi_scale)
            if icon_pixmap:
                icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.builder.dpi_scale))

            header_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self.builder._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel()
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)
        self.builder.text_renderer.register_widget(title_lbl, title_key, group="settings_page")

        desc_lbl = QLabel()
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)
        self.builder.text_renderer.register_widget(desc_lbl, desc_key, group="settings_page")

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

        setattr(self.builder.window, f"{content_attr}_content_layout", content_layout)
        setattr(self.builder.window, f"{content_attr}_icon_path", icon_path)
        setattr(self.builder.window, f"{content_attr}_icon_path_active", icon_path_active)
        setattr(self.builder.window, f"{content_attr}_icon_label", icon_label)

        return container

    def _create_bg_card(self, title_key, desc_key, selected, handler):
        """创建背景卡片"""
        from widgets import CardButton

        card = CardButton()
        card.setFixedHeight(self.builder._scale_size(70))
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(handler)

        style = "background:rgba(255,255,255,0.15);" if selected else "background:rgba(255,255,255,0.05);"
        card.setStyleSheet(
            f"QPushButton{{{style}border:none;border-radius:0px;}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.1);}}"
            f"QPushButton:pressed{{background:rgba(255,255,255,0.05);}}"
        )

        layout = QHBoxLayout(card)
        layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        layout.setSpacing(self.builder._scale_size(12))

        check_label = QLabel()
        check_label.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
        check_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        check_label.setStyleSheet("background:transparent;")
        check_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        if selected:
            from utils import load_svg_icon, scale_icon_for_display
            check_pixmap = load_svg_icon("svg/check-lg.svg", self.builder.dpi_scale)
            if check_pixmap:
                check_label.setPixmap(scale_icon_for_display(check_pixmap, 20, self.builder.dpi_scale))

        layout.addWidget(check_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self.builder._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel()
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)
        self.builder.text_renderer.register_widget(title_lbl, title_key, group="settings_page")

        desc_lbl = QLabel()
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)
        self.builder.text_renderer.register_widget(desc_lbl, desc_key, group="settings_page")

        layout.addLayout(text_layout)
        layout.addStretch()

        card.check_label = check_label
        return card

    def _create_opacity_slider(self):
        """创建不透明度滑块"""
        self.builder.window.opacity_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        self.builder.window.opacity_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        opacity_layout = QVBoxLayout(self.builder.window.opacity_widget)
        opacity_layout.setContentsMargins(
            self.builder._scale_size(50), self.builder._scale_size(8),
            self.builder._scale_size(15), self.builder._scale_size(8)
        )
        opacity_layout.setSpacing(self.builder._scale_size(4))

        opacity_header_layout = QHBoxLayout()
        opacity_label = QLabel()
        opacity_label.setStyleSheet(
            f"color:rgba(255,255,255,0.8);font-size:{self.builder._scale_size(13)}px;"
            f"font-family:'{self.builder._get_font_family()}';"
        )
        self.builder.text_renderer.register_widget(opacity_label, "opacity", group="settings_page")
        opacity_label.setStyleSheet(
            f"color:rgba(255,255,255,0.8);font-size:{self.builder._scale_size(13)}px;"
            f"font-family:'{self.builder._get_font_family()}';"
        )

        opacity_value = QLabel()
        # 统一的百分比计算：10-255 映射到 0%-100%
        opacity_percent = int((self.builder.window.config.get("blur_opacity", 150) - 10) / (255 - 10) * 100)
        opacity_value.setText(str(opacity_percent) + "%")
        opacity_value.setStyleSheet(
            f"color:rgba(255,255,255,0.8);font-size:{self.builder._scale_size(13)}px;"
            f"font-family:'{self.builder._get_font_family()}';"
        )
        self.builder.window.opacity_value_label = opacity_value

        opacity_header_layout.addWidget(opacity_label)
        opacity_header_layout.addStretch()
        opacity_header_layout.addWidget(opacity_value)
        opacity_layout.addLayout(opacity_header_layout)

        self.builder.text_renderer.register_widget(opacity_label, "opacity", group="settings_page")

        from PyQt6.QtWidgets import QSlider
        self.builder.window.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.builder.window.opacity_slider.setRange(10, 255)
        self.builder.window.opacity_slider.setValue(self.builder.window.config.get("blur_opacity", 150))

        from styles import SLIDER_STYLE
        self.builder.window.opacity_slider.setStyleSheet(SLIDER_STYLE)

        self.builder.window.opacity_slider.valueChanged.connect(self.builder.window.on_opacity_preview)
        self.builder.window.opacity_slider.sliderReleased.connect(self.builder.window.on_opacity_released)

        opacity_layout.addWidget(self.builder.window.opacity_slider)

        # 不透明度滑块只在纯色背景模式下显示
        self.builder.window.opacity_widget.setVisible(self.builder.window.config.get("background_mode") == "solid")

    def _create_path_input(self):
        """创建路径输入区域"""
        self.builder.window.path_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        self.builder.window.path_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        path_layout = QHBoxLayout(self.builder.window.path_widget)
        path_layout.setContentsMargins(
            self.builder._scale_size(35), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        path_layout.setSpacing(self.builder._scale_size(10))

        path_label = self.builder._create_label_with_style("bg_image_path")
        path_layout.addWidget(path_label)

        self.builder.text_renderer.register_widget(path_label, "bg_image_path", group="settings_page")

        self.builder.window.path_input = QLineEdit()
        self.builder.window.path_input.setText(self.builder.window.config.get("background_image_path", ""))
        self.builder.window.path_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.window.path_input.editingFinished.connect(self.builder.window.on_path_changed)
        path_layout.addWidget(self.builder.window.path_input, 1)

        # 浏览按钮
        from widgets import ClickableLabel
        from utils import load_svg_icon, scale_icon_for_display
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(self.builder.window.choose_background_image)
        folder_pixmap = load_svg_icon("svg/folder2.svg", self.builder.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.builder.dpi_scale))
        path_layout.addWidget(browse_btn)

        self.builder.window.path_widget.setVisible(self.builder.window.config.get("background_mode") == "image")

    def _create_color_picker(self):
        """创建颜色选择器"""
        from PyQt6.QtCore import QSize

        self.builder.window.color_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        self.builder.window.color_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        color_layout = QHBoxLayout(self.builder.window.color_widget)
        color_layout.setContentsMargins(
            self.builder._scale_size(50), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        color_layout.setSpacing(self.builder._scale_size(10))

        color_label = self.builder._create_label_with_style("bg_color")
        color_layout.addWidget(color_label)

        self.builder.text_renderer.register_widget(color_label, "bg_color", group="settings_page")

        self.builder.window.color_input = QLineEdit()
        self.builder.window.color_input.setText(self.builder.window.config.get("background_color", "#00000000"))
        self.builder.window.color_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.window.color_input.editingFinished.connect(self.builder.window.on_color_changed)
        color_layout.addWidget(self.builder.window.color_input, 1)

        # 颜色选择按钮
        from PyQt6.QtGui import QColor
        color_btn = QPushButton()
        color_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
        border_radius_btn = self.builder._scale_size(4)
        color_str = self.builder.window.config.get("background_color", "#00000000")
        bg_color = self._parse_color_to_hex(color_str)
        color_btn.setStyleSheet(
            f"QPushButton{{background:{bg_color};border:1px solid rgba(255,255,255,0.3);"
            f"border-radius:{border_radius_btn}px;}}"
            f"QPushButton:hover{{background:{bg_color};border:1px solid rgba(255,255,255,0.5);}}"
        )
        color_btn.clicked.connect(self.builder.window.choose_background_color)
        color_layout.addWidget(color_btn)
        self.builder.window.color_btn = color_btn

        self.builder.window.color_widget.setVisible(self.builder.window.config.get("background_mode") == "solid")

    def _parse_color_to_hex(self, color_str):
        """解析颜色字符串并返回十六进制格式"""
        from PyQt6.QtGui import QColor
        color = QColor(color_str)
        if color.isValid():
            return color.name(QColor.NameFormat.HexArgb)
        if len(color_str) == 7 and color_str.startswith('#'):
            return QColor(f"#FF{color_str[1:]}").name(QColor.NameFormat.HexArgb)
        return "#00000000"

    def _create_font_select_widget(self):
        """创建字体选择部件"""
        from PyQt6.QtGui import QFontDatabase

        self.builder.window.font_select_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        self.builder.window.font_select_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        font_select_layout = QHBoxLayout(self.builder.window.font_select_widget)
        font_select_layout.setContentsMargins(
            self.builder._scale_size(35), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        font_select_layout.setSpacing(self.builder._scale_size(10))

        font_select_label = QLabel()
        font_select_label.setStyleSheet(
            f"color:rgba(255,255,255,0.8);font-size:{self.builder._scale_size(13)}px;"
            f"font-family:'{self.builder._get_font_family()}';"
        )
        font_select_layout.addWidget(font_select_label)

        self.builder.text_renderer.register_widget(font_select_label, "font_select_label", group="settings_page")

        font_select_layout.addStretch()

        self.builder.window.font_combo = QComboBox()
        self._setup_font_combobox(self.builder.window.font_combo)
        font_select_layout.addWidget(self.builder.window.font_combo)

        return self.builder.window.font_select_widget

    def _setup_font_combobox(self, combo):
        """设置字体下拉框"""
        from PyQt6.QtGui import QFontDatabase

        combo.setFixedHeight(self.builder._scale_size(32))
        combo.setFixedWidth(self.builder._scale_size(200))
        combo.setMaxVisibleItems(8)

        padding = self.builder._scale_size(6)
        border_radius = self.builder._scale_size(4)

        # 获取当前下拉框透明度（主页透明度 + 50）
        blur_opacity = self.builder.window.config.get("blur_opacity", 150)
        dropdown_opacity_value = min(255, blur_opacity + 50)
        dropdown_opacity_rgba = dropdown_opacity_value / 255.0

        escaped_font = self.builder._get_font_family().replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'

        combo.setStyleSheet(
            f"QComboBox{{"
            f"background:rgba(0,0,0,0.3);"
            f"border:1px solid rgba(255,255,255,0.15);"
            f"border-radius:{border_radius}px;"
            f"padding:{padding}px;"
            f"color:rgba(255,255,255,0.95);"
            f"font-size:{self.builder._scale_size(13)}px;"
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
            f"QComboBox::drop-down{{"
            f"border:none;"
            f"width:28px;"
            f"background:transparent;"
            f"}}"
            f"QComboBox QAbstractItemView{{"
            f"background:rgba(0,0,0,{dropdown_opacity_rgba:.2f});"
            f"border:1px solid rgba(255,255,255,0.1);"
            f"border-radius:{border_radius}px;"
            f"selection-background-color:rgba(255,255,255,0.15);"
            f"selection-color:white;"
            f"outline:none;"
            f"padding:{self.builder._scale_size(2)}px;"
            f"}}"
            f"QComboBox QAbstractItemView::item{{"
            f"height:{self.builder._scale_size(28)}px;"
            f"padding:{self.builder._scale_size(6)}px {self.builder._scale_size(8)}px;"
            f"color:rgba(255,255,255,0.85);"
            f"border-radius:{border_radius - 1}px;"
            f"font-family:{font_family_quoted};"
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
        )

        # 获取系统字体
        font_families = QFontDatabase.families()

        # 添加常用字体到前面
        common_fonts = ["Microsoft YaHei UI", "SimHei", "Arial", "Segoe UI", "Helvetica"]
        added_fonts = set()

        for font in common_fonts:
            if font in font_families:
                combo.addItem(font)
                added_fonts.add(font)

        for font in font_families:
            if font not in added_fonts:
                combo.addItem(font)

        current_font_family = self.builder.window.config.get("custom_font_family", "Microsoft YaHei UI")
        font_index = combo.findText(current_font_family)
        if font_index >= 0:
            combo.setCurrentIndex(font_index)

        combo.currentTextChanged.connect(self.builder.window.on_font_family_changed)

    def _create_font_path_widget(self):
        """创建字体路径部件"""
        self.builder.window.font_path_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        self.builder.window.font_path_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        font_path_layout = QHBoxLayout(self.builder.window.font_path_widget)
        font_path_layout.setContentsMargins(
            self.builder._scale_size(35), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        font_path_layout.setSpacing(self.builder._scale_size(10))

        font_path_label = self.builder._create_label_with_style("font_custom_label")
        font_path_layout.addWidget(font_path_label)

        self.builder.text_renderer.register_widget(font_path_label, "font_custom_label", group="settings_page")

        # 创建输入框
        from PyQt6.QtWidgets import QLineEdit
        self.builder.window.font_path_input = QLineEdit()
        self.builder.window.font_path_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.window.font_path_input.editingFinished.connect(self.builder.window.on_font_path_changed)
        font_path_layout.addWidget(self.builder.window.font_path_input, 1)

        # 浏览按钮
        from widgets import ClickableLabel
        from utils import load_svg_icon, scale_icon_for_display
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(self.builder.window.choose_font_file)
        folder_pixmap = load_svg_icon("svg/folder2.svg", self.builder.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.builder.dpi_scale))
        font_path_layout.addWidget(browse_btn)

        self.builder.window.font_path_widget.setVisible(self.builder.window.config.get("font_mode") == 1)

        return self.builder.window.font_path_widget

    def _create_language_card(self):
        """创建语言选择卡片"""
        language_widget = QWidget()
        border_radius = self.builder._scale_size(8)
        language_widget.setStyleSheet(
            f"background:rgba(255,255,255,0);"
            f"border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;"
        )
        language_layout = QHBoxLayout(language_widget)
        language_layout.setContentsMargins(
            self.builder._scale_size(35), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        language_layout.setSpacing(self.builder._scale_size(10))

        language_label = QLabel()
        language_label.setStyleSheet(
            f"color:rgba(255,255,255,0.8);font-size:{self.builder._scale_size(13)}px;"
            f"font-family:'{self.builder._get_font_family()}';"
        )
        language_layout.addWidget(language_label)

        self.builder.text_renderer.register_widget(language_label, "settings_language_label", group="settings_page")

        language_layout.addStretch()

        self.builder.window.language_combo = QComboBox()
        self.builder._setup_combobox(self.builder.window.language_combo, width=150, max_items=5)

        # 添加语言选项
        languages = self.builder.window.language_manager.get_all_languages()
        for lang_code, display_name in languages:
            self.builder.window.language_combo.addItem(display_name, lang_code)

        # 设置当前语言
        current_lang = self.builder.window.language_manager.get_language()
        for i in range(self.builder.window.language_combo.count()):
            if self.builder.window.language_combo.itemData(i) == current_lang:
                self.builder.window.language_combo.setCurrentIndex(i)
                break

        self.builder.window.language_combo.currentIndexChanged.connect(self.builder.window.change_language)
        language_layout.addWidget(self.builder.window.language_combo)

        self.builder.window.language_content_layout.addWidget(language_widget)

        return language_widget

    def _create_blur_toggle_option(self):
        """创建背景模糊开关选项"""
        from .components import ToggleSwitch
        from utils import load_svg_icon, scale_icon_for_display

        blur_enabled = self.builder.window.config.get("background_blur_enabled", True)

        self.builder.window.blur_toggle_widget = QWidget()
        self.builder.window.blur_toggle_widget.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        blur_toggle_layout = QHBoxLayout(self.builder.window.blur_toggle_widget)
        blur_toggle_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        blur_toggle_layout.setSpacing(self.builder._scale_size(12))

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self.builder._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel()
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)
        self.builder.text_renderer.register_widget(title_lbl, "background_blur_enabled", group="settings_page")
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel()
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)
        self.builder.text_renderer.register_widget(desc_lbl, "background_blur_enabled_desc", group="settings_page")
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)

        blur_toggle_layout.addLayout(text_layout)
        blur_toggle_layout.addStretch()

        self.builder.window.blur_toggle = ToggleSwitch(checked=blur_enabled, dpi_scale=self.builder.dpi_scale)
        self.builder.window.blur_toggle.setCallback(lambda checked: self.builder.window.toggle_blur_enabled(checked))
        blur_toggle_layout.addWidget(self.builder.window.blur_toggle)

        self.builder.window.blur_toggle_widget.setVisible(self.builder.window.config.get("background_mode") == "solid")

    def _create_version_isolation_option(self):
        """创建版本隔离选项"""
        from .components import ToggleSwitch
        from utils import load_svg_icon, scale_icon_for_display

        version_isolation_enabled = self.builder.window.config.get("version_isolation", True)

        self.builder.window.version_isolation_widget = QWidget()
        self.builder.window.version_isolation_widget.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        version_isolation_layout = QHBoxLayout(self.builder.window.version_isolation_widget)
        version_isolation_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        version_isolation_layout.setSpacing(self.builder._scale_size(12))

        # 盒子图标
        box_icon = load_svg_icon("svg/box-fill.svg", self.builder.dpi_scale)
        icon_label = QLabel()
        icon_label.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if box_icon:
            icon_label.setPixmap(scale_icon_for_display(box_icon, 20, self.builder.dpi_scale))
        version_isolation_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self.builder._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel()
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)
        self.builder.text_renderer.register_widget(title_lbl, "version_isolation", group="settings_page")
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel()
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)
        self.builder.text_renderer.register_widget(desc_lbl, "version_isolation_desc", group="settings_page")
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)

        version_isolation_layout.addLayout(text_layout)
        version_isolation_layout.addStretch()

        self.builder.window.version_isolation_toggle = ToggleSwitch(checked=version_isolation_enabled, dpi_scale=self.builder.dpi_scale)
        self.builder.window.version_isolation_toggle.setCallback(lambda checked: self.builder.window.toggle_version_isolation(checked))
        version_isolation_layout.addWidget(self.builder.window.version_isolation_toggle)

    def _create_dev_console_option(self):
        """创建开发控制台选项"""
        from .components import ToggleSwitch
        from utils import load_svg_icon, scale_icon_for_display

        dev_console_enabled = self.builder.window.config.get("dev_console_enabled", False)

        self.builder.window.dev_console_widget = QWidget()
        self.builder.window.dev_console_widget.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        dev_console_layout = QHBoxLayout(self.builder.window.dev_console_widget)
        dev_console_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        dev_console_layout.setSpacing(self.builder._scale_size(12))

        # 终端图标
        console_icon = load_svg_icon("svg/terminal.svg", self.builder.dpi_scale)
        icon_label = QLabel()
        icon_label.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if console_icon:
            icon_label.setPixmap(scale_icon_for_display(console_icon, 20, self.builder.dpi_scale))
        dev_console_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(self.builder._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel()
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)
        self.builder.text_renderer.register_widget(title_lbl, "dev_console", group="settings_page")
        title_lbl.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel()
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)
        self.builder.text_renderer.register_widget(desc_lbl, "dev_console_desc", group="settings_page")
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        text_layout.addWidget(desc_lbl)

        dev_console_layout.addLayout(text_layout)
        dev_console_layout.addStretch()

        self.builder.window.dev_console_toggle = ToggleSwitch(checked=dev_console_enabled, dpi_scale=self.builder.dpi_scale)
        self.builder.window.dev_console_toggle.setCallback(lambda checked: self.builder.window.toggle_dev_console(checked))
        dev_console_layout.addWidget(self.builder.window.dev_console_toggle)
