"""文字渲染管理器 - 统一控制本地化和字体更新

该模块提供了一个 TextRenderer 类，用于统一管理界面中的文字渲染，
包括本地化翻译和字体更新，确保语言切换后所有文本能够立即刷新。
"""

from typing import Optional, Dict, List, Callable, Any
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QComboBox, QTreeWidgetItem
from PyQt6.QtGui import QFont
import logging

logger = logging.getLogger(__name__)


class TextRenderer:
    """文字渲染管理器 - 统一控制本地化和字体更新"""

    def __init__(self, language_manager=None):
        """
        初始化文字渲染管理器

        Args:
            language_manager: 语言管理器实例
        """
        self.language_manager = language_manager
        self._registered_widgets: Dict[str, List[Dict[str, Any]]] = {}
        # 字体缓存
        self._font_family: str = "Microsoft YaHei UI"
        # DPI 缩放比例
        self._dpi_scale: float = 1.0

    def set_language_manager(self, language_manager):
        """设置语言管理器"""
        self.language_manager = language_manager

    def set_dpi_scale(self, scale: float):
        """设置 DPI 缩放比例"""
        self._dpi_scale = scale

    def set_font_family(self, font_family: str):
        """设置字体系列"""
        self._font_family = font_family
        # 更新所有已注册的字体
        self._update_all_fonts()

    def register_widget(
        self,
        widget: QWidget,
        text_key: str,
        update_method: Optional[str] = "setText",
        format_kwargs: Optional[Dict[str, Any]] = None,
        group: Optional[str] = None
    ):
        """
        注册一个需要动态更新的控件

        Args:
            widget: 要注册的控件
            text_key: 翻译键
            update_method: 更新方法名，默认为 setText
            format_kwargs: 格式化参数（用于字符串格式化）
            group: 分组名称，用于批量更新
        """
        widget_info = {
            "widget": widget,
            "text_key": text_key,
            "update_method": update_method,
            "format_kwargs": format_kwargs or {}
        }

        group_key = group if group else "default"
        if group_key not in self._registered_widgets:
            self._registered_widgets[group_key] = []

        self._registered_widgets[group_key].append(widget_info)
        logger.debug(f"注册控件: {widget.__class__.__name__}, 键: {text_key}, 分组: {group_key}")

        # 立即更新一次文本
        self._update_widget(widget_info)

    def unregister_widget(self, widget: QWidget, group: Optional[str] = None):
        """
        注销一个控件

        Args:
            widget: 要注销的控件
            group: 分组名称，如果为 None 则在所有分组中查找
        """
        if group:
            if group in self._registered_widgets:
                self._registered_widgets[group] = [
                    info for info in self._registered_widgets[group]
                    if info["widget"] is not widget
                ]
        else:
            # 在所有分组中查找并删除
            for group_key in self._registered_widgets:
                self._registered_widgets[group_key] = [
                    info for info in self._registered_widgets[group_key]
                    if info["widget"] is not widget
                ]

    def unregister_group(self, group: str):
        """注销整个分组"""
        if group in self._registered_widgets:
            del self._registered_widgets[group]

    def update_language(self):
        """更新所有已注册控件的语言"""
        for group_key, widgets in self._registered_widgets.items():
            for widget_info in widgets:
                self._update_widget(widget_info)
        logger.info(f"已更新 {sum(len(w) for w in self._registered_widgets.values())} 个控件的语言")

    def update_group_language(self, group: str):
        """更新指定分组的语言"""
        if group in self._registered_widgets:
            for widget_info in self._registered_widgets[group]:
                self._update_widget(widget_info)

    def _update_widget(self, widget_info: Dict[str, Any]):
        """更新单个控件的文本"""
        widget = widget_info["widget"]
        text_key = widget_info["text_key"]
        update_method = widget_info["update_method"]
        format_kwargs = widget_info["format_kwargs"]

        # 检查控件是否已被删除（使用 try-except 包装 isinstance 检查）
        try:
            try:
                # 尝试调用控件方法，如果失败则说明控件已被删除
                widget.isVisible()
            except:
                # 控件已被删除，跳过更新
                return
        except:
            pass

        # 获取翻译文本
        if self.language_manager:
            text = self.language_manager.translate(text_key, default=text_key)
        else:
            text = text_key

        # 应用格式化参数
        if format_kwargs:
            try:
                text = text.format(**format_kwargs)
            except (KeyError, AttributeError, ValueError) as e:
                logger.warning(f"格式化文本失败: {text}, 错误: {e}")

        # 调用更新方法
        try:
            if hasattr(widget, update_method):
                method = getattr(widget, update_method)
                method(text)
            else:
                logger.warning(f"控件 {widget.__class__.__name__} 没有方法 {update_method}")
        except Exception as e:
            # 如果是 "wrapped C/C++ object has been deleted" 错误，说明控件已被删除
            if "has been deleted" in str(e):
                # 控件已被删除，跳过更新
                return
            logger.error(f"更新控件文本失败: {widget.__class__.__name__}, 错误: {e}")

    def _update_all_fonts(self):
        """更新所有已注册控件的字体"""
        for group_key, widgets in self._registered_widgets.items():
            for widget_info in widgets:
                self._update_widget_font(widget_info["widget"])
        logger.info(f"已更新 {sum(len(w) for w in self._registered_widgets.values())} 个控件的字体")

    def _update_widget_font(self, widget: QWidget):
        """更新单个控件的字体"""
        try:
            # 检查控件是否已被删除
            try:
                widget.isVisible()
            except:
                return

            escaped_font = self._font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
            font_family_quoted = f'"{escaped_font}"'

            # 为 QLabel 设置字体（通过样式表）
            if isinstance(widget, QLabel):
                current_style = widget.styleSheet()
                # 使用正则替换 font-family
                import re
                new_style = re.sub(r'font-family:\s*[^;]+;', f'font-family: {font_family_quoted};', current_style)
                if new_style == current_style:  # 如果没有 font-family，添加它
                    widget.setStyleSheet(f"{current_style} font-family: {font_family_quoted};")
                else:
                    widget.setStyleSheet(new_style)

            # 为 QPushButton 设置字体（通过样式表）
            elif isinstance(widget, QPushButton):
                current_style = widget.styleSheet()
                import re
                new_style = re.sub(r'font-family:\s*[^;]+;', f'font-family: {font_family_quoted};', current_style)
                if new_style == current_style:
                    widget.setStyleSheet(f"{current_style} font-family: {font_family_quoted};")
                else:
                    widget.setStyleSheet(new_style)

            # 为 QLineEdit 设置字体（通过样式表）
            elif isinstance(widget, QLineEdit):
                current_style = widget.styleSheet()
                import re
                new_style = re.sub(r'font-family:\s*[^;]+;', f'font-family: {font_family_quoted};', current_style)
                if new_style == current_style:
                    widget.setStyleSheet(f"{current_style} font-family: {font_family_quoted};")
                else:
                    widget.setStyleSheet(new_style)

            # 为 QComboBox 设置字体（通过样式表）
            elif isinstance(widget, QComboBox):
                current_style = widget.styleSheet()
                import re
                new_style = re.sub(r'font-family:\s*[^;]+;', f'font-family: {font_family_quoted};', current_style)
                if new_style == current_style:
                    widget.setStyleSheet(f"{current_style} font-family: {font_family_quoted};")
                else:
                    widget.setStyleSheet(new_style)

            # 为 QTreeWidgetItem 设置字体（通过setFont方法）
            elif isinstance(widget, QTreeWidgetItem):
                font = widget.font(0)
                font.setFamily(self._font_family)
                widget.setFont(0, font)

        except Exception as e:
            # 如果是 "wrapped C/C++ object has been deleted" 错误，说明控件已被删除
            if "has been deleted" in str(e):
                return
            logger.error(f"更新控件字体失败: {widget.__class__.__name__}, 错误: {e}")

    def create_styled_label(
        self,
        text_key: str,
        font_size: int = 13,
        color: str = "rgba(255,255,255,0.8)",
        bold: bool = False,
        group: Optional[str] = None
    ) -> QLabel:
        """
        创建一个带样式的标签并自动注册

        Args:
            text_key: 翻译键
            font_size: 字体大小（会根据 DPI 缩放）
            color: 文本颜色
            bold: 是否加粗
            group: 分组名称

        Returns:
            创建的 QLabel 实例
        """
        label = QLabel()
        scaled_size = int(font_size * self._dpi_scale)

        # 设置样式表
        style_parts = [
            f"color: {color};",
            f"font-size: {scaled_size}px;",
            f"font-family: '{self._font_family}';"
        ]
        if bold:
            style_parts.append("font-weight: bold;")

        label.setStyleSheet("".join(style_parts))

        # 注册控件
        self.register_widget(label, text_key, group=group)

        return label

    def create_styled_button(
        self,
        text_key: str,
        font_size: int = 13,
        group: Optional[str] = None
    ) -> QPushButton:
        """
        创建一个带样式的按钮并自动注册

        Args:
            text_key: 翻译键
            font_size: 字体大小（会根据 DPI 缩放）
            group: 分组名称

        Returns:
            创建的 QPushButton 实例
        """
        button = QPushButton()
        scaled_size = int(font_size * self._dpi_scale)

        # 设置字体
        font = button.font()
        font.setFamily(self._font_family)
        font.setPointSize(scaled_size)
        button.setFont(font)

        # 注册控件
        self.register_widget(button, text_key, group=group)

        return button

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        """
        获取翻译文本（辅助方法）

        Args:
            key: 翻译键
            default: 默认值
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        if self.language_manager:
            text = self.language_manager.translate(key, default=default or key)
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except (KeyError, AttributeError, ValueError):
                    pass
            return text
        return default or key

    def get_font_family(self) -> str:
        """获取当前字体系列"""
        return self._font_family

    def clear_all(self):
        """清空所有已注册的控件"""
        self._registered_widgets.clear()
        logger.info("已清空所有注册的控件")
