"""UI构建器"""

import os
import sys
import logging

logger = logging.getLogger(__name__)

from PyQt6.QtCore import Qt, QEvent
from PyQt6.QtGui import QColor, QPixmap, QIcon, QFontDatabase
from PyQt6.QtWidgets import (QColorDialog, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSlider, QVBoxLayout, QWidget,
                             QComboBox)

from styles import SLIDER_STYLE, STYLE_BTN, STYLE_ICON
from utils import load_svg_icon, scale_icon_for_display
from widgets import (CardButton, ClickableLabel, JellyButton,
                      get_current_font, make_transparent, set_current_font,
                      TextRenderer, ModrinthResultCard)


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
            bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self._get_dpi_scale())
            if bookmark_pixmap:
                self._bookmark_btn.setIcon(QIcon(scale_icon_for_display(bookmark_pixmap, 16, self._get_dpi_scale())))
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


class UIBuilder:
    def __init__(self, window):
        self.window = window
        self.dpi_scale = getattr(window, 'dpi_scale', 1.0)
        # 获取 window 的 text_renderer，如果没有则创建一个新的
        self.text_renderer = getattr(window, 'text_renderer', None)
        if self.text_renderer is None:
            self.text_renderer = TextRenderer(getattr(window, 'language_manager', None))
            self.text_renderer.set_dpi_scale(self.dpi_scale)

    def _scale_size(self, size):
        return int(size * self.dpi_scale)

    def _get_font_family(self):
        """获取当前字体系列"""
        return get_current_font()

    def _get_scroll_area_stylesheet(self):
        """获取统一的滚动区域样式表"""
        return """
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
        """

    def _create_scroll_area(self, parent=None):
        """创建统一的滚动区域"""
        from PyQt6.QtWidgets import QScrollArea
        scroll_area = QScrollArea(parent)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet(self._get_scroll_area_stylesheet())
        return scroll_area

    def _create_scroll_content(self, margins=(0, 10, 0, 0), spacing=15):
        """创建滚动内容容器"""
        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(
            self._scale_size(margins[0]),
            self._scale_size(margins[1]),
            self._scale_size(margins[2]),
            self._scale_size(margins[3])
        )
        layout.setSpacing(self._scale_size(spacing))
        return content, layout

    def _create_page_title(self, text):
        """创建页面标题"""
        title = QLabel(text)
        title.setStyleSheet(
            f"color:white;font-size:{self._scale_size(20)}px;font-family:'{self._get_font_family()}';font-weight:bold;"
        )
        return title

    def _get_lineedit_stylesheet(self, font_family=None):
        """获取统一的LineEdit样式表"""
        if font_family is None:
            font_family = self._get_font_family()
        escaped_font = font_family.replace("\\\\", "\\\\\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)
        return f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};}}"

    def _create_label_with_style(self, text, font_size=13, color="rgba(255,255,255,0.8)"):
        """创建带统一样式的标签"""
        label = QLabel(text)
        label.setStyleSheet(
            f"color:{color};font-size:{self._scale_size(font_size)}px;font-family:'{self._get_font_family()}';"
        )
        return label

    def _get_combobox_stylesheet(self, opacity_rgba=None, font_family=None):
        """生成统一的 QComboBox 样式表"""
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)
        
        # 使用传入的字体，或获取当前字体
        if font_family is None:
            font_family = self._get_font_family()
        
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\\\", "\\\\\\\\").replace("'", "\\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'
        
        # 计算透明度
        if opacity_rgba is None:
            blur_opacity = self.window.config.get("blur_opacity", 150)
            opacity_value = min(255, blur_opacity + 50)
            opacity_rgba = opacity_value / 255.0
        else:
            opacity_rgba = opacity_rgba

        return f"""QComboBox{{
            background:rgba(0,0,0,0.3);
            border:1px solid rgba(255,255,255,0.15);
            border-radius:{border_radius}px;
            padding:{padding}px;
            color:rgba(255,255,255,0.95);
            font-size:{self._scale_size(13)}px;
            font-family:{font_family_quoted};
        }}
        QComboBox:hover{{
            background:rgba(0,0,0,0.4);
            border:1px solid rgba(255,255,255,0.25);
        }}
        QComboBox:focus{{
            background:rgba(0,0,0,0.5);
            border:1px solid rgba(100,150,255,0.6);
        }}
        QComboBox:on{{
            padding-top:{padding - 1}px;
            padding-bottom:{padding - 1}px;
        }}
        QComboBox::drop-down{{
            border:none;
            width:28px;
            background:transparent;
        }}
        QComboBox QAbstractItemView{{
            background:rgba(0,0,0,{opacity_rgba:.2f});
            border:1px solid rgba(255,255,255,0.1);
            border-radius:{border_radius}px;
            selection-background-color:rgba(255,255,255,0.15);
            selection-color:white;
            outline:none;
            padding:{self._scale_size(2)}px;
            font-family:{font_family_quoted};
        }}
        QComboBox QAbstractItemView::item{{
            height:{self._scale_size(28)}px;
            padding:{self._scale_size(6)}px {self._scale_size(8)}px;
            color:rgba(255,255,255,0.85);
            border-radius:{border_radius - 1}px;
            font-family:{font_family_quoted};
        }}
        QComboBox QAbstractItemView::item:hover{{
            background:rgba(255,255,255,0.1);
        }}
        QComboBox QAbstractItemView::item:selected{{
            background:rgba(255,255,255,0.15);
            color:white;
        }}
        QComboBox QScrollBar:vertical{{
            background:rgba(255,255,255,0.05);
            width:8px;
            margin:0px;
            border-radius:4px;
        }}
        QComboBox QScrollBar::handle:vertical{{
            background:rgba(255,255,255,0.3);
            min-height:20px;
            border-radius:4px;
        }}
        QComboBox QScrollBar::handle:vertical:hover{{
            background:rgba(255,255,255,0.5);
        }}
        QComboBox QScrollBar::add-line:vertical,
        QComboBox QScrollBar::sub-line:vertical{{
            border:none;
            background:none;
        }}
        QComboBox QScrollBar::add-page:vertical,
        QComboBox QScrollBar::sub-page:vertical{{
            background:none;
        }}"""

    def _setup_combobox(self, combo, width=200, max_items=8):
        """统一设置 QComboBox 属性"""
        combo.setFixedHeight(self._scale_size(32))
        combo.setFixedWidth(self._scale_size(width))
        combo.setMaxVisibleItems(max_items)
        combo.setStyleSheet(self._get_combobox_stylesheet())

    def _update_combobox_font(self, combo_widget, font_family_quoted):
        """更新 QComboBox 的字体"""
        combo_widget.setStyleSheet(self._get_combobox_stylesheet(font_family=font_family_quoted))

    def _update_single_combobox_opacity(self, combo, opacity_rgba):
        """更新单个下拉框的透明度"""
        combo.setStyleSheet(self._get_combobox_stylesheet(opacity_rgba=opacity_rgba))

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

        # 背景模糊开关
        self._create_blur_toggle_option()
        self.window.appearance_content_layout.addWidget(self.window.blur_toggle_widget)

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

        # 版本隔离选项
        self._create_version_isolation_option()
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.window.version_isolation_widget)

        # 开发控制台选项
        self._create_dev_console_option()
        scroll_layout.insertWidget(scroll_layout.count() - 1, self.window.dev_console_widget)

        return page

    def create_instance_page(self):
        """创建实例页面 - 使用多层级导航结构"""
        from PyQt6.QtWidgets import QScrollArea, QStackedWidget, QLabel as QtLabel
        from widgets import FileExplorer
        from utils import load_svg_icon, scale_icon_for_display

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # 创建堆叠窗口用于多层级页面导航
        self.window.instance_stack = QStackedWidget()
        self.window.instance_stack.setStyleSheet("background:transparent;")
        self.window.instance_pages = []  # 存储页面历史（不再使用，保留以避免兼容性问题）

        # 第一层：主页面（路径选择和版本列表）
        main_page = self._create_instance_main_page()
        self.window.instance_stack.addWidget(main_page)

        pl.addWidget(self.window.instance_stack)

        return page

    def _create_instance_main_page(self):
        """创建实例主页面（第一层）"""
        from PyQt6.QtWidgets import QScrollArea, QLabel as QtLabel
        from utils import load_svg_icon, scale_icon_for_display

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        title = QLabel(self.window.language_manager.translate("page_instances"))
        title.setStyleSheet(f"color:white;font-size:{self._scale_size(20)}px;font-family:'{self._get_font_family()}';font-weight:bold;")
        pl.addWidget(title)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(title, "page_instances", group="instance_page")

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

        # Minecraft路径选择区域
        path_container = QWidget()
        path_container.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        path_layout = QVBoxLayout(path_container)
        path_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        path_layout.setSpacing(self._scale_size(10))

        # 路径标题
        path_title = QtLabel(self.window.language_manager.translate("instance_path_title"))
        path_title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-weight:bold;font-family:'{self._get_font_family()}';background:transparent;")
        path_layout.addWidget(path_title)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(path_title, "instance_path_title", group="instance_page")

        # 路径描述
        path_desc = QtLabel(self.window.language_manager.translate("instance_path_desc"))
        path_desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        path_desc.setWordWrap(True)
        path_layout.addWidget(path_desc)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(path_desc, "instance_path_desc", group="instance_page")

        # 路径输入和选择按钮
        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(self._scale_size(10))

        from PyQt6.QtWidgets import QLineEdit
        self.window.instance_path_input = QLineEdit()
        self.window.instance_path_input.setPlaceholderText(self.window.language_manager.translate("instance_path_placeholder"))
        padding = self._scale_size(6)
        border_radius_input = self._scale_size(4)
        self.window.instance_path_input.setStyleSheet(
            f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);border-radius:{border_radius_input}px;padding:{padding}px;color:white;font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';}}"
        )
        self.window.instance_path_input.editingFinished.connect(self._on_instance_path_changed)
        path_input_layout.addWidget(self.window.instance_path_input, 1)
        # 注册到 TextRenderer（使用 setPlaceholderText 方法）
        self.text_renderer.register_widget(
            self.window.instance_path_input,
            "instance_path_placeholder",
            update_method="setPlaceholderText",
            group="instance_page"
        )

        # 浏览按钮
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius_input}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius_input}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(self._choose_instance_path)
        folder_pixmap = load_svg_icon("svg/folder2.svg", self.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.dpi_scale))
        path_input_layout.addWidget(browse_btn)

        path_layout.addLayout(path_input_layout)

        scroll_layout.addWidget(path_container)

        # 版本列表容器
        version_container = QWidget()
        version_container.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        version_container_layout = QVBoxLayout(version_container)
        version_container_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        version_container_layout.setSpacing(self._scale_size(8))

        # 版本列表标题
        version_title = QtLabel(self.window.language_manager.translate("instance_version_label"))
        version_title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-weight:bold;font-family:'{self._get_font_family()}';background:transparent;")
        version_container_layout.addWidget(version_title)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(version_title, "instance_version_label", group="instance_page")

        # 版本列表（滚动区域）
        from PyQt6.QtWidgets import QWidget as QtWidget
        version_list_widget = QtWidget()
        version_list_layout = QVBoxLayout(version_list_widget)
        version_list_layout.setContentsMargins(0, 0, 0, 0)
        version_list_layout.setSpacing(self._scale_size(6))

        # 版本列表容器引用，用于动态更新
        self.window.instance_version_list_container = version_list_layout
        self.window.instance_version_container = version_container  # 保存版本容器引用
        self.window.instance_version_list_widget = version_list_widget  # 保存版本列表小部件引用

        version_container_layout.addWidget(version_list_widget)
        scroll_layout.addWidget(version_container)

        # 根目录材质包容器（用于版本隔离关闭时显示）
        root_resourcepacks_container = QWidget()
        root_resourcepacks_container.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        root_resourcepacks_layout = QVBoxLayout(root_resourcepacks_container)
        root_resourcepacks_layout.setContentsMargins(0, 0, 0, 0)
        root_resourcepacks_layout.setSpacing(0)

        # 创建文件浏览器用于显示根目录材质包（无滚动模式）
        from widgets import FileExplorer
        self.window.root_resourcepacks_explorer = FileExplorer(
            dpi_scale=self.dpi_scale,
            config_manager=self.window.config_manager,
            language_manager=self.window.language_manager,
            text_renderer=self.text_renderer,
            no_scroll=True  # 无滚动模式，让file_tree根据内容自动调整大小
        )
        root_resourcepacks_layout.addWidget(self.window.root_resourcepacks_explorer)

        scroll_layout.addWidget(root_resourcepacks_container)
        self.window.root_resourcepacks_container = root_resourcepacks_container  # 保存根目录材质包容器引用

        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 加载保存的Minecraft路径和版本列表
        saved_path = self.window.config.get("minecraft_path", "")
        if saved_path and os.path.exists(saved_path):
            self.window.instance_path_input.setText(saved_path)
            # 使用QTimer延迟加载版本列表，确保UI完全初始化
            from PyQt6.QtCore import QTimer
            def delayed_load():
                try:
                    self._load_version_list(saved_path)
                except Exception as e:
                    pass
            QTimer.singleShot(300, delayed_load)

        return page

    def _create_instance_resourcepack_page(self, title, resourcepacks_path):
        """创建资源包页面（第二层）"""
        from PyQt6.QtWidgets import QScrollArea
        from widgets import FileExplorer

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # 顶部导航栏（包含标题和返回按钮）
        nav_bar = QWidget()
        nav_bar.setFixedHeight(self._scale_size(40))
        nav_bar.setStyleSheet("background:rgba(255,255,255,0.05);")
        nav_layout = QHBoxLayout(nav_bar)
        nav_layout.setContentsMargins(self._scale_size(20), 0, self._scale_size(20), 0)
        nav_layout.setSpacing(self._scale_size(10))

        # 返回按钮（更小，使用x.svg图标）
        from widgets import ClickableLabel
        back_btn = ClickableLabel()
        back_btn.setFixedSize(self._scale_size(28), self._scale_size(28))
        back_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border-radius:{self._scale_size(14)}px;",
            f"background:rgba(255,255,255,0.15);border-radius:{self._scale_size(14)}px;"
        )
        back_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        from utils import load_svg_icon, scale_icon_for_display
        x_pixmap = load_svg_icon("svg/x.svg", self.dpi_scale)
        if x_pixmap:
            back_btn.setPixmap(scale_icon_for_display(x_pixmap, 16, self.dpi_scale))
        back_btn.setCallback(lambda: self._navigate_instance_back())
        nav_layout.addWidget(back_btn)

        # 页面标题
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color:white;font-size:{self._scale_size(16)}px;font-weight:bold;font-family:'{self._get_font_family()}';background:transparent;")
        nav_layout.addWidget(title_label)
        nav_layout.addStretch()
        # 保存标题标签引用以便更新
        self.window.resourcepack_page_title = title_label
        # 注册到 TextRenderer（使用版本名称的翻译键）
        # 这里需要保存原始版本名称，以便语言切换时重新获取翻译
        if "resourcepacks_path" in resourcepacks_path:
            # 这是版本资源包页面，标题是版本名称
            # 语言切换时需要根据新的语言重新显示版本名称（不翻译）
            # 暂时不注册，因为版本名称不需要翻译
            pass
        else:
            # 根目录资源包页面，使用固定文本
            # 可以注册到 TextRenderer
            self.text_renderer.register_widget(title_label, "instance_version_root", group="instance_page")

        pl.addWidget(nav_bar)

        # 文件浏览器
        self.window.file_explorer = FileExplorer(
            dpi_scale=self.dpi_scale,
            config_manager=self.window.config_manager,
            language_manager=self.window.language_manager,
            text_renderer=self.text_renderer
        )

        # 设置资源包路径
        if resourcepacks_path and os.path.exists(resourcepacks_path):
            # 获取.minecraft路径
            minecraft_path = None
            if "\\versions\\" in resourcepacks_path or "/versions/" in resourcepacks_path:
                # 版本路径
                parts = resourcepacks_path.replace("\\", "/").split("/versions/")
                if len(parts) > 1:
                    minecraft_path = parts[0]
            else:
                # 根目录路径
                parts = resourcepacks_path.replace("\\", "/").split("/resourcepacks")
                if len(parts) > 1:
                    minecraft_path = parts[0]

            # 使用新的set_resourcepacks_path方法
            if minecraft_path:
                self.window.file_explorer.set_resourcepacks_path(resourcepacks_path, minecraft_path)
            else:
                # 兜底方案：如果没有找到minecraft路径
                self.window.file_explorer.root_path = os.path.dirname(resourcepacks_path)
                self.window.file_explorer.base_path = resourcepacks_path
                self.window.file_explorer.current_path = resourcepacks_path
                self.window.file_explorer.resourcepack_mode = True
                display_path = self.window.file_explorer._format_path_display(resourcepacks_path)
                self.window.file_explorer.path_label.setText(display_path)
                self.window.file_explorer.path_label.show()
                self.window.file_explorer.back_btn.setEnabled(False)
                self.window.file_explorer.empty_label.hide()
                self.window.file_explorer.file_tree.show()
                self.window.file_explorer._load_directory(resourcepacks_path)
        else:
            self.window.file_explorer.empty_label.setText(f"路径不存在: {resourcepacks_path}")
            self.window.file_explorer.empty_label.show()
            self.window.file_explorer.file_tree.hide()

        pl.addWidget(self.window.file_explorer, 1)

        return page

    def _load_versions(self, minecraft_path):
        """加载Minecraft版本列表（为兼容性保留）"""
        self._load_version_list(minecraft_path)

    def _on_version_changed(self, text):
        """版本下拉框改变事件（为兼容性保留）"""
        # 当前版本选择逻辑由点击版本卡片处理，此方法保留为空
        pass

    def create_download_page(self):
        """创建下载页面"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        pl.setSpacing(self._scale_size(15))

        # 使用统一的标题创建方法
        title = self._create_page_title(self.window.language_manager.translate("page_downloads"))
        pl.addWidget(title)

        # 搜索框、搜索按钮和版本选择
        search_container = QWidget()
        search_container.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(self._scale_size(12), self._scale_size(8), self._scale_size(12), self._scale_size(8))
        search_layout.setSpacing(self._scale_size(10))

        # 搜索输入框（缩短）
        self.window.download_search = QLineEdit()
        self.window.download_search.setPlaceholderText("Search downloads...")
        self.window.download_search.setStyleSheet(self._get_lineedit_stylesheet())
        self.window.download_search.setClearButtonEnabled(True)
        # 添加 Enter 键事件处理
        self.window.download_search.returnPressed.connect(self._on_search_clicked)
        search_layout.addWidget(self.window.download_search, 3)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(
            self.window.download_search,
            "download_search_placeholder",
            update_method="setPlaceholderText",
            group="download_page"
        )

        # 搜索按钮（正方形）
        search_btn = QPushButton()
        search_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        search_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        search_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        search_pixmap = load_svg_icon("svg/search.svg", self.dpi_scale)
        if search_pixmap:
            from PyQt6.QtCore import QSize
            search_btn.setIcon(QIcon(scale_icon_for_display(search_pixmap, 16, self.dpi_scale)))
            search_btn.setIconSize(QSize(self._scale_size(16), self._scale_size(16)))
        search_btn.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(search_btn)

        # 版本选择（固定长度的长条，用于选择下载目标）
        self.window.download_version_combo = QComboBox()
        self._setup_combobox(self.window.download_version_combo, width=230)
        # 根据版本隔离设置显示/隐藏
        self.window.download_version_combo.setVisible(self.window.config.get("version_isolation", True))
        search_layout.addWidget(self.window.download_version_combo, 2)

        pl.addWidget(search_container)

        # 平台选择和筛选排序按钮容器
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(self._scale_size(10))

        # 平台选择按钮（三段式按钮）
        platform_container = QWidget()
        platform_container.setStyleSheet(f"background:rgba(255,255,255,0.05);border-radius:{self._scale_size(8)}px;")
        platform_layout = QHBoxLayout(platform_container)
        platform_layout.setContentsMargins(self._scale_size(4), self._scale_size(4), self._scale_size(4), self._scale_size(4))
        platform_layout.setSpacing(0)

        # 全部按钮
        self.window.download_platform_all = QPushButton(self.window.language_manager.translate("download_platform_all"))
        self.window.download_platform_all.setFixedSize(120, 32)
        self._setup_platform_button(self.window.download_platform_all, True, 0)
        self.window.download_platform_all.clicked.connect(lambda: self._on_platform_selected(0))
        platform_layout.addWidget(self.window.download_platform_all)

        # Modrinth 按钮
        self.window.download_platform_modrinth = QPushButton(self.window.language_manager.translate("download_platform_modrinth"))
        self.window.download_platform_modrinth.setFixedSize(160, 32)
        self._setup_platform_button(self.window.download_platform_modrinth, False, 1)
        self.window.download_platform_modrinth.clicked.connect(lambda: self._on_platform_selected(1))
        platform_layout.addWidget(self.window.download_platform_modrinth)

        # CurseForge 按钮
        self.window.download_platform_curseforge = QPushButton(self.window.language_manager.translate("download_platform_curseforge"))
        self.window.download_platform_curseforge.setFixedSize(160, 32)
        self._setup_platform_button(self.window.download_platform_curseforge, False, 2)
        self.window.download_platform_curseforge.clicked.connect(lambda: self._on_platform_selected(2))
        platform_layout.addWidget(self.window.download_platform_curseforge)

        # 存储平台按钮的引用，用于更新选中状态
        self.window.download_platform_buttons = [
            self.window.download_platform_all,
            self.window.download_platform_modrinth,
            self.window.download_platform_curseforge
        ]
        # 当前选中的平台索引
        self.window.current_download_platform = 0

        # 平台选择按钮靠左
        controls_layout.addWidget(platform_container, 0, Qt.AlignmentFlag.AlignLeft)
        # 弹性空间，使按钮靠右
        controls_layout.addStretch(1)

        # 筛选按钮
        filter_btn = QPushButton()
        filter_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        filter_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        funnel_pixmap = load_svg_icon("svg/funnel.svg", self.dpi_scale)
        if funnel_pixmap:
            from PyQt6.QtCore import QSize
            filter_btn.setIcon(QIcon(scale_icon_for_display(funnel_pixmap, 16, self.dpi_scale)))
            filter_btn.setIconSize(QSize(self._scale_size(16), self._scale_size(16)))
        controls_layout.addWidget(filter_btn)

        # 排序按钮
        sort_btn = QPushButton()
        sort_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        sort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        sort_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
            }
            QPushButton:pressed {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        sort_pixmap = load_svg_icon("svg/sort-down.svg", self.dpi_scale)
        if sort_pixmap:
            from PyQt6.QtCore import QSize
            sort_btn.setIcon(QIcon(scale_icon_for_display(sort_pixmap, 16, self.dpi_scale)))
            sort_btn.setIconSize(QSize(self._scale_size(16), self._scale_size(16)))
        controls_layout.addWidget(sort_btn)

        pl.addWidget(controls_container)

        # 使用统一的滚动区域创建方法
        scroll_area = self._create_scroll_area()
        scroll_content, scroll_layout = self._create_scroll_content()
        scroll_layout.addStretch()
        
        # 保存滚动内容区域的引用，用于显示搜索结果
        self.window.download_scroll_content = scroll_content
        self.window.download_scroll_layout = scroll_layout

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 加载 Minecraft 版本列表到下拉框
        self._load_versions_to_download_combo()

        return page

    def _load_versions_to_download_combo(self):
        """从.minecraft路径加载版本列表到下载页面的下拉框（用于选择下载目标）"""
        import os
        try:
            # 如果版本隔离关闭，不加载版本列表，也不显示"根目录"选项
            if not self.window.config.get("version_isolation", True):
                self.window.download_version_combo.clear()
                return

            minecraft_path = self.window.config.get("minecraft_path", "")
            if minecraft_path and os.path.exists(minecraft_path):
                versions_path = os.path.join(minecraft_path, "versions")
                if os.path.exists(versions_path) and os.path.isdir(versions_path):
                    # 清除现有选项（不添加"Root"）
                    self.window.download_version_combo.clear()

                    # 获取并添加所有版本
                    versions = []
                    for item in sorted(os.listdir(versions_path)):
                        item_path = os.path.join(versions_path, item)
                        if os.path.isdir(item_path):
                            versions.append(item)

                    # 添加版本到下拉框
                    for version in versions:
                        self.window.download_version_combo.addItem(version)

                    logger.info(f"Loaded {len(versions)} versions to download combo")
        except Exception as e:
            logger.error(f"Error loading versions to download combo: {e}")

    def get_download_target_path(self):
        """获取下载目标路径（基于下拉框选择）"""
        import os
        try:
            minecraft_path = self.window.config.get("minecraft_path", "")
            if not minecraft_path or not os.path.exists(minecraft_path):
                return None

            # 如果版本隔离关闭，直接返回根目录的resourcepacks路径
            if not self.window.config.get("version_isolation", True):
                return os.path.join(minecraft_path, "resourcepacks")

            # 版本隔离开启时，根据下拉框选择返回对应路径
            selected_version = self.window.download_version_combo.currentText()
            if selected_version:
                # 返回对应版本的resourcepacks路径
                return os.path.join(minecraft_path, "versions", selected_version, "resourcepacks")
            # 如果没有选择版本，返回根目录
            return os.path.join(minecraft_path, "resourcepacks")
        except Exception as e:
            logger.error(f"Error getting download target path: {e}")
            return None

    def _setup_platform_button(self, button, is_selected, index):
        """设置平台按钮的样式"""
        border_radius = self._scale_size(8)
        # 根据位置设置不同的圆角
        if index == 0:
            # 左侧按钮
            border_style = f"border-top-left-radius:{border_radius}px;border-bottom-left-radius:{border_radius}px;border-right:none;"
        elif index == 2:
            # 右侧按钮
            border_style = f"border-top-right-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;border-left:none;"
        else:
            # 中间按钮
            border_style = "border:none;"
        
        if is_selected:
            button.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.15);
                    {border_style}
                    color: white;
                    font-size: {self._scale_size(13)}px;
                    font-family: '{self._get_font_family()}';
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    {border_style}
                    color: rgba(255, 255, 255, 0.7);
                    font-size: {self._scale_size(13)}px;
                    font-family: '{self._get_font_family()}';
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.9);
                }}
            """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_platform_selected(self, index):
        """平台选择事件处理"""
        self.window.current_download_platform = index
        # 更新按钮样式
        for i, button in enumerate(self.window.download_platform_buttons):
            self._setup_platform_button(button, i == index, i)

    def _update_platform_button_texts(self):
        """更新平台按钮的文本"""
        if hasattr(self.window, 'download_platform_buttons'):
            current_index = self.window.current_download_platform
            for i, button in enumerate(self.window.download_platform_buttons):
                # 更新文本
                if i == 0:
                    button.setText(self.window.language_manager.translate("download_platform_all"))
                elif i == 1:
                    button.setText(self.window.language_manager.translate("download_platform_modrinth"))
                elif i == 2:
                    button.setText(self.window.language_manager.translate("download_platform_curseforge"))
                # 重新应用样式以确保选中状态正确
                self._setup_platform_button(button, i == current_index, i)

    def _on_search_clicked(self):
        """搜索按钮点击事件处理"""
        query = self.window.download_search.text().strip()
        if not query:
            return
        
        # 根据选中的平台执行搜索
        platform = self.window.current_download_platform
        if platform == 1:  # Modrinth
            self._search_modrinth(query)
        elif platform == 2:  # CurseForge
            self._search_curseforge(query)
        else:  # 全部平台 - 默认搜索 Modrinth
            self._search_modrinth(query)
    
    def _search_modrinth(self, query):
        """搜索 Modrinth 项目"""
        from managers.modrinth_manager import ModrinthManager
        from PyQt6.QtCore import QThread, pyqtSignal, QTimer
        
        # 清除之前的搜索结果
        self._clear_search_results()
        
        # 显示加载提示
        self._show_loading_message()
        
        # 使用 QTimer 延迟执行搜索，给 UI 时间更新
        def do_search():
            try:
                manager = ModrinthManager()
                # 添加资源包类型筛选
                facets = [["project_type:resourcepack"]]
                result = manager.search_projects(query, facets=facets, limit=10)
                hits = result.get('hits', [])
                # 使用 QTimer 再次延迟，确保在主线程执行
                QTimer.singleShot(0, lambda: self._on_modrinth_search_finished(hits))
            except Exception as e:
                logger.error(f"Modrinth search failed: {e}")
                QTimer.singleShot(0, lambda: self._on_search_error(str(e)))
        
        QTimer.singleShot(50, do_search)
    
    def _search_curseforge(self, query):
        """搜索 CurseForge 项目（暂未实现）"""
        logger.info(f"CurseForge search not implemented yet: {query}")
    
    def _clear_search_results(self):
        """清除搜索结果"""
        if hasattr(self.window, 'download_scroll_layout'):
            # 清除搜索结果，保留最后一个 stretch
            layout = self.window.download_scroll_layout
            # 从后向前删除，保留最后一个 stretch
            for i in range(layout.count() - 2, -1, -1):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    widget.setParent(None)
                    widget.deleteLater()
    
    def _show_loading_message(self):
        """显示加载消息"""
        if hasattr(self.window, 'download_scroll_layout'):
            from PyQt6.QtWidgets import QLabel
            loading_label = QLabel("Searching...")
            loading_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, loading_label)
    
    def _on_modrinth_search_finished(self, hits):
        """Modrinth 搜索完成"""
        # 清除加载消息
        self._clear_search_results()
        
        if not hits:
            # 显示无结果消息
            self._show_no_results_message()
            return
        
        # 显示搜索结果
        layout = self.window.download_scroll_layout
        start_index = layout.count() - 1  # 在 stretch 之前插入
        
        # 使用 QTimer 延迟创建和添加卡片，分批渲染
        def create_and_add_cards(current_hit_index=0):
            # 每次添加 2 个卡片，避免阻塞 UI
            batch_size = 2
            end_hit_index = min(current_hit_index + batch_size, len(hits))
            
            insert_index = start_index + current_hit_index
            
            for i in range(current_hit_index, end_hit_index):
                hit = hits[i]
                project_data = {
                    'title': hit.get('title', 'Unknown'),
                    'description': hit.get('description', ''),
                    'icon_url': hit.get('icon_url', ''),
                    'downloads': hit.get('downloads', 0),
                    'follows': hit.get('follows', 0),
                    'project_id': hit.get('project_id', ''),
                    'slug': hit.get('slug', '')
                }
                
                # 使用函数包装避免 lambda 闭包问题
                def make_download_handler(data):
                    return lambda checked=False: self._on_download_modrinth_project(data)
                
                # 创建结果卡片
                result_card = ModrinthResultCard(
                    project_data,
                    dpi_scale=self.dpi_scale,
                    on_download=make_download_handler(project_data)
                )
                
                # 立即显示卡片
                result_card.show()
                result_card.update()
                
                # 添加到滚动区域
                layout.insertWidget(insert_index, result_card)
                insert_index += 1
            
            # 如果还有卡片要添加，继续下一批
            if end_hit_index < len(hits):
                QTimer.singleShot(10, lambda idx=end_hit_index: create_and_add_cards(idx))
        
        # 开始分批创建卡片
        from PyQt6.QtCore import QTimer
        QTimer.singleShot(50, create_and_add_cards)
        
        logger.info(f"Modrinth search completed: {len(hits)} results found")
    
    def _on_search_error(self, error):
        """搜索错误处理"""
        self._clear_search_results()
        self._show_error_message(error)
        logger.error(f"Search error: {error}")
    
    def _show_no_results_message(self):
        """显示无结果消息"""
        if hasattr(self.window, 'download_scroll_layout'):
            from PyQt6.QtWidgets import QLabel
            no_results_label = QLabel("No results found")
            no_results_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, no_results_label)
    
    def _show_error_message(self, error):
        """显示错误消息"""
        if hasattr(self.window, 'download_scroll_layout'):
            from PyQt6.QtWidgets import QLabel
            error_label = QLabel(f"Search failed: {error}")
            error_label.setStyleSheet("color: rgba(255, 100, 100, 0.9); font-size: 14px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, error_label)
    
    def _on_download_modrinth_project(self, project_data, checked=False):
        """下载 Modrinth 项目"""
        logger.info(f"Downloading project: {project_data.get('title', 'Unknown')}")
        # TODO: 实现下载逻辑
        # 这里需要：
        # 1. 获取项目的最新版本
        # 2. 下载文件到指定目录
        # 3. 更新文件浏览器显示
        pass

    def create_console_page(self):
        """创建控制台/日志页面"""
        from PyQt6.QtWidgets import QTextEdit, QLineEdit
        from PyQt6.QtCore import Qt

        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(self._scale_size(20), self._scale_size(10), self._scale_size(20), self._scale_size(20))
        console_layout.setSpacing(self._scale_size(15))

        title = self._create_page_title(self.window.language_manager.translate("page_console"))
        console_layout.addWidget(title)

        # 计算背景透明度（主页透明度 + 20）
        blur_opacity = self.window.config.get("blur_opacity", 150)
        bg_opacity = min(255, blur_opacity + 20)

        # 背景容器
        bg_container = QWidget()
        bg_container.setStyleSheet(f"""
            QWidget {{
                background: rgba(0, 0, 0, {bg_opacity});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {self._scale_size(8)}px;
            }}
        """)
        bg_layout = QVBoxLayout(bg_container)
        bg_layout.setContentsMargins(self._scale_size(10), self._scale_size(10), self._scale_size(10), self._scale_size(10))
        bg_layout.setSpacing(self._scale_size(10))

        # 创建日志文本框
        self.window.console_text = QTextEdit()
        self.window.console_text.setReadOnly(True)
        self.window.console_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.9);
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {self._scale_size(12)}px;
                padding: 0px;
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: rgba(255, 255, 255, 0.5);
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                background: rgba(255, 255, 255, 0.1);
                height: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(255, 255, 255, 0.3);
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(255, 255, 255, 0.5);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        bg_layout.addWidget(self.window.console_text, 1)

        # 输入框
        self.window.console_input = QLineEdit()
        self.window.console_input.setPlaceholderText("Enter command (restart to restart program)")
        self.window.console_input.setStyleSheet(self._get_lineedit_stylesheet())
        # 注册到 TextRenderer
        self.text_renderer.register_widget(
            self.window.console_input,
            "console_input_placeholder",
            update_method="setPlaceholderText",
            group="console_page"
        )

        # 监听回车键
        def handle_command():
            command = self.window.console_input.text().strip()
            self.window.console_input.clear()

            cmd_lower = command.lower()

            if cmd_lower == "restart":
                # 重启程序
                import sys
                import os
                self.window.close()
                python = sys.executable
                os.execl(python, python, *sys.argv)

            elif cmd_lower in ["exit", "quit"]:
                # 退出程序
                from PyQt6.QtWidgets import QApplication
                QApplication.instance().quit()

            elif cmd_lower == "clear":
                # 清空日志显示
                self.window.console_text.clear()

            elif cmd_lower == "reload":
                # 重新加载日志
                self.window._load_console_logs()

            elif cmd_lower == "help":
                # 显示帮助信息
                help_text = """
Available commands:
  restart  - Restart the program
  exit     - Exit the program
  quit     - Exit the program (same as exit)
  clear    - Clear the console display
  reload   - Reload log files
  info     - Show program information
  help     - Show this help message
"""
                self.window.console_text.append(help_text)

            elif cmd_lower == "info":
                # 显示程序信息
                import sys
                from managers import ConfigManager
                config_manager = ConfigManager()
                config = config_manager.config

                info_text = f"""
Spectra Information:
  Python Version: {sys.version.split()[0]}
  Window Size: {self.window.width()}x{self.window.height()}
  DPI Scale: {self.window.dpi_scale:.2f}
  Background Mode: {config.get('background_mode', 'blur')}
  Blur Opacity: {config.get('blur_opacity', 150)}
  Language: {config.get('language', 'en_US')}
"""
                self.window.console_text.append(info_text)

            else:
                # 未知指令
                self.window.console_text.append(f"Unknown command: {command}")
                self.window.console_text.append("Type 'help' to see available commands.")

        self.window.console_input.returnPressed.connect(handle_command)
        bg_layout.addWidget(self.window.console_input)

        console_layout.addWidget(bg_container, 1)

        # 加载日志
        self.window._load_console_logs()

        return console_widget

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
        # 注册到 TextRenderer
        self.text_renderer.register_widget(opacity_label, "blur_opacity", group="settings_page")

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

        path_label = self._create_label_with_style(self.window.language_manager.translate("bg_image_path"))
        path_layout.addWidget(path_label)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(path_label, "bg_image_path", group="settings_page")

        self.window.path_input = QLineEdit()
        self.window.path_input.setText(self.window.config.get("background_image_path", ""))
        self.window.path_input.setStyleSheet(self._get_lineedit_stylesheet())
        self.window.path_input.editingFinished.connect(self.window.on_path_changed)
        path_layout.addWidget(self.window.path_input, 1)

        # 浏览按钮
        browse_btn = self._create_browse_button(self.window.choose_background_image)
        path_layout.addWidget(browse_btn)

        self.window.path_widget.setVisible(self.window.config.get("background_mode") == "image")

    def _create_browse_button(self, callback):
        """创建统一的浏览按钮"""
        border_radius_btn = self._scale_size(4)
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius_btn}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius_btn}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(callback)

        folder_pixmap = load_svg_icon("svg/folder2.svg", self.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.dpi_scale))

        return browse_btn

    def _create_color_picker(self):
        self.window.color_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.color_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        color_layout = QHBoxLayout(self.window.color_widget)
        color_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        color_layout.setSpacing(self._scale_size(10))

        color_label = self._create_label_with_style(self.window.language_manager.translate("bg_color"))
        color_layout.addWidget(color_label)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(color_label, "bg_color", group="settings_page")

        # 颜色预览和输入
        self.window.color_input = QLineEdit()
        self.window.color_input.setText(self.window.config.get("background_color", "#00000000"))
        self.window.color_input.setStyleSheet(self._get_lineedit_stylesheet())
        self.window.color_input.editingFinished.connect(self.window.on_color_changed)
        color_layout.addWidget(self.window.color_input, 1)

        # 颜色选择按钮
        color_btn = QPushButton()
        color_btn.setFixedSize(self._scale_size(32), self._scale_size(32))
        border_radius_btn = self._scale_size(4)
        color_str = self.window.config.get("background_color", "#00000000")
        bg_color = self._parse_color_to_hex(color_str)
        color_btn.setStyleSheet(f"QPushButton{{background:{bg_color};border:1px solid rgba(255,255,255,0.3);border-radius:{border_radius_btn}px;}}QPushButton:hover{{background:{bg_color};border:1px solid rgba(255,255,255,0.5);}}")
        color_btn.clicked.connect(self.window.choose_background_color)
        color_layout.addWidget(color_btn)
        self.window.color_btn = color_btn

        self.window.color_widget.setVisible(self.window.config.get("background_mode") == "solid")

    def _parse_color_to_hex(self, color_str):
        """解析颜色字符串并返回十六进制格式"""
        color = QColor(color_str)
        if color.isValid():
            return color.name(QColor.NameFormat.HexArgb)
        if len(color_str) == 7 and color_str.startswith('#'):
            return QColor(f"#FF{color_str[1:]}").name(QColor.NameFormat.HexArgb)
        return "#00000000"

    def _create_font_select_widget(self):
        from PyQt6.QtGui import QFontDatabase
        from PyQt6.QtWidgets import QComboBox

        self.window.font_select_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.font_select_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        font_select_layout = QHBoxLayout(self.window.font_select_widget)
        font_select_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        font_select_layout.setSpacing(self._scale_size(10))

        font_select_label = QLabel(self.window.language_manager.translate("font_select_label"))
        font_select_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        font_select_layout.addWidget(font_select_label)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(font_select_label, "font_select_label", group="settings_page")

        font_select_layout.addStretch()

        self.window.font_combo = QComboBox()
        self.window.font_combo.setFixedHeight(self._scale_size(32))
        self.window.font_combo.setFixedWidth(self._scale_size(200))
        self.window.font_combo.setMaxVisibleItems(8)
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)

        # 获取当前下拉框透明度（主页透明度 + 50）
        blur_opacity = self.window.config.get("blur_opacity", 150)
        dropdown_opacity_value = min(255, blur_opacity + 50)
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
        font_families = QFontDatabase.families()

        # 添加常用字体到前面
        common_fonts = ["Microsoft YaHei UI", "SimHei", "Arial", "Segoe UI", "Helvetica"]
        added_fonts = set()

        # 先添加常用字体
        for font in common_fonts:
            if font in font_families:
                self.window.font_combo.addItem(font)
                added_fonts.add(font)

        # 添加其他字体
        for font in font_families:
            if font not in added_fonts:
                self.window.font_combo.addItem(font)
        
        # 设置当前字体
        current_font_family = self.window.config.get("custom_font_family", "Microsoft YaHei UI")
        font_index = self.window.font_combo.findText(current_font_family)
        if font_index >= 0:
            self.window.font_combo.setCurrentIndex(font_index)
        
        # 连接字体选择事件
        self.window.font_combo.currentTextChanged.connect(self.window.on_font_family_changed)
        
        font_select_layout.addWidget(self.window.font_combo)

        return self.window.font_select_widget

    # 实例页面相关方法
    def _choose_instance_path(self):
        """选择Minecraft路径"""
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(
            self.window,
            self.window.language_manager.translate("instance_path_dialog_title"),
            ""
        )
        if path:
            self.window.instance_path_input.setText(path)
            self._on_instance_path_changed()

    def _on_instance_path_changed(self):
        """Minecraft路径变化"""
        import os
        try:
            path = self.window.instance_path_input.text().strip()
            if path and os.path.exists(path):
                # 保存路径到配置
                self.window.config["minecraft_path"] = path
                self.window.config_manager.save_config()

                # 加载版本列表
                self._load_version_list(path)
                
                # 更新下载页面的版本列表
                self._load_versions_to_download_combo()
            else:
                # 清空版本列表
                self._clear_version_list()
                
                # 清空下载页面的版本列表
                if hasattr(self.window, 'download_version_combo'):
                    self.window.download_version_combo.clear()
                    self.window.download_version_combo.addItem(self.window.language_manager.translate("instance_version_root"))
        except Exception as e:
            # 静默处理错误，避免崩溃
            import traceback
            logger.error(f"Error loading version list: {e}")
            logger.error(traceback.format_exc())
            pass

    def _load_version_list(self, minecraft_path):
        """加载Minecraft版本列表（显示为可点击的卡片）"""
        import os
        try:
            logger.info(f"Loading version list from: {minecraft_path}")

            # 如果版本隔离关闭，直接在版本列表位置显示根目录材质包
            if not self.window.config.get("version_isolation", True):
                self._clear_version_list()
                # 隐藏版本容器
                if hasattr(self.window, 'instance_version_container'):
                    self.window.instance_version_container.setVisible(False)
                # 显示根目录材质包容器
                if hasattr(self.window, 'root_resourcepacks_container'):
                    self.window.root_resourcepacks_container.setVisible(True)
                    # 设置根目录材质包路径
                    root_resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
                    if os.path.exists(root_resourcepacks_path):
                        self.window.root_resourcepacks_explorer.set_resourcepacks_path(root_resourcepacks_path, minecraft_path)
                return

            # 显示版本容器，隐藏根目录材质包容器
            if hasattr(self.window, 'instance_version_container'):
                self.window.instance_version_container.setVisible(True)
            if hasattr(self.window, 'root_resourcepacks_container'):
                self.window.root_resourcepacks_container.setVisible(False)

            versions_path = os.path.join(minecraft_path, "versions")
            logger.info(f"Versions path: {versions_path}")
            self._clear_version_list()

            # 获取收藏的版本列表
            favorited_versions = self.window.config.get("favorited_versions", [])
            logger.info(f"Favorited versions: {favorited_versions}")

            # 收集所有版本
            all_versions = []
            if os.path.exists(versions_path) and os.path.isdir(versions_path):
                for item in sorted(os.listdir(versions_path)):
                    item_path = os.path.join(versions_path, item)
                    if os.path.isdir(item_path):
                        all_versions.append(item)
                logger.info(f"Found {len(all_versions)} versions: {all_versions}")
            else:
                logger.warning(f"Versions path does not exist or is not a directory: {versions_path}")

            # 将版本分为收藏和非收藏两组
            favorites = []
            non_favorites = []
            for version in all_versions:
                if version in favorited_versions:
                    favorites.append(version)
                else:
                    non_favorites.append(version)

            # 先添加收藏的版本
            logger.info(f"Adding {len(favorites)} favorite versions")
            for version in favorites:
                self._add_version_item(minecraft_path, version, is_version=True, is_favorited=True)

            # 再添加非收藏的版本
            logger.info(f"Adding {len(non_favorites)} non-favorite versions")
            for version in non_favorites:
                self._add_version_item(minecraft_path, version, is_version=True, is_favorited=False)
        except Exception as e:
            # 静默处理错误，避免崩溃
            import traceback
            logger.error(f"Error loading version list: {e}")
            logger.error(traceback.format_exc())
            pass

    def _clear_version_list(self):
        """清空版本列表"""
        if hasattr(self.window, 'instance_version_list_container'):
            # 清空现有列表
            while self.window.instance_version_list_container.count() > 0:
                child = self.window.instance_version_list_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def _add_version_item(self, minecraft_path, version_name, is_version=False, is_favorited=False):
        """添加一个版本项到列表"""
        from widgets import ClickableLabel, make_transparent
        from utils import load_svg_icon, scale_icon_for_display

        # 创建版本卡片
        version_card = VersionCardWidget()
        version_card.setFixedHeight(self._scale_size(48))
        
        normal_style = f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.08);
                border-radius: {self._scale_size(8)}px;
            }}
        """
        hover_style = f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.15);
                border-radius: {self._scale_size(8)}px;
            }}
        """
        version_card.set_styles(normal_style, hover_style)
        version_card.setStyleSheet(normal_style)
        version_card.setCursor(Qt.CursorShape.PointingHandCursor)

        # 确定资源包路径和显示名称
        if is_version:
            resourcepacks_path = os.path.join(minecraft_path, "versions", version_name, "resourcepacks")
            # 检查是否有自定义别名
            version_aliases = self.window.config.get("version_aliases", {})
            display_name = version_aliases.get(version_name, version_name)
        else:
            resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
            display_name = self.window.language_manager.translate("instance_version_root")

        # 卡片内容布局
        card_layout = QHBoxLayout(version_card)
        card_layout.setContentsMargins(self._scale_size(12), 0, self._scale_size(12), 0)
        card_layout.setSpacing(self._scale_size(10))

        # 创建点击区域容器
        click_area = ClickableLabel()
        click_area.setStyleSheet("background:transparent;")
        click_area.setCallback(lambda rp=resourcepacks_path, dn=display_name: self._navigate_to_resourcepack_page(dn, rp))
        click_area_layout = QHBoxLayout(click_area)
        click_area_layout.setContentsMargins(0, 0, 0, 0)
        click_area_layout.setSpacing(self._scale_size(10))

        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(self._scale_size(32), self._scale_size(32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setStyleSheet("background:transparent;")
        
        # 判断版本类型并选择图标
        if is_version:
            version_type = self._detect_version_type(minecraft_path, version_name)
            if version_type == "fabric":
                icon_path = "png/fabric.png"
            elif version_type == "forge":
                icon_path = "png/forge.png"
            elif version_type == "neoforge":
                icon_path = "png/neoforged.png"
            else:  # vanilla or unknown
                icon_path = "png/block.png"
            
            # 获取 PNG 文件的正确路径
            if hasattr(sys, '_MEIPASS'):
                # 打包后环境，优先从 _internal 读取
                png_path = os.path.join(sys._MEIPASS, icon_path.replace('\\', os.sep))
                if not os.path.exists(png_path):
                    png_path = os.path.join(os.getcwd(), icon_path.replace('\\', os.sep))
            else:
                # 开发环境
                png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", icon_path.replace('\\', os.sep))
                png_path = os.path.abspath(png_path)
            
            # 加载PNG图标
            from PyQt6.QtGui import QPixmap
            icon_pixmap = QPixmap(png_path)
            if not icon_pixmap.isNull():
                scaled_pixmap = icon_pixmap.scaled(
                    int(20 * self.dpi_scale),
                    int(20 * self.dpi_scale),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
        else:
            # 根目录使用默认图标
            icon_pixmap = load_svg_icon("svg/box-fill.svg", self.dpi_scale)
            if icon_pixmap:
                icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))
        click_area_layout.addWidget(icon_label)

        # 版本名称
        name_label = QLabel(display_name)
        name_label.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        click_area_layout.addWidget(name_label)
        click_area_layout.addStretch()

        # 箭头图标
        arrow_label = QLabel()
        arrow_label.setFixedSize(self._scale_size(20), self._scale_size(20))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("background:transparent;")
        arrow_pixmap = load_svg_icon("svg/arrow-bar-right.svg", self.dpi_scale)
        if arrow_pixmap:
            arrow_label.setPixmap(scale_icon_for_display(arrow_pixmap, 16, self.dpi_scale))
        click_area_layout.addWidget(arrow_label)

        card_layout.addWidget(click_area)

        bookmark_btn = None
        edit_btn = None

        # 收藏按钮和编辑按钮（仅对版本显示）
        if is_version:
            # 编辑按钮
            edit_btn = QPushButton()
            edit_btn.setFixedSize(self._scale_size(20), self._scale_size(20))
            edit_btn.hide()  # 默认隐藏
            edit_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 0;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """)
            edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            edit_btn.clicked.connect(lambda: self._edit_version_name(version_name, name_label))
            
            # 设置编辑图标
            edit_pixmap = load_svg_icon("svg/pencil-square.svg", self.dpi_scale)
            if edit_pixmap:
                edit_btn.setIcon(QIcon(scale_icon_for_display(edit_pixmap, 16, self.dpi_scale)))
            
            # 将编辑按钮设置到卡片中，以便悬停时显示
            version_card.set_edit_button(edit_btn)
            
            card_layout.addWidget(edit_btn)
            
            # 收藏按钮
            bookmark_btn = QPushButton()
            bookmark_btn.setFixedSize(self._scale_size(20), self._scale_size(20))
            bookmark_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    padding: 0;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 4px;
                }
            """)
            bookmark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            bookmark_btn.clicked.connect(lambda: self._toggle_favorite_version(version_name))
            
            # 设置初始图标
            if is_favorited:
                bookmark_pixmap = load_svg_icon("svg/bookmarks-fill.svg", self.dpi_scale)
            else:
                bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self.dpi_scale)
            
            if bookmark_pixmap:
                bookmark_btn.setIcon(QIcon(scale_icon_for_display(bookmark_pixmap, 16, self.dpi_scale)))
            
            # 设置卡片按钮信息
            version_card.set_bookmark_info(bookmark_btn, is_favorited)
            
            # 未收藏的版本初始时不显示图标
            if not is_favorited:
                bookmark_btn.setIcon(QIcon())
            
            card_layout.addWidget(bookmark_btn)

        # 处理卡片的点击事件
        def mouse_press_handler(e):
            click_area.mousePressEvent(e)
        
        def mouse_release_handler(e):
            click_area.mouseReleaseEvent(e)
        
        version_card.mousePressEvent = mouse_press_handler
        version_card.mouseReleaseEvent = mouse_release_handler

        self.window.instance_version_list_container.addWidget(version_card)

        return bookmark_btn

    def _navigate_to_resourcepack_page(self, title, resourcepacks_path):
        """导航到资源包页面（第二层）"""
        logger.info(f"Navigating to resourcepack page: {title}, path: {resourcepacks_path}")
        logger.info(f"Stack widgets: {self.window.instance_stack.count()}")
        
        # 检查是否已经存在相同路径的资源包页面
        for i in range(self.window.instance_stack.count()):
            widget = self.window.instance_stack.widget(i)
            if hasattr(widget, '_resourcepacks_path') and widget._resourcepacks_path == resourcepacks_path:
                # 如果已存在，直接切换到该页面
                logger.info(f"Found existing page for path: {resourcepacks_path}")
                self.window.instance_stack.setCurrentIndex(i)
                return
        
        # 创建新的资源包页面
        resourcepack_page = self._create_instance_resourcepack_page(title, resourcepacks_path)
        resourcepack_page._resourcepacks_path = resourcepacks_path  # 标记页面路径
        self.window.instance_stack.addWidget(resourcepack_page)
        self.window.instance_stack.setCurrentWidget(resourcepack_page)
        
        logger.info(f"Stack widgets after adding: {self.window.instance_stack.count()}")

    def _navigate_instance_back(self):
        """返回上一页"""
        logger.info(f"_navigate_instance_back called")
        logger.info(f"Stack count: {self.window.instance_stack.count()}")
        logger.info(f"Current index: {self.window.instance_stack.currentIndex()}")
        
        count = self.window.instance_stack.count()
        if count <= 1:
            logger.info("Only one page in stack, cannot go back")
            return
        
        # 获取当前索引
        current_index = self.window.instance_stack.currentIndex()
        
        # 移除当前页面（最后一个页面）
        widget_to_remove = self.window.instance_stack.currentWidget()
        logger.info(f"Removing widget at index {current_index}")
        
        self.window.instance_stack.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()
        
        # 切换到前一个页面（自动切换到 count-1 位置）
        logger.info(f"Switching to index {self.window.instance_stack.currentIndex()}")
        
        logger.info(f"Stack count after back: {self.window.instance_stack.count()}")

    def _detect_version_type(self, minecraft_path, version_name):
        """检测Minecraft版本类型（fabric/forge/neoforge/vanilla）"""
        import json
        import zipfile
        
        try:
            version_path = os.path.join(minecraft_path, "versions", version_name)
            if not os.path.exists(version_path):
                return "vanilla"
            
            # 查找版本jar文件或目录
            version_jar = os.path.join(version_path, version_name + ".jar")
            if not os.path.exists(version_jar):
                version_jar = os.path.join(version_path, version_name)
                if os.path.isdir(version_jar):
                    # 如果是目录，查找其中的jar文件
                    for item in os.listdir(version_jar):
                        if item.endswith(".jar"):
                            version_jar = os.path.join(version_jar, item)
                            break
            
            if not os.path.exists(version_jar) or not os.path.isfile(version_jar):
                return "vanilla"
            
            # 检查json文件
            version_json = os.path.join(version_path, version_name + ".json")
            if os.path.exists(version_json):
                with open(version_json, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    
                    # 检查inheritsFrom字段（有此字段说明是子版本，如forge）
                    if "inheritsFrom" in json_data:
                        parent_version = json_data["inheritsFrom"]
                        # 检查父版本的名称
                        if "forge" in version_name.lower():
                            return "forge"
                        elif "neoforge" in version_name.lower():
                            return "neoforge"
                        elif "fabric" in version_name.lower():
                            return "fabric"
                    
                    # 检查id字段
                    if "id" in json_data:
                        version_id = json_data["id"].lower()
                        if "forge" in version_id and "neoforge" not in version_id:
                            return "forge"
                        elif "neoforge" in version_id:
                            return "neoforge"
                        elif "fabric" in version_id:
                            return "fabric"
                    
                    # 检查version字段
                    if "version" in json_data:
                        version_val = json_data["version"].lower()
                        if "forge" in version_val and "neoforge" not in version_val:
                            return "forge"
                        elif "neoforge" in version_val:
                            return "neoforge"
                        elif "fabric" in version_val:
                            return "fabric"
            
            # 检查jar文件中的fabric.mod.json
            try:
                with zipfile.ZipFile(version_jar, 'r') as jar_file:
                    # 检查fabric.mod.json
                    mod_json_files = [f for f in jar_file.namelist() if 'fabric.mod.json' in f]
                    if mod_json_files:
                        return "fabric"
                    
                    # 检查forge的mods.toml
                    mods_toml_files = [f for f in jar_file.namelist() if 'mods.toml' in f]
                    if mods_toml_files:
                        # 检查是否是neoforge
                        for f in jar_file.namelist():
                            if 'neoforge' in f.lower():
                                return "neoforge"
                        return "forge"
            except:
                pass
            
            # 根据版本名称判断
            version_lower = version_name.lower()
            if "neoforge" in version_lower:
                return "neoforge"
            elif "forge" in version_lower:
                return "forge"
            elif "fabric" in version_lower:
                return "fabric"
            
            return "vanilla"
        except Exception as e:
            logger.error(f"Error detecting version type for {version_name}: {e}")
            return "vanilla"

    def _edit_version_name(self, original_name, name_label):
        """编辑版本名称"""
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit
        from PyQt6.QtCore import Qt
        
        # 获取当前显示的名称（可能是修改过的）
        current_name = name_label.text()
        
        # 获取主窗口背景模式，使用相同的背景设置
        background_mode = self.window.config.get("background_mode", "blur")
        
        # 设置对话框样式（与主页外观一致）
        if background_mode == "blur":
            # 模糊模式：使用透明度+50
            blur_opacity = self.window.config.get("blur_opacity", 150)
            dialog_opacity = min(255, blur_opacity + 50)
            opacity_alpha = dialog_opacity / 255.0
            dialog_style = f"""
                QDialog {{
                    background: rgba(0, 0, 0, {opacity_alpha});
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self._scale_size(12)}px;
                }}
            """
        elif background_mode == "solid":
            # 纯色模式：使用纯色背景
            bg_color = self.window.config.get("background_color", "#00000000")
            dialog_style = f"""
                QDialog {{
                    background: {bg_color};
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self._scale_size(12)}px;
                }}
            """
        else:  # image 或其他模式
            # 图片模式：使用透明度+50
            blur_opacity = self.window.config.get("blur_opacity", 150)
            dialog_opacity = min(255, blur_opacity + 50)
            opacity_alpha = dialog_opacity / 255.0
            dialog_style = f"""
                QDialog {{
                    background: rgba(0, 0, 0, {opacity_alpha});
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self._scale_size(12)}px;
                }}
            """
        
        # 创建自定义对话框（无标题栏）
        dialog = QDialog(self.window)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setFixedSize(self._scale_size(400), self._scale_size(180))
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        dialog.setStyleSheet(dialog_style)
        
        # 对话框布局
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(self._scale_size(24), self._scale_size(24), self._scale_size(24), self._scale_size(24))
        dialog_layout.setSpacing(self._scale_size(16))
        
        # 标题标签（使用本地化）
        title_label = QLabel(self.window.language_manager.translate("edit_version_name_title"))
        title_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                font-size: {self._scale_size(14)}px;
                font-family: '{self._get_font_family()}';
            }}
        """)
        dialog_layout.addWidget(title_label)
        
        # 输入框
        input_field = QLineEdit(current_name)
        input_field.setFixedHeight(self._scale_size(36))
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self._scale_size(6)}px;
                padding: 0 {self._scale_size(12)}px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {self._scale_size(14)}px;
                font-family: '{self._get_font_family()}';
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(100, 150, 255, 0.6);
            }}
        """)
        input_field.selectAll()  # 全选文本方便修改
        dialog_layout.addWidget(input_field)
        
        dialog_layout.addStretch()
        
        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(self._scale_size(10))
        
        # 取消按钮（使用本地化）
        cancel_btn = QPushButton(self.window.language_manager.translate("cancel"))
        cancel_btn.setFixedHeight(self._scale_size(36))
        cancel_btn.setFixedWidth(self._scale_size(100))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {self._scale_size(6)}px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {self._scale_size(13)}px;
                font-family: '{self._get_font_family()}';
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.12);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.08);
            }}
        """)
        cancel_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        cancel_btn.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_btn)
        
        # 确认按钮（使用本地化）
        confirm_btn = QPushButton(self.window.language_manager.translate("confirm"))
        confirm_btn.setFixedHeight(self._scale_size(36))
        confirm_btn.setFixedWidth(self._scale_size(100))
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100, 150, 255, 0.8);
                border: none;
                border-radius: {self._scale_size(6)}px;
                color: white;
                font-size: {self._scale_size(13)}px;
                font-family: '{self._get_font_family()}';
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(100, 150, 255, 1.0);
            }}
            QPushButton:pressed {{
                background: rgba(100, 150, 255, 0.7);
            }}
        """)
        confirm_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        confirm_btn.clicked.connect(dialog.accept)
        button_layout.addWidget(confirm_btn)
        
        button_layout.addStretch()
        dialog_layout.addLayout(button_layout)
        
        # 设置对话框为模态并显示
        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        input_field.setFocus()
        
        result = dialog.exec()
        
        if result == QDialog.DialogCode.Accepted:
            new_name = input_field.text().strip()
            if new_name:
                # 获取版本别名映射
                version_aliases = self.window.config.get("version_aliases", {})
                
                if new_name == original_name:
                    # 如果新名字和原始名字相同，移除别名
                    if original_name in version_aliases:
                        del version_aliases[original_name]
                        self.window.config_manager.set("version_aliases", version_aliases)
                        name_label.setText(original_name)
                        logger.info(f"Removed alias for version: {original_name}")
                else:
                    # 保存新的别名
                    version_aliases[original_name] = new_name
                    self.window.config_manager.set("version_aliases", version_aliases)
                    name_label.setText(new_name)
                    logger.info(f"Updated version name: {original_name} -> {new_name}")

    def _toggle_favorite_version(self, version_name):
        """切换版本的收藏状态"""
        logger.info(f"Toggling favorite status for version: {version_name}")
        favorited_versions = self.window.config.get("favorited_versions", [])
        
        if version_name in favorited_versions:
            # 取消收藏
            logger.info(f"Removing {version_name} from favorites")
            favorited_versions.remove(version_name)
        else:
            # 添加收藏
            logger.info(f"Adding {version_name} to favorites")
            favorited_versions.append(version_name)
        
        # 更新配置
        logger.info(f"Saving favorited versions: {favorited_versions}")
        self.window.config_manager.set("favorited_versions", favorited_versions)
        
        # 重新加载版本列表，使收藏的版本置顶
        saved_path = self.window.config.get("minecraft_path", "")
        logger.info(f"Reloading version list from path: {saved_path}")
        if saved_path:
            self._load_version_list(saved_path)

    def _create_font_path_widget(self):
        self.window.font_path_widget = QWidget()
        border_radius = self._scale_size(8)
        self.window.font_path_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;")
        font_path_layout = QHBoxLayout(self.window.font_path_widget)
        font_path_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        font_path_layout.setSpacing(self._scale_size(10))

        font_path_label = self._create_label_with_style(self.window.language_manager.translate("font_custom_label"))
        font_path_layout.addWidget(font_path_label)

        self.window.font_path_input = QLineEdit()
        self.window.font_path_input.setText(self.window.config.get("custom_font_path", ""))
        self.window.font_path_input.setStyleSheet(self._get_lineedit_stylesheet())
        self.window.font_path_input.editingFinished.connect(self.window.on_font_path_changed)
        font_path_layout.addWidget(self.window.font_path_input, 1)

        # 浏览按钮
        browse_btn = self._create_browse_button(self.window.choose_font_file)
        font_path_layout.addWidget(browse_btn)

        self.window.font_path_widget.setVisible(self.window.config.get("font_mode") == 1)

        return self.window.font_path_widget

    def _create_toggle_switch(self, checked=False):
        """创建自定义切换开关"""
        from PyQt6.QtWidgets import QWidget
        from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
        from PyQt6.QtGui import QPainter, QColor, QBrush
        from PyQt6.QtCore import pyqtProperty

        class ToggleSwitch(QWidget):
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
                painter.drawRoundedRect(int(track_x), int(track_y), int(track_width), int(track_height), int(track_height / 2), int(track_height / 2))

                # 绘制滑块
                knob_x = track_x + self._slider_position * (track_width - knob_size)
                knob_y = (h - knob_size) / 2

                if self._checked:
                    painter.setBrush(QBrush(QColor(255, 255, 255)))
                else:
                    painter.setBrush(QBrush(QColor(200, 200, 200)))

                painter.drawEllipse(int(knob_x), int(knob_y), int(knob_size), int(knob_size))

        toggle = ToggleSwitch(checked=checked, dpi_scale=self.dpi_scale)
        return toggle

    def _create_blur_toggle_option(self):
        """创建背景模糊开关选项"""
        blur_enabled = self.window.config.get("background_blur_enabled", True)

        # 创建可点击的容器
        self.window.blur_toggle_widget = QWidget()
        self.window.blur_toggle_widget.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        blur_toggle_layout = QHBoxLayout(self.window.blur_toggle_widget)
        blur_toggle_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        blur_toggle_layout.setSpacing(self._scale_size(12))

        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(self._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(self.window.language_manager.translate("background_blur_enabled"))
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(self.window.language_manager.translate("background_blur_enabled_desc"))
        desc_lbl.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(desc_lbl)

        blur_toggle_layout.addLayout(text_layout)
        blur_toggle_layout.addStretch()

        # 切换开关
        self.window.blur_toggle = self._create_toggle_switch(blur_enabled)
        self.window.blur_toggle.setCallback(lambda checked: self.window.toggle_blur_enabled(checked))
        blur_toggle_layout.addWidget(self.window.blur_toggle)

    def _create_version_isolation_option(self):
        """创建版本隔离选项"""
        version_isolation_enabled = self.window.config.get("version_isolation", True)

        # 创建可点击的容器
        self.window.version_isolation_widget = QWidget()
        self.window.version_isolation_widget.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        version_isolation_layout = QHBoxLayout(self.window.version_isolation_widget)
        version_isolation_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        version_isolation_layout.setSpacing(self._scale_size(12))

        # 盒子图标
        box_icon = load_svg_icon("svg/box-fill.svg", self.dpi_scale)
        icon_label = QLabel()
        icon_label.setFixedSize(self._scale_size(20), self._scale_size(20))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if box_icon:
            icon_label.setPixmap(scale_icon_for_display(box_icon, 20, self.dpi_scale))
        version_isolation_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(self._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(self.window.language_manager.translate("version_isolation"))
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(self.window.language_manager.translate("version_isolation_desc"))
        desc_lbl.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(desc_lbl)

        version_isolation_layout.addLayout(text_layout)
        version_isolation_layout.addStretch()

        # 切换开关
        self.window.version_isolation_toggle = self._create_toggle_switch(version_isolation_enabled)
        self.window.version_isolation_toggle.setCallback(lambda checked: self.window.toggle_version_isolation(checked))
        version_isolation_layout.addWidget(self.window.version_isolation_toggle)

    def _create_dev_console_option(self):
        """创建开发控制台选项"""
        dev_console_enabled = self.window.config.get("dev_console_enabled", False)

        # 创建可点击的容器
        self.window.dev_console_widget = QWidget()
        self.window.dev_console_widget.setStyleSheet(f"background:rgba(255,255,255,0.08);border-radius:{self._scale_size(8)}px;")
        dev_console_layout = QHBoxLayout(self.window.dev_console_widget)
        dev_console_layout.setContentsMargins(self._scale_size(15), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        dev_console_layout.setSpacing(self._scale_size(12))

        # 终端图标
        console_icon = load_svg_icon("svg/terminal.svg", self.dpi_scale)
        icon_label = QLabel()
        icon_label.setFixedSize(self._scale_size(20), self._scale_size(20))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if console_icon:
            icon_label.setPixmap(scale_icon_for_display(console_icon, 20, self.dpi_scale))
        dev_console_layout.addWidget(icon_label, 0, Qt.AlignmentFlag.AlignTop)

        # 文本区域
        text_layout = QVBoxLayout()
        text_layout.setSpacing(self._scale_size(4))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(self.window.language_manager.translate("dev_console"))
        title_lbl.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(self.window.language_manager.translate("dev_console_desc"))
        desc_lbl.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;")
        text_layout.addWidget(desc_lbl)

        dev_console_layout.addLayout(text_layout)
        dev_console_layout.addStretch()

        # 切换开关
        self.window.dev_console_toggle = self._create_toggle_switch(dev_console_enabled)
        self.window.dev_console_toggle.setCallback(lambda checked: self.window.toggle_dev_console(checked))
        dev_console_layout.addWidget(self.window.dev_console_toggle)

    def _create_language_card(self):
        from PyQt6.QtWidgets import QComboBox

        language_widget = QWidget()
        language_widget.setStyleSheet(f"background:rgba(255,255,255,0);border-bottom-left-radius:{self._scale_size(8)}px;border-bottom-right-radius:{self._scale_size(8)}px;")
        language_layout = QHBoxLayout(language_widget)
        language_layout.setContentsMargins(self._scale_size(35), self._scale_size(12), self._scale_size(15), self._scale_size(12))
        language_layout.setSpacing(self._scale_size(10))

        language_label = QLabel(self.window.language_manager.translate("settings_language_label"))
        language_label.setStyleSheet(f"color:rgba(255,255,255,0.8);font-size:{self._scale_size(13)}px;font-family:'{self._get_font_family()}';")
        language_layout.addWidget(language_label)
        # 注册到 TextRenderer
        self.text_renderer.register_widget(language_label, "settings_language_label", group="settings_page")

        language_layout.addStretch()

        self.window.language_combo = QComboBox()
        self._setup_combobox(self.window.language_combo, width=150, max_items=5)

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

        # 更新实例页面的版本列表中的根版本名称
        self._update_instance_version_labels()

        # 更新下载页面标题
        download_page = self.window.stack.widget(2)
        if download_page and download_page.layout():
            title = download_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_downloads"))

        # 更新下载页面平台按钮文本
        self._update_platform_button_texts()

        # 更新控制台页面标题
        console_page = self.window.stack.widget(3)
        if console_page and console_page.layout():
            title = console_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_console"))

        # 更新设置页面标题
        settings_page = self.window.stack.widget(4)
        if settings_page and settings_page.layout():
            title = settings_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.window.language_manager.translate("page_settings"))

    def _update_instance_version_labels(self):
        """更新实例页面中版本列表的标签（包括根版本名称）"""
        if not hasattr(self.window, 'instance_version_list_container'):
            return

        root_text = self.window.language_manager.translate("instance_version_root")

        # 遍历版本列表容器，更新根版本的名称标签
        for i in range(self.window.instance_version_list_container.count()):
            item = self.window.instance_version_list_container.itemAt(i)
            if item and item.widget():
                # 获取卡片中的 click_area
                card = item.widget()
                card_layout = card.layout()
                if card_layout and card_layout.count() > 0:
                    # 第一个元素应该是 click_area
                    click_area = card_layout.itemAt(0).widget()
                    if click_area and click_area.layout():
                        # 查找版本名称标签（第二个子元素，第一个是图标）
                        if click_area.layout().count() > 1:
                            name_label = click_area.layout().itemAt(1).widget()
                            if name_label and hasattr(name_label, 'setText'):
                                # 检查是否是根版本（通过比较文本）
                                current_text = name_label.text()
                                # 如果当前文本是"根目录"或对应的英文，则更新
                                if current_text in ["Root Directory", "根目录", root_text]:
                                    name_label.setText(root_text)

        # 更新资源包页面的标题（如果存在）
        if hasattr(self.window, 'resourcepack_page_title') and self.window.resourcepack_page_title:
            try:
                # 检查 widget 是否仍然有效（未被删除）
                if not self.window.resourcepack_page_title.isVisible():
                    # 如果不可见，说明可能已被删除，跳过更新
                    pass
                else:
                    current_title = self.window.resourcepack_page_title.text()
                    if current_title in ["Root Directory", "根目录", root_text]:
                        self.window.resourcepack_page_title.setText(root_text)
            except RuntimeError:
                # 如果 widget 已被删除，捕获异常并跳过
                pass
    
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

        # 更新开发控制台选项
        if hasattr(self.window, 'dev_console_widget') and self.window.dev_console_widget.layout():
            dev_console_layout = self.window.dev_console_widget.layout()
            for i in range(dev_console_layout.count()):
                item = dev_console_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        if title and hasattr(title, 'setText'):
                            title.setText(self.window.language_manager.translate("dev_console"))
                        if desc and hasattr(desc, 'setText'):
                            desc.setText(self.window.language_manager.translate("dev_console_desc"))
                        break

        # 更新版本隔离选项
        if hasattr(self.window, 'version_isolation_widget') and self.window.version_isolation_widget.layout():
            version_isolation_layout = self.window.version_isolation_widget.layout()
            for i in range(version_isolation_layout.count()):
                item = version_isolation_layout.itemAt(i)
                if item and isinstance(item.layout(), QVBoxLayout):
                    text_layout = item.layout()
                    if text_layout.count() >= 2:
                        title = text_layout.itemAt(0).widget()
                        desc = text_layout.itemAt(1).widget()
                        if title and hasattr(title, 'setText'):
                            title.setText(self.window.language_manager.translate("version_isolation"))
                        if desc and hasattr(desc, 'setText'):
                            desc.setText(self.window.language_manager.translate("version_isolation_desc"))
                        break

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

    def _refresh_instance_page(self):
        """刷新实例页面（当版本隔离设置变化时调用）"""
        import os
        try:
            # 获取当前Minecraft路径
            minecraft_path = self.window.config.get("minecraft_path", "")
            if minecraft_path and os.path.exists(minecraft_path):
                # 重新加载版本列表（会根据版本隔离设置显示不同内容）
                self._load_version_list(minecraft_path)
                # 更新下载页面的版本列表
                self._load_versions_to_download_combo()
                # 更新下载页面的版本选择框可见性
                if hasattr(self.window, 'download_version_combo'):
                    self.window.download_version_combo.setVisible(self.window.config.get("version_isolation", True))
        except Exception as e:
            logger.error(f"Error refreshing instance page: {e}")

    def _update_bg_card(self, card, title_key, desc_key):
        """更新卡片的标题和描述文本"""
        if not card or not card.layout():
            return
        
        layout = card.layout()
        # 查找文本布局（通常在中间的 QVBoxLayout）
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.layout(), QHBoxLayout):
                inner_layout = item.layout()
                for j in range(inner_layout.count()):
                    inner_item = inner_layout.itemAt(j)
                    if inner_item and isinstance(inner_item.layout(), QVBoxLayout):
                        text_layout = inner_item.layout()
                        # 第一个是标题，第二个是描述
                        if text_layout.count() >= 2:
                            title = text_layout.itemAt(0).widget()
                            desc = text_layout.itemAt(1).widget()
                            if title and hasattr(title, 'setText'):
                                title.setText(self.window.language_manager.translate(title_key))
                            if desc and hasattr(desc, 'setText'):
                                desc.setText(self.window.language_manager.translate(desc_key))
                            break
                        break

    def _update_bg_card_font(self, card, font_family):
        """更新卡片的字体"""
        if not card or not card.layout():
            return
        
        layout = card.layout()
        # 查找文本布局（通常在中间的 QVBoxLayout）
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.layout(), QHBoxLayout):
                inner_layout = item.layout()
                for j in range(inner_layout.count()):
                    inner_item = inner_item.layout()
                    if inner_item and isinstance(inner_item.layout(), QVBoxLayout):
                        text_layout = inner_item.layout()
                        # 第一个是标题，第二个是描述
                        if text_layout.count() >= 2:
                            title = text_layout.itemAt(0).widget()
                            desc = text_layout.itemAt(1).widget()
                            if title:
                                title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:{font_family};background:transparent;")
                            if desc:
                                desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:{font_family};background:transparent;")
                            break
                        break

    def _update_expandable_menu_font(self, container, font_family):
        """更新可展开菜单的字体"""
        if not container or not container.layout():
            return
        
        header = container.layout().itemAt(0).widget()
        if not header or not header.layout():
            return
        
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
                    if title:
                        title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:{font_family};background:transparent;")
                    if desc:
                        desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:{font_family};background:transparent;")
                    break

