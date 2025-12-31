"""实例页面模块

提供实例页面和版本管理的创建功能
"""

import os
import sys
import logging
import json
import zipfile

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QDialog,
                             QPushButton, QFileDialog, QCheckBox, QComboBox)
from PyQt6.QtGui import QPixmap

from utils import load_svg_icon, scale_icon_for_display, normalize_path
from widgets import ClickableLabel, FileExplorer

logger = logging.getLogger(__name__)


class InstancesPageBuilder:
    """实例页面构建器"""

    def __init__(self, builder):
        self.builder = builder
        # 配置编辑器页面缓存，用于返回
        self._config_editor_page = None

    def create_instance_page(self):
        """创建实例页面 - 使用多层级导航结构"""
        from PyQt6.QtWidgets import QScrollArea, QStackedWidget

        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # 创建堆叠窗口用于多层级页面导航
        self.builder.window.instance_stack = QStackedWidget()
        self.builder.window.instance_stack.setStyleSheet("background:transparent;")
        self.builder.window.instance_pages = []

        # 第一层：主页面（路径选择和版本列表）
        main_page = self._create_instance_main_page()
        self.builder.window.instance_stack.addWidget(main_page)
        pl.addWidget(self.builder.window.instance_stack)

        return page

    def _create_instance_main_page(self):
        """创建实例主页面（第一层）"""
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
        pl.addWidget(title)
        self.builder.text_renderer.register_widget(title, "page_instances", group="instance_page")
        title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(20)}px;"
            f"font-family:'{self.builder._get_font_family()}';font-weight:bold;"
        )
        pl.addWidget(title)

        # 注册到 TextRenderer
        self.builder.text_renderer.register_widget(title, "page_instances", group="instance_page")

        # 创建滚动区域
        scroll_area = self.builder._create_scroll_area()
        scroll_content, scroll_layout = self.builder._create_scroll_content(
            margins=(0, self.builder._scale_size(10), 0, 0)
        )

        # Minecraft路径选择区域
        path_container = self._create_path_container()
        scroll_layout.addWidget(path_container)

        # 版本列表容器
        version_container = self._create_version_container()
        scroll_layout.addWidget(version_container)

        # 根目录材质包容器（用于版本隔离关闭时显示）
        root_resourcepacks_container = self._create_root_resourcepacks_container()
        scroll_layout.addWidget(root_resourcepacks_container)

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 加载保存的Minecraft路径和版本列表
        saved_path = self.builder.window.config.get("minecraft_path", "")
        if saved_path and os.path.exists(saved_path):
            self.builder.window.instance_path_input.setText(saved_path)

            def delayed_load():
                try:
                    self._load_version_list(saved_path)
                except Exception as e:
                    pass

            QTimer.singleShot(300, delayed_load)

        return page

    def _create_path_container(self):
        """创建路径选择容器"""
        path_container = QWidget()
        path_container.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        path_layout = QVBoxLayout(path_container)
        path_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        path_layout.setSpacing(self.builder._scale_size(10))

        # 路径标题
        path_title = QLabel()
        path_title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;font-weight:bold;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        path_layout.addWidget(path_title)
        self.builder.text_renderer.register_widget(path_title, "instance_path_title", group="instance_page")
        path_title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;font-weight:bold;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        path_layout.addWidget(path_title)

        self.builder.text_renderer.register_widget(path_title, "instance_path_title", group="instance_page")

        # 路径描述
        path_desc = QLabel()
        path_desc.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        path_desc.setWordWrap(True)
        path_layout.addWidget(path_desc)
        self.builder.text_renderer.register_widget(path_desc, "instance_path_desc", group="instance_page")
        path_desc.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{self.builder._scale_size(12)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        path_desc.setWordWrap(True)
        path_layout.addWidget(path_desc)

        self.builder.text_renderer.register_widget(path_desc, "instance_path_desc", group="instance_page")

        # 路径输入和选择按钮
        path_input_layout = QHBoxLayout()
        path_input_layout.setSpacing(self.builder._scale_size(10))

        self.builder.window.instance_path_input = QLineEdit()
        self.builder.window.instance_path_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.text_renderer.register_widget(
            self.builder.window.instance_path_input,
            "instance_path_placeholder",
            update_method="setPlaceholderText",
            group="instance_page"
        )
        self.builder.window.instance_path_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.window.instance_path_input.editingFinished.connect(self._on_instance_path_changed)
        path_input_layout.addWidget(self.builder.window.instance_path_input, 1)

        self.builder.text_renderer.register_widget(
            self.builder.window.instance_path_input,
            "instance_path_placeholder",
            update_method="setPlaceholderText",
            group="instance_page"
        )

        # 浏览按钮
        browse_btn = ClickableLabel()
        browse_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
        border_radius_input = self.builder._scale_size(4)
        browse_btn.setHoverStyle(
            f"background:rgba(255,255,255,0.1);border:none;border-radius:{border_radius_input}px;",
            f"background:rgba(255,255,255,0.15);border:none;border-radius:{border_radius_input}px;"
        )
        browse_btn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.setCallback(self._choose_instance_path)
        folder_pixmap = load_svg_icon("svg/folder2.svg", self.builder.dpi_scale)
        if folder_pixmap:
            browse_btn.setPixmap(scale_icon_for_display(folder_pixmap, 20, self.builder.dpi_scale))
        path_input_layout.addWidget(browse_btn)

        path_layout.addLayout(path_input_layout)

        return path_container

    def _create_version_container(self):
        """创建版本列表容器"""
        version_container = QWidget()
        version_container.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        version_container_layout = QVBoxLayout(version_container)
        version_container_layout.setContentsMargins(
            self.builder._scale_size(15), self.builder._scale_size(12),
            self.builder._scale_size(15), self.builder._scale_size(12)
        )
        version_container_layout.setSpacing(self.builder._scale_size(8))

        # 版本列表标题
        version_title = QLabel()
        version_title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;font-weight:bold;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        version_container_layout.addWidget(version_title)
        self.builder.text_renderer.register_widget(version_title, "instance_version_label", group="instance_page")
        version_title.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;font-weight:bold;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        version_container_layout.addWidget(version_title)

        self.builder.text_renderer.register_widget(version_title, "instance_version_label", group="instance_page")

        # 版本列表（滚动区域）
        version_list_widget = QWidget()
        version_list_layout = QVBoxLayout(version_list_widget)
        version_list_layout.setContentsMargins(0, 0, 0, 0)
        version_list_layout.setSpacing(self.builder._scale_size(6))

        # 版本列表容器引用，用于动态更新
        self.builder.window.instance_version_list_container = version_list_layout
        self.builder.window.instance_version_container = version_container
        self.builder.window.instance_version_list_widget = version_list_widget

        version_container_layout.addWidget(version_list_widget)

        return version_container

    def _create_root_resourcepacks_container(self):
        """创建根目录材质包容器"""
        root_resourcepacks_container = QWidget()
        root_resourcepacks_container.setStyleSheet("background:transparent;")
        root_resourcepacks_layout = QVBoxLayout(root_resourcepacks_container)
        root_resourcepacks_layout.setContentsMargins(0, 0, 0, 0)
        root_resourcepacks_layout.setSpacing(0)

        # 创建文件浏览器用于显示根目录材质包（无滚动模式，不显示关闭按钮）
        self.builder.window.root_resourcepacks_explorer = FileExplorer(
            dpi_scale=self.builder.dpi_scale,
            config_manager=self.builder.window.config_manager,
            language_manager=self.builder.window.language_manager,
            text_renderer=self.builder.text_renderer,
            no_scroll=True,
            show_close_button=False,
            instances_page_builder=self
        )
        root_resourcepacks_layout.addWidget(self.builder.window.root_resourcepacks_explorer)

        self.builder.window.root_resourcepacks_container = root_resourcepacks_container

        return root_resourcepacks_container

    def _create_instance_resourcepack_page(self, title, resourcepacks_path):
        """创建资源包页面（第二层）"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(0, 0, 0, 0)
        pl.setSpacing(0)

        # 文件浏览器（现在包含自己的标题和路径卡片）
        self.builder.window.file_explorer = FileExplorer(
            dpi_scale=self.builder.dpi_scale,
            config_manager=self.builder.window.config_manager,
            language_manager=self.builder.window.language_manager,
            text_renderer=self.builder.text_renderer,
            instances_page_builder=self
        )

        # 连接关闭按钮信号
        self.builder.window.file_explorer.close_requested.connect(self._navigate_instance_back)

        # 设置资源包路径
        if resourcepacks_path and os.path.exists(resourcepacks_path):
            self._setup_file_explorer_path(resourcepacks_path)
        else:
            self.builder.window.file_explorer.empty_label.setText(f"路径不存在: {resourcepacks_path}")
            self.builder.window.file_explorer.empty_label.show()
            self.builder.window.file_explorer.file_tree.hide()

        pl.addWidget(self.builder.window.file_explorer, 1)

        return page

    def _setup_file_explorer_path(self, resourcepacks_path):
        """设置文件浏览器路径"""
        minecraft_path = None
        if "\\versions\\" in resourcepacks_path:
            parts = resourcepacks_path.split("\\versions\\")
            if len(parts) > 1:
                minecraft_path = parts[0]
        else:
            parts = resourcepacks_path.split("\\resourcepacks")
            if len(parts) > 1:
                minecraft_path = parts[0]

        if minecraft_path:
            self.builder.window.file_explorer.set_resourcepacks_path(resourcepacks_path, minecraft_path)
        else:
            self.builder.window.file_explorer.root_path = os.path.dirname(resourcepacks_path)
            self.builder.window.file_explorer.base_path = resourcepacks_path
            self.builder.window.file_explorer.current_path = resourcepacks_path
            self.builder.window.file_explorer.resourcepack_mode = True
            display_path = self.builder.window.file_explorer._format_path_display(resourcepacks_path)
            self.builder.window.file_explorer.path_label.setText(display_path)
            self.builder.window.file_explorer.path_card.show()
            self.builder.window.file_explorer.back_btn.setEnabled(False)
            self.builder.window.file_explorer.empty_label.hide()
            self.builder.window.file_explorer.file_tree.show()
            self.builder.window.file_explorer._load_directory(resourcepacks_path)

    def _choose_instance_path(self):
        """选择Minecraft路径"""
        from PyQt6.QtWidgets import QFileDialog
        path = QFileDialog.getExistingDirectory(
            self.builder.window,
            self.builder.text_renderer.translate("instance_path_dialog_title"),
            ""
        )
        if path:
            self.builder.window.instance_path_input.setText(path)
            self._on_instance_path_changed()

    def _on_instance_path_changed(self):
        """Minecraft路径变化"""
        try:
            path = self.builder.window.instance_path_input.text().strip()
            if path and os.path.exists(path):
                self.builder.window.config["minecraft_path"] = path
                self.builder.window.config_manager.save_config()
                self._load_version_list(path)
            else:
                self._clear_version_list()
                if hasattr(self.builder.window, 'download_version_combo'):
                    self.builder.window.download_version_combo.clear()
        except Exception as e:
            logger.error(f"Error loading version list: {e}")
            pass

    def _load_version_list(self, minecraft_path):
        """加载Minecraft版本列表（显示为可点击的卡片）"""
        try:
            # 如果版本隔离关闭，直接在版本列表位置显示根目录材质包
            if not self.builder.window.config.get("version_isolation", True):
                self._clear_version_list()
                if hasattr(self.builder.window, 'instance_version_container'):
                    self.builder.window.instance_version_container.setVisible(False)
                if hasattr(self.builder.window, 'root_resourcepacks_container'):
                    self.builder.window.root_resourcepacks_container.setVisible(True)
                    root_resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
                    if os.path.exists(root_resourcepacks_path):
                        self.builder.window.root_resourcepacks_explorer.set_resourcepacks_path(
                            root_resourcepacks_path, minecraft_path
                        )
                return

            # 显示版本容器，隐藏根目录材质包容器
            if hasattr(self.builder.window, 'instance_version_container'):
                self.builder.window.instance_version_container.setVisible(True)
            if hasattr(self.builder.window, 'root_resourcepacks_container'):
                self.builder.window.root_resourcepacks_container.setVisible(False)

            versions_path = os.path.join(minecraft_path, "versions")
            self._clear_version_list()

            # 获取收藏的版本列表
            favorited_versions = self.builder.window.config.get("favorited_versions", [])

            # 收集所有版本
            all_versions = []
            if os.path.exists(versions_path) and os.path.isdir(versions_path):
                for item in sorted(os.listdir(versions_path)):
                    item_path = os.path.join(versions_path, item)
                    if os.path.isdir(item_path):
                        all_versions.append(item)

            # 将版本分为收藏和非收藏两组
            favorites = [v for v in all_versions if v in favorited_versions]
            non_favorites = [v for v in all_versions if v not in favorited_versions]

            # 先添加收藏的版本
            for version in favorites:
                self._add_version_item(minecraft_path, version, is_version=True, is_favorited=True)

            # 再添加非收藏的版本
            for version in non_favorites:
                self._add_version_item(minecraft_path, version, is_version=True, is_favorited=False)

        except Exception as e:
            logger.error(f"Error loading version list: {e}")
            pass

    def _clear_version_list(self):
        """清空版本列表"""
        if hasattr(self.builder.window, 'instance_version_list_container'):
            while self.builder.window.instance_version_list_container.count() > 0:
                child = self.builder.window.instance_version_list_container.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

    def _add_version_item(self, minecraft_path, version_name, is_version=False, is_favorited=False):
        """添加一个版本项到列表"""
        from widgets import make_transparent
        from .components import VersionCardWidget

        # 创建版本卡片
        version_card = VersionCardWidget()
        version_card.setFixedHeight(self.builder._scale_size(48))

        normal_style = f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.08);
                border-radius: {self.builder._scale_size(8)}px;
            }}
        """
        hover_style = f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.15);
                border-radius: {self.builder._scale_size(8)}px;
            }}
        """
        version_card.set_styles(normal_style, hover_style)
        version_card.setStyleSheet(normal_style)
        version_card.setCursor(Qt.CursorShape.PointingHandCursor)

        # 确定资源包路径和显示名称
        if is_version:
            resourcepacks_path = os.path.join(minecraft_path, "versions", version_name, "resourcepacks")
            version_aliases = self.builder.window.config.get("version_aliases", {})
            display_name = version_aliases.get(version_name, version_name)
        else:
            resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
            display_name = self.builder.window.language_manager.translate("instance_version_root")

        # 卡片内容布局
        card_layout = QHBoxLayout(version_card)
        card_layout.setContentsMargins(self.builder._scale_size(12), 0, self.builder._scale_size(12), 0)
        card_layout.setSpacing(self.builder._scale_size(10))

        # 创建点击区域容器
        click_area = ClickableLabel()
        click_area.setStyleSheet("background:transparent;")
        click_area.setCallback(lambda rp=resourcepacks_path, dn=display_name: self._navigate_to_resourcepack_page(dn, rp))
        click_area_layout = QHBoxLayout(click_area)
        click_area_layout.setContentsMargins(0, 0, 0, 0)
        click_area_layout.setSpacing(self.builder._scale_size(10))

        # 图标
        icon_label = QLabel()
        icon_label.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
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
            else:
                icon_path = "png/block.png"

            # 获取 PNG 文件的正确路径
            if hasattr(sys, '_MEIPASS'):
                png_path = os.path.join(sys._MEIPASS, icon_path.replace('\\', os.sep))
                if not os.path.exists(png_path):
                    png_path = os.path.join(os.getcwd(), icon_path.replace('\\', os.sep))
            else:
                png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", icon_path.replace('\\', os.sep))
                png_path = os.path.abspath(png_path)

            icon_pixmap = QPixmap(png_path)
            if not icon_pixmap.isNull():
                scaled_pixmap = icon_pixmap.scaled(
                    int(20 * self.builder.dpi_scale),
                    int(20 * self.builder.dpi_scale),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                icon_label.setPixmap(scaled_pixmap)
        else:
            icon_pixmap = load_svg_icon("svg/box-fill.svg", self.builder.dpi_scale)
            if icon_pixmap:
                icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.builder.dpi_scale))

        click_area_layout.addWidget(icon_label)

        # 版本名称
        name_label = QLabel(display_name)
        name_label.setStyleSheet(
            f"color:white;font-size:{self.builder._scale_size(14)}px;"
            f"font-family:'{self.builder._get_font_family()}';background:transparent;"
        )
        click_area_layout.addWidget(name_label)
        click_area_layout.addStretch()

        # 箭头图标
        arrow_label = QLabel()
        arrow_label.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
        arrow_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow_label.setStyleSheet("background:transparent;")
        arrow_pixmap = load_svg_icon("svg/arrow-bar-right.svg", self.builder.dpi_scale)
        if arrow_pixmap:
            arrow_label.setPixmap(scale_icon_for_display(arrow_pixmap, 16, self.builder.dpi_scale))
        click_area_layout.addWidget(arrow_label)

        card_layout.addWidget(click_area)

        # 收藏按钮和编辑按钮（仅对版本显示）
        bookmark_btn = None
        edit_btn = None

        if is_version:
            # 编辑按钮
            from PyQt6.QtWidgets import QPushButton
            from PyQt6.QtGui import QIcon

            edit_btn = QPushButton()
            edit_btn.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
            edit_btn.hide()
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

            edit_pixmap = load_svg_icon("svg/pencil-square.svg", self.builder.dpi_scale)
            if edit_pixmap:
                edit_btn.setIcon(QIcon(scale_icon_for_display(edit_pixmap, 16, self.builder.dpi_scale)))

            version_card.set_edit_button(edit_btn)
            card_layout.addWidget(edit_btn)

            # 收藏按钮
            bookmark_btn = QPushButton()
            bookmark_btn.setFixedSize(self.builder._scale_size(20), self.builder._scale_size(20))
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

            if is_favorited:
                bookmark_pixmap = load_svg_icon("svg/bookmarks-fill.svg", self.builder.dpi_scale)
            else:
                bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self.builder.dpi_scale)

            if bookmark_pixmap:
                bookmark_btn.setIcon(QIcon(scale_icon_for_display(bookmark_pixmap, 16, self.builder.dpi_scale)))

            version_card.set_bookmark_info(bookmark_btn, is_favorited)

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

        self.builder.window.instance_version_list_container.addWidget(version_card)

    def _navigate_to_resourcepack_page(self, title, resourcepacks_path):
        """导航到资源包页面（第二层）"""
        logger.info(f"Navigating to resourcepack page: {title}, path: {normalize_path(resourcepacks_path)}")

        # 检查是否已经存在相同路径的资源包页面
        for i in range(self.builder.window.instance_stack.count()):
            widget = self.builder.window.instance_stack.widget(i)
            if hasattr(widget, '_resourcepacks_path') and widget._resourcepacks_path == resourcepacks_path:
                self.builder.window.instance_stack.setCurrentIndex(i)
                return

        # 创建新的资源包页面
        resourcepack_page = self._create_instance_resourcepack_page(title, resourcepacks_path)
        resourcepack_page._resourcepacks_path = resourcepacks_path
        self.builder.window.instance_stack.addWidget(resourcepack_page)
        self.builder.window.instance_stack.setCurrentWidget(resourcepack_page)

    def _navigate_instance_back(self):
        """返回上一页"""
        count = self.builder.window.instance_stack.count()
        if count <= 1:
            return

        widget_to_remove = self.builder.window.instance_stack.currentWidget()
        self.builder.window.instance_stack.removeWidget(widget_to_remove)
        widget_to_remove.deleteLater()

    def _close_all_version_pages(self):
        """关闭所有版本资源包页面，返回到主页面"""
        count = self.builder.window.instance_stack.count()
        # 只保留第一页（主页面），删除所有其他页面
        while count > 1:
            widget_to_remove = self.builder.window.instance_stack.widget(1)
            if widget_to_remove:
                self.builder.window.instance_stack.removeWidget(widget_to_remove)
                widget_to_remove.deleteLater()
            count = self.builder.window.instance_stack.count()
        # 确保返回到主页面
        self.builder.window.instance_stack.setCurrentIndex(0)

    def _navigate_to_config_editor_page(self, full_path, name):
        """导航到资源包配置编辑器页面"""
        try:
            from widgets.resourcepack_config_editor_page import ResourcepackConfigEditorPage

            # 保存当前页面（文件浏览器页面）
            current_page = self.builder.window.instance_stack.currentWidget()

            # 创建并添加配置编辑器页面
            config_page = ResourcepackConfigEditorPage(
                parent=self.builder.window.instance_stack,
                full_path=full_path,
                dpi_scale=self.builder.dpi_scale,
                text_renderer=self.builder.text_renderer,
                on_back=lambda: self._navigate_back_from_config(current_page)
            )

            # 缓存配置编辑器页面
            self._config_editor_page = config_page

            # 添加到堆叠窗口并导航
            self.builder.window.instance_stack.addWidget(config_page)
            self.builder.window.instance_stack.setCurrentWidget(config_page)
        except Exception as e:
            logger.error(f"Error navigating to config editor page: {e}")
            import traceback
            traceback.print_exc()
    
    def _navigate_back_from_config(self, previous_page):
        """从配置编辑器页面返回"""
        try:
            if hasattr(self, '_config_editor_page') and self._config_editor_page:
                self.builder.window.instance_stack.removeWidget(self._config_editor_page)
                self._config_editor_page.deleteLater()
                self._config_editor_page = None
        except Exception as e:
            logger.error(f"Error removing config editor page: {e}")

        # 返回到之前的页面
        if previous_page:
            try:
                self.builder.window.instance_stack.setCurrentWidget(previous_page)
            except Exception as e:
                logger.error(f"Error setting current widget: {e}")
                # 如果出错，尝试返回到第一个页面
                try:
                    self.builder.window.instance_stack.setCurrentIndex(0)
                except:
                    pass

    def _detect_version_type(self, minecraft_path, version_name):
        """检测Minecraft版本类型（fabric/forge/neoforge/vanilla）"""
        try:
            version_path = os.path.join(minecraft_path, "versions", version_name)
            if not os.path.exists(version_path):
                return "vanilla"

            # 查找版本jar文件或目录
            version_jar = os.path.join(version_path, version_name + ".jar")
            if not os.path.exists(version_jar):
                version_jar = os.path.join(version_path, version_name)
                if os.path.isdir(version_jar):
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

                    if "inheritsFrom" in json_data:
                        parent_version = json_data["inheritsFrom"]
                        if "forge" in version_name.lower():
                            return "forge"
                        elif "neoforge" in version_name.lower():
                            return "neoforge"
                        elif "fabric" in version_name.lower():
                            return "fabric"

                    if "id" in json_data:
                        version_id = json_data["id"].lower()
                        if "forge" in version_id and "neoforge" not in version_id:
                            return "forge"
                        elif "neoforge" in version_id:
                            return "neoforge"
                        elif "fabric" in version_id:
                            return "fabric"

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
                    mod_json_files = [f for f in jar_file.namelist() if 'fabric.mod.json' in f]
                    if mod_json_files:
                        return "fabric"

                    mods_toml_files = [f for f in jar_file.namelist() if 'mods.toml' in f]
                    if mods_toml_files:
                        for f in jar_file.namelist():
                            if 'neoforge' in f.lower():
                                return "neoforge"
                        return "forge"
            except:
                pass

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
        current_name = name_label.text()

        # 获取主窗口背景模式，使用相同的背景设置
        background_mode = self.builder.window.config.get("background_mode", "blur")

        if background_mode == "blur":
            blur_opacity = self.builder.window.config.get("blur_opacity", 150)
            dialog_opacity = min(255, blur_opacity + 50)
            opacity_alpha = dialog_opacity / 255.0
            dialog_style = f"""
                QDialog {{
                    background: rgba(0, 0, 0, {opacity_alpha});
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self.builder._scale_size(12)}px;
                }}
            """
        elif background_mode == "solid":
            bg_color = self.builder.window.config.get("background_color", "#00000000")
            dialog_style = f"""
                QDialog {{
                    background: {bg_color};
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self.builder._scale_size(12)}px;
                }}
            """
        else:
            blur_opacity = self.builder.window.config.get("blur_opacity", 150)
            dialog_opacity = min(255, blur_opacity + 50)
            opacity_alpha = dialog_opacity / 255.0
            dialog_style = f"""
                QDialog {{
                    background: rgba(0, 0, 0, {opacity_alpha});
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {self.builder._scale_size(12)}px;
                }}
            """

        # 创建自定义对话框（无标题栏）
        dialog = QDialog(self.builder.window)
        dialog.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        dialog.setFixedSize(self.builder._scale_size(400), self.builder._scale_size(180))
        dialog.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        dialog.setStyleSheet(dialog_style)

        # 对话框布局
        dialog_layout = QVBoxLayout(dialog)
        dialog_layout.setContentsMargins(
            self.builder._scale_size(24), self.builder._scale_size(24),
            self.builder._scale_size(24), self.builder._scale_size(24)
        )
        dialog_layout.setSpacing(self.builder._scale_size(16))

        # 标题标签
        title_label = QLabel()
        self.builder.text_renderer.register_widget(title_label, "edit_version_name_title", group="instance_page")
        title_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
                font-size: {self.builder._scale_size(14)}px;
                font-family: '{self.builder._get_font_family()}';
            }}
        """)
        dialog_layout.addWidget(title_label)

        # 输入框
        input_field = QLineEdit(current_name)
        input_field.setFixedHeight(self.builder._scale_size(36))
        input_field.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self.builder._scale_size(6)}px;
                padding: 0 {self.builder._scale_size(12)}px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {self.builder._scale_size(14)}px;
                font-family: '{self.builder._get_font_family()}';
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(100, 150, 255, 0.6);
            }}
        """)
        input_field.selectAll()
        dialog_layout.addWidget(input_field)

        dialog_layout.addStretch()

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.setSpacing(self.builder._scale_size(10))

        # 取消按钮
        cancel_btn = QPushButton()
        self.builder.text_renderer.register_widget(cancel_btn, "cancel", group="instance_page")
        cancel_btn.setFixedHeight(self.builder._scale_size(36))
        cancel_btn.setFixedWidth(self.builder._scale_size(100))
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {self.builder._scale_size(6)}px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {self.builder._scale_size(13)}px;
                font-family: '{self.builder._get_font_family()}';
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

        # 确认按钮
        confirm_btn = QPushButton()
        self.builder.text_renderer.register_widget(confirm_btn, "confirm", group="instance_page")
        confirm_btn.setFixedHeight(self.builder._scale_size(36))
        confirm_btn.setFixedWidth(self.builder._scale_size(100))
        confirm_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(100, 150, 255, 0.8);
                border: none;
                border-radius: {self.builder._scale_size(6)}px;
                color: white;
                font-size: {self.builder._scale_size(13)}px;
                font-family: '{self.builder._get_font_family()}';
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

        dialog.setWindowModality(Qt.WindowModality.ApplicationModal)
        input_field.setFocus()

        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            new_name = input_field.text().strip()
            if new_name:
                version_aliases = self.builder.window.config.get("version_aliases", {})

                if new_name == original_name:
                    if original_name in version_aliases:
                        del version_aliases[original_name]
                        self.builder.window.config_manager.set("version_aliases", version_aliases)
                        name_label.setText(original_name)
                else:
                    version_aliases[original_name] = new_name
                    self.builder.window.config_manager.set("version_aliases", version_aliases)
                    name_label.setText(new_name)

    def _toggle_favorite_version(self, version_name):
        """切换版本的收藏状态"""
        favorited_versions = self.builder.window.config.get("favorited_versions", [])

        if version_name in favorited_versions:
            favorited_versions.remove(version_name)
        else:
            favorited_versions.append(version_name)

        self.builder.window.config_manager.set("favorited_versions", favorited_versions)

        saved_path = self.builder.window.config.get("minecraft_path", "")
        if saved_path:
            self._load_version_list(saved_path)
