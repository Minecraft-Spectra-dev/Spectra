"""UI构建器 - 重构后的主文件

负责整合各个页面构建器，提供统一的UI构建接口
"""

import os
import sys
import logging
from PyQt6.QtCore import Qt, QEvent, QThread, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap, QIcon
from PyQt6.QtWidgets import (QColorDialog, QHBoxLayout, QLabel, QLineEdit,
                             QPushButton, QSlider, QVBoxLayout, QWidget,
                             QComboBox, QMenu, QScrollArea)

from styles import SLIDER_STYLE, STYLE_BTN, STYLE_ICON
from utils import load_svg_icon, scale_icon_for_display
from widgets import (CardButton, ClickableLabel, JellyButton,
                      get_current_font, make_transparent, set_current_font,
                      TextRenderer, ModrinthResultCard)

# 导入重构后的模块
from .components import VersionCardWidget, ToggleSwitch
from .styles import StyleMixin
from .download_thread import DownloadThread
from .console_page import ConsolePageBuilder
from .settings_page import SettingsPageBuilder
from .instances_page import InstancesPageBuilder
from .downloads_page import DownloadsPageBuilder

logger = logging.getLogger(__name__)


class UIBuilder(StyleMixin):
    """UI构建器主类

    整合各个页面构建器，提供统一的UI构建接口
    """

    def __init__(self, window):
        self.window = window
        self.dpi_scale = getattr(window, 'dpi_scale', 1.0)
        # 获取 window 的 text_renderer，如果没有则创建一个新的
        self.text_renderer = getattr(window, 'text_renderer', None)
        if self.text_renderer is None:
            self.text_renderer = TextRenderer(getattr(window, 'language_manager', None))
            self.text_renderer.set_dpi_scale(self.dpi_scale)

        # 初始化各个页面构建器
        self.console_page_builder = ConsolePageBuilder(self)
        self.settings_page_builder = SettingsPageBuilder(self)
        self.instances_page_builder = InstancesPageBuilder(self)
        self.downloads_page_builder = DownloadsPageBuilder(self)

    def _scale_size(self, size):
        """缩放尺寸"""
        return int(size * self.dpi_scale)

    def _get_font_family(self):
        """获取当前字体系列"""
        return get_current_font()

    def _create_scroll_area(self, parent=None):
        """创建统一的滚动区域"""
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

    def _create_label_with_style(self, text, font_size=13, color="rgba(255,255,255,0.8)"):
        """创建带统一样式的标签"""
        label = QLabel(text)
        label.setStyleSheet(
            f"color:{color};font-size:{self._scale_size(font_size)}px;font-family:'{self._get_font_family()}';"
        )
        return label

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
        """创建标题按钮"""
        b = JellyButton(text)
        b.setFixedSize(self._scale_size(32), self._scale_size(32))
        font_size = self._scale_size(16)
        b.setStyleSheet(
            f"QPushButton{{background:transparent;color:white;border:none;border-radius:{self._scale_size(16)}px;font-size:{font_size}px;font-family:'{self._get_font_family()}';}}QPushButton:hover{{background:rgba(255,255,255,0.2);}}"
        )
        b.clicked.connect(handler)
        return b

    def create_bg_card(self, title, desc, selected, handler):
        """创建背景卡片"""
        card = CardButton()
        card.setFixedHeight(self._scale_size(70))
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        card.clicked.connect(handler)

        style = "background:rgba(255,255,255,0.15);" if selected else "background:rgba(255,255,255,0.05);"
        card.setStyleSheet(
            f"QPushButton{{{style}border:none;border-radius:0px;}}QPushButton:hover{{background:rgba(255,255,255,0.1);}}QPushButton:pressed{{background:rgba(255,255,255,0.05);}}"
        )

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
            f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:'{self._get_font_family()}';background:transparent;"
        )
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        layout.addLayout(text_layout)
        layout.addStretch()

        card.check_label = check_label
        return card

    def create_config_page(self):
        """创建设置页面"""
        return self.settings_page_builder.create_config_page()

    def create_instance_page(self):
        """创建实例页面"""
        return self.instances_page_builder.create_instance_page()

    def create_download_page(self):
        """创建下载页面"""
        return self.downloads_page_builder.create_download_page()

    def create_console_page(self):
        """创建控制台页面"""
        return self.console_page_builder.create_console_page()

    # 页面更新相关方法

    def _update_page_titles(self):
        """更新页面标题"""
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
        self.console_page_builder.update_page_title()

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

        for i in range(self.window.instance_version_list_container.count()):
            item = self.window.instance_version_list_container.itemAt(i)
            if item and item.widget():
                card = item.widget()
                card_layout = card.layout()
                if card_layout and card_layout.count() > 0:
                    click_area = card_layout.itemAt(0).widget()
                    if click_area and click_area.layout():
                        if click_area.layout().count() > 1:
                            name_label = click_area.layout().itemAt(1).widget()
                            if name_label and hasattr(name_label, 'setText'):
                                current_text = name_label.text()
                                if current_text in ["Root Directory", "根目录", root_text]:
                                    name_label.setText(root_text)

        # 更新资源包页面的标题
        if hasattr(self.window, 'resourcepack_page_title') and self.window.resourcepack_page_title:
            try:
                if not self.window.resourcepack_page_title.isVisible():
                    pass
                else:
                    current_title = self.window.resourcepack_page_title.text()
                    if current_title in ["Root Directory", "根目录", root_text]:
                        self.window.resourcepack_page_title.setText(root_text)
            except RuntimeError:
                pass

    def _update_settings_page(self):
        """更新设置页面的文本"""
        # 这个方法需要从 settings_page_builder 中实现
        pass

    def _update_settings_font(self, font_family):
        """更新设置页面的字体"""
        # 这个方法需要从 settings_page_builder 中实现
        pass

    def _refresh_instance_page(self):
        """刷新实例页面（当版本隔离设置变化时调用）"""
        self.instances_page_builder._load_version_list(
            self.window.config.get("minecraft_path", "")
        )

    def _update_bg_card(self, card, title_key, desc_key):
        """更新卡片的标题和描述文本"""
        if not card or not card.layout():
            return

        layout = card.layout()
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.layout(), QHBoxLayout):
                inner_layout = item.layout()
                for j in range(inner_layout.count()):
                    inner_item = inner_layout.itemAt(j)
                    if inner_item and isinstance(inner_item.layout(), QVBoxLayout):
                        text_layout = inner_item.layout()
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
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item and isinstance(item.layout(), QHBoxLayout):
                inner_layout = item.layout()
                for j in range(inner_layout.count()):
                    inner_item = inner_layout.layout()
                    if inner_item and isinstance(inner_item.layout(), QVBoxLayout):
                        text_layout = inner_item.layout()
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
        for i in range(header_layout.count()):
            item = header_layout.itemAt(i)
            if item and isinstance(item.layout(), QVBoxLayout):
                text_layout = item.layout()
                if text_layout.count() >= 2:
                    title = text_layout.itemAt(0).widget()
                    desc = text_layout.itemAt(1).widget()
                    if title:
                        title.setStyleSheet(f"color:white;font-size:{self._scale_size(14)}px;font-family:{font_family};background:transparent;")
                    if desc:
                        desc.setStyleSheet(f"color:rgba(255,255,255,0.6);font-size:{self._scale_size(12)}px;font-family:{font_family};background:transparent;")
                    break

    def _update_platform_button_texts(self):
        """更新平台按钮的文本"""
        if hasattr(self.window, 'download_platform_buttons'):
            current_index = self.window.current_download_platform
            for i, button in enumerate(self.window.download_platform_buttons):
                if i == 0:
                    button.setText(self.window.language_manager.translate("download_platform_all"))
                elif i == 1:
                    button.setText(self.window.language_manager.translate("download_platform_modrinth"))
                elif i == 2:
                    button.setText(self.window.language_manager.translate("download_platform_curseforge"))
                self.downloads_page_builder._setup_platform_button(button, i == current_index, i)

    # 下载相关方法（代理到 downloads_page_builder）

    def get_download_target_path(self):
        """获取下载目标路径"""
        return self.downloads_page_builder.get_download_target_path() if hasattr(self.downloads_page_builder, 'get_download_target_path') else None

    def _search_modrinth(self, query, page=1, sort_by="relevance"):
        """搜索 Modrinth"""
        self.downloads_page_builder._search_modrinth(query, page, sort_by)

    # 实例页面相关方法（代理到 instances_page_builder）

    def _on_instance_path_changed(self):
        """Minecraft路径变化"""
        self.instances_page_builder._on_instance_path_changed()

    def _load_version_list(self, minecraft_path):
        """加载Minecraft版本列表"""
        self.instances_page_builder._load_version_list(minecraft_path)

    def _clear_version_list(self):
        """清空版本列表"""
        self.instances_page_builder._clear_version_list()

    # 下载回调方法（保留在主文件中，方便访问）

    def _on_download_modrinth_project(self, project_data, checked=False):
        """下载 Modrinth 项目"""
        project_title = project_data.get('title', 'Unknown')
        logger.info(f"Downloading project: {project_title}")

        if hasattr(self.window, '_download_thread') and self.window._download_thread:
            logger.warning("A download is already in progress")
            return

        target_path = self.downloads_page_builder.get_download_target_path() if hasattr(self.downloads_page_builder, 'get_download_target_path') else None
        if not target_path:
            logger.error("No target path configured")
            return

        os.makedirs(target_path, exist_ok=True)

        project_id = project_data.get('project_id', '')
        if hasattr(self.window, 'download_cards'):
            for card in self.window.download_cards:
                if card.project_data.get('project_id') == project_id:
                    card.set_downloading_status(True)
                    break

        self.window._download_thread = DownloadThread(
            project_data, target_path,
            language_manager=self.window.language_manager
        )
        self.window._download_thread.download_complete.connect(self._on_download_complete)
        self.window._download_thread.download_error.connect(self._on_download_error)
        self.window._download_thread.download_progress.connect(self._on_download_progress)
        self.window._download_thread.finished.connect(self._on_download_thread_finished)
        self.window._download_thread.start()

    def _on_download_complete(self, file_path, filename):
        """下载完成回调"""
        project_id = None
        if hasattr(self.window, '_download_thread'):
            project_id = self.window._download_thread.project_data.get('project_id', '')

        if hasattr(self.window, 'download_cards') and project_id:
            for card in self.window.download_cards:
                if card.project_data.get('project_id') == project_id:
                    card.set_downloading_status(False)
                    card._set_downloaded_status(True)
                    break

        if hasattr(self.window, '_refresh_file_browser'):
            self.window._refresh_file_browser()

    def _on_download_error(self, error_message):
        """下载错误回调"""
        logger.error(f"Download error: {error_message}")

        project_id = None
        if hasattr(self.window, '_download_thread'):
            project_id = self.window._download_thread.project_data.get('project_id', '')

        if hasattr(self.window, 'download_cards') and project_id:
            for card in self.window.download_cards:
                if card.project_data.get('project_id') == project_id:
                    card.set_downloading_status(False)
                    break

        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            self.window,
            "Download Error" if not self.window.language_manager
                else self.window.language_manager.translate("download_error_title"),
            error_message
        )

    def _on_download_progress(self, downloaded, total):
        """下载进度回调"""
        logger.debug(f"Download progress: {downloaded}/{total}")

        if total > 0:
            progress = int((downloaded / total) * 100)
            if hasattr(self.window, '_download_thread') and hasattr(self.window, 'download_cards'):
                project_id = self.window._download_thread.project_data.get('project_id', '')
                if project_id:
                    for card in self.window.download_cards:
                        if card.project_data.get('project_id') == project_id:
                            card.update_download_progress(progress)
                            break

    def _on_download_thread_finished(self):
        """下载线程完成回调"""
        if hasattr(self.window, '_download_thread'):
            thread = self.window._download_thread

            if hasattr(thread, 'skipped') and thread.skipped:
                project_id = thread.project_data.get('project_id', '')
                if hasattr(self.window, 'download_cards') and project_id:
                    for card in self.window.download_cards:
                        if card.project_data.get('project_id') == project_id:
                            card.set_downloading_status(False)
                            card._set_downloaded_status(True)
                            break

            self.window._download_thread.deleteLater()
            self.window._download_thread = None
            logger.info("Download thread cleaned up")


# 导出的类和组件已经在模块顶部导入，无需重新导出
