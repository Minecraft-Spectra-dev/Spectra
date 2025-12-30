"""UI样式管理模块

提供统一样式表生成方法
"""


class StyleMixin:
    """样式生成混入类

    为UIBuilder提供样式相关方法
    """

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

    def _get_lineedit_stylesheet(self, font_family=None):
        """获取统一的LineEdit样式表"""
        if font_family is None:
            font_family = self._get_font_family()
        escaped_font = font_family.replace("\\\\", "\\\\\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'
        padding = self._scale_size(6)
        border_radius = self._scale_size(4)
        return (f"QLineEdit{{background:rgba(255,255,255,0.1);border:1px solid rgba(255,255,255,0.2);"
                f"border-radius:{border_radius}px;padding:{padding}px;color:white;"
                f"font-size:{self._scale_size(13)}px;font-family:{font_family_quoted};}}")

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
            background:rgba(0,0,0,0.15);
            border:1px solid rgba(255,255,255,0.1);
            border-radius:{border_radius}px;
            selection-background-color:rgba(255,255,255,0.3);
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
        from PyQt6.QtWidgets import QComboBox
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
