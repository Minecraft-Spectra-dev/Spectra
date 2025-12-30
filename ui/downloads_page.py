"""下载页面模块

提供下载页面的创建和Modrinth搜索功能
"""

import logging
import os
from PyQt6.QtCore import Qt, QThread, QTimer, QSize
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QMenu, QComboBox
from PyQt6.QtGui import QIcon

from utils import load_svg_icon, scale_icon_for_display, normalize_path

logger = logging.getLogger(__name__)


class DownloadsPageBuilder:
    """下载页面构建器"""

    def __init__(self, builder):
        self.builder = builder

    def create_download_page(self):
        """创建下载页面"""
        page = QWidget()
        page.setStyleSheet("background:transparent;")
        pl = QVBoxLayout(page)
        pl.setContentsMargins(
            self.builder._scale_size(20), self.builder._scale_size(10),
            self.builder._scale_size(20), self.builder._scale_size(20)
        )
        pl.setSpacing(self.builder._scale_size(15))

        # 使用统一的标题创建方法
        title = self.builder._create_page_title(self.builder.window.language_manager.translate("page_downloads"))
        pl.addWidget(title)

        # 搜索框、搜索按钮和版本选择
        search_container = self._create_search_container()
        pl.addWidget(search_container)

        # 平台选择和筛选排序按钮容器
        controls_container = self._create_controls_container()
        pl.addWidget(controls_container)

        # 滚动区域
        scroll_area = self.builder._create_scroll_area()
        scroll_content, scroll_layout = self.builder._create_scroll_content()

        # 顶部翻页控件
        top_pagination = self._create_pagination_control()
        self.builder.window.download_top_pagination = top_pagination
        top_pagination.setVisible(False)
        scroll_layout.addWidget(top_pagination)

        scroll_layout.addStretch()

        self.builder.window.download_scroll_content = scroll_content
        self.builder.window.download_scroll_layout = scroll_layout

        scroll_area.setWidget(scroll_content)
        pl.addWidget(scroll_area, 1)

        # 加载 Minecraft 版本列表到下拉框
        self._load_versions_to_download_combo()

        return page

    def _create_search_container(self):
        """创建搜索容器"""
        from utils import load_svg_icon, scale_icon_for_display

        search_container = QWidget()
        search_container.setStyleSheet(
            f"background:rgba(255,255,255,0.08);border-radius:{self.builder._scale_size(8)}px;"
        )
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(
            self.builder._scale_size(12), self.builder._scale_size(8),
            self.builder._scale_size(12), self.builder._scale_size(8)
        )
        search_layout.setSpacing(self.builder._scale_size(10))

        # 搜索输入框
        self.builder.window.download_search = QLineEdit()
        self.builder.window.download_search.setPlaceholderText("Search downloads...")
        x_pixmap = load_svg_icon("svg/x.svg", self.builder.dpi_scale)
        if x_pixmap:
            lineedit_stylesheet = self.builder._get_lineedit_stylesheet()
            lineedit_stylesheet += (
                f"QLineEdit::clear-button {{ image: url(svg/x.svg); }} "
                f"QLineEdit::clear-button:hover {{ image: url(svg/x.svg); }}"
            )
            self.builder.window.download_search.setStyleSheet(lineedit_stylesheet)
        else:
            self.builder.window.download_search.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.window.download_search.setClearButtonEnabled(True)
        self.builder.window.download_search.returnPressed.connect(self._on_search_clicked)
        search_layout.addWidget(self.builder.window.download_search, 3)

        # 注册到 TextRenderer
        self.builder.text_renderer.register_widget(
            self.builder.window.download_search,
            "download_search_placeholder",
            update_method="setPlaceholderText",
            group="download_page"
        )

        # 搜索按钮
        search_btn = QPushButton()
        search_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
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
        search_pixmap = load_svg_icon("svg/search.svg", self.builder.dpi_scale)
        if search_pixmap:
            search_btn.setIcon(QIcon(scale_icon_for_display(search_pixmap, 16, self.builder.dpi_scale)))
            search_btn.setIconSize(QSize(self.builder._scale_size(16), self.builder._scale_size(16)))
        search_btn.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(search_btn)

        # 版本选择
        self.builder.window.download_version_combo = QComboBox()
        self.builder._setup_combobox(self.builder.window.download_version_combo, width=230)
        self.builder.window.download_version_combo.setVisible(
            self.builder.window.config.get("version_isolation", True)
        )
        self.builder.window.download_version_combo.currentIndexChanged.connect(self._on_download_version_changed)
        search_layout.addWidget(self.builder.window.download_version_combo, 2)

        return search_container

    def _create_controls_container(self):
        """创建控制容器（平台选择和筛选）"""
        controls_container = QWidget()
        controls_layout = QHBoxLayout(controls_container)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(self.builder._scale_size(10))

        # 平台选择按钮（三段式按钮）
        platform_container = QWidget()
        platform_container.setStyleSheet(
            f"background:rgba(255,255,255,0.05);border-radius:{self.builder._scale_size(8)}px;"
        )
        platform_layout = QHBoxLayout(platform_container)
        platform_layout.setContentsMargins(
            self.builder._scale_size(4), self.builder._scale_size(4),
            self.builder._scale_size(4), self.builder._scale_size(4)
        )
        platform_layout.setSpacing(0)

        # 全部按钮
        self.builder.window.download_platform_all = QPushButton(
            self.builder.window.language_manager.translate("download_platform_all")
        )
        self.builder.window.download_platform_all.setFixedSize(120, 32)
        self._setup_platform_button(self.builder.window.download_platform_all, True, 0)
        self.builder.window.download_platform_all.clicked.connect(lambda: self._on_platform_selected(0))
        platform_layout.addWidget(self.builder.window.download_platform_all)

        # Modrinth 按钮
        self.builder.window.download_platform_modrinth = QPushButton(
            self.builder.window.language_manager.translate("download_platform_modrinth")
        )
        self.builder.window.download_platform_modrinth.setFixedSize(160, 32)
        self._setup_platform_button(self.builder.window.download_platform_modrinth, False, 1)
        self.builder.window.download_platform_modrinth.clicked.connect(lambda: self._on_platform_selected(1))
        platform_layout.addWidget(self.builder.window.download_platform_modrinth)

        # CurseForge 按钮
        self.builder.window.download_platform_curseforge = QPushButton(
            self.builder.window.language_manager.translate("download_platform_curseforge")
        )
        self.builder.window.download_platform_curseforge.setFixedSize(160, 32)
        self._setup_platform_button(self.builder.window.download_platform_curseforge, False, 2)
        self.builder.window.download_platform_curseforge.clicked.connect(lambda: self._on_platform_selected(2))
        platform_layout.addWidget(self.builder.window.download_platform_curseforge)

        self.builder.window.download_platform_buttons = [
            self.builder.window.download_platform_all,
            self.builder.window.download_platform_modrinth,
            self.builder.window.download_platform_curseforge
        ]
        self.builder.window.current_download_platform = 0
        self.builder.window.download_current_page = 1
        self.builder.window.download_total_pages = 1
        self.builder.window.download_total_hits = 0
        self.builder.window.download_per_page = 20
        self.builder.window.download_last_query = ""

        controls_layout.addWidget(platform_container, 0, Qt.AlignmentFlag.AlignLeft)
        controls_layout.addStretch(1)

        # 筛选按钮
        from utils import load_svg_icon, scale_icon_for_display
        filter_btn = QPushButton()
        filter_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
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
        funnel_pixmap = load_svg_icon("svg/funnel.svg", self.builder.dpi_scale)
        if funnel_pixmap:
            filter_btn.setIcon(QIcon(scale_icon_for_display(funnel_pixmap, 16, self.builder.dpi_scale)))
            filter_btn.setIconSize(QSize(self.builder._scale_size(16), self.builder._scale_size(16)))
        controls_layout.addWidget(filter_btn)

        # 排序按钮
        sort_btn = QPushButton()
        sort_btn.setFixedSize(self.builder._scale_size(32), self.builder._scale_size(32))
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
        sort_pixmap = load_svg_icon("svg/sort-down.svg", self.builder.dpi_scale)
        if sort_pixmap:
            sort_btn.setIcon(QIcon(scale_icon_for_display(sort_pixmap, 16, self.builder.dpi_scale)))
            sort_btn.setIconSize(QSize(self.builder._scale_size(16), self.builder._scale_size(16)))
        sort_btn.clicked.connect(self._show_sort_menu)
        controls_layout.addWidget(sort_btn)

        self.builder.window.download_sort_btn = sort_btn
        self.builder.window.current_sort_type = "relevance"
        self.builder.window.current_sort_text = self.builder.window.language_manager.translate("download_sort_relevance")
        self.builder.window.download_page_initialized = False

        return controls_container

    def _setup_platform_button(self, button, is_selected, index):
        """设置平台按钮的样式"""
        border_radius = self.builder._scale_size(8)
        if index == 0:
            border_style = f"border-top-left-radius:{border_radius}px;border-bottom-left-radius:{border_radius}px;border-right:none;"
        elif index == 2:
            border_style = f"border-top-right-radius:{border_radius}px;border-bottom-right-radius:{border_radius}px;border-left:none;"
        else:
            border_style = "border:none;"

        if is_selected:
            button.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.15);
                    {border_style}
                    color: white;
                    font-size: {self.builder._scale_size(13)}px;
                    font-family: '{self.builder._get_font_family()}';
                }}
            """)
        else:
            button.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    {border_style}
                    color: rgba(255, 255, 255, 0.7);
                    font-size: {self.builder._scale_size(13)}px;
                    font-family: '{self.builder._get_font_family()}';
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.1);
                    color: rgba(255, 255, 255, 0.9);
                }}
            """)
        button.setCursor(Qt.CursorShape.PointingHandCursor)

    def _on_platform_selected(self, index):
        """平台选择事件处理"""
        self.builder.window.current_download_platform = index
        for i, button in enumerate(self.builder.window.download_platform_buttons):
            self._setup_platform_button(button, i == index, i)

    def _on_download_version_changed(self, index):
        """下载页面版本切换事件处理"""
        self._refresh_all_card_download_status()

    def _refresh_all_card_download_status(self):
        """刷新所有已显示卡片的下载状态"""
        if not hasattr(self.builder.window, 'download_scroll_layout'):
            return

        new_target_path = self.builder.get_download_target_path()
        logger.info(f"Version changed, new target path: {normalize_path(new_target_path)}")

        layout = self.builder.window.download_scroll_layout
        card_count = 0
        for i in range(layout.count()):
            widget = layout.itemAt(i).widget()
            if widget and hasattr(widget, 'refresh_download_status'):
                card_count += 1
                widget.refresh_download_status(new_target_path)

        logger.info(f"Refreshed download status for {card_count} cards")

    def _on_search_clicked(self):
        """搜索按钮点击事件处理"""
        query = self.builder.window.download_search.text().strip()
        if not query:
            return

        platform = self.builder.window.current_download_platform
        if platform == 1:  # Modrinth
            self._search_modrinth(query, sort_by="relevance")
        elif platform == 2:  # CurseForge
            logger.info(f"CurseForge search not implemented yet: {query}")
        else:  # 全部平台 - 默认搜索 Modrinth
            self._search_modrinth(query, sort_by="relevance")

    def _show_sort_menu(self):
        """显示排序菜单"""
        menu = QMenu(self.builder.window)
        menu.setStyleSheet("""
            QMenu {
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 4px;
                padding: 4px;
            }
            QMenu::item {
                background: transparent;
                color: rgba(255, 255, 255, 0.9);
                padding: 6px 24px;
                font-size: 13px;
            }
            QMenu::item:selected {
                background: rgba(255, 255, 255, 0.2);
            }
            QMenu::item:checked {
                background: rgba(255, 255, 255, 0.2);
            }
        """)

        sort_options = [
            ("relevance", self.builder.window.language_manager.translate("download_sort_relevance")),
            ("downloads", self.builder.window.language_manager.translate("download_sort_downloads")),
            ("follows", self.builder.window.language_manager.translate("download_sort_follows")),
            ("newest", self.builder.window.language_manager.translate("download_sort_newest")),
            ("updated", self.builder.window.language_manager.translate("download_sort_updated")),
        ]

        for sort_type, text in sort_options:
            action = menu.addAction(text)
            action.setCheckable(True)
            if sort_type == self.builder.window.current_sort_type:
                action.setChecked(True)
            action.triggered.connect(lambda checked, st=sort_type: self._on_sort_selected(st))

        button = self.builder.window.download_sort_btn
        menu.exec(button.mapToGlobal(button.rect().bottomLeft()))

    def _on_sort_selected(self, sort_type):
        """排序选项被选中"""
        self.builder.window.current_sort_type = sort_type

        sort_options_map = {
            "downloads": self.builder.window.language_manager.translate("download_sort_downloads"),
            "relevance": self.builder.window.language_manager.translate("download_sort_relevance"),
            "follows": self.builder.window.language_manager.translate("download_sort_follows"),
            "newest": self.builder.window.language_manager.translate("download_sort_newest"),
            "updated": self.builder.window.language_manager.translate("download_sort_updated"),
        }
        self.builder.window.current_sort_text = sort_options_map.get(sort_type, sort_type)

        query = self.builder.window.download_last_query
        if query:
            self._search_modrinth(query, page=1, sort_by=sort_type)
        else:
            self._search_modrinth("", page=1, sort_by=sort_type)

    def _search_modrinth(self, query, page=1, sort_by="relevance"):
        """搜索 Modrinth 项目"""
        from managers.modrinth_manager import ModrinthManager

        self.builder.window.download_last_query = query
        self.builder.window.download_current_page = page

        self._clear_search_results()
        self._show_loading_message()

        def do_search():
            try:
                manager = ModrinthManager()
                facets = [["project_type:resourcepack"]]
                offset = (page - 1) * self.builder.window.download_per_page
                result = manager.search_projects(
                    query, facets=facets,
                    limit=self.builder.window.download_per_page,
                    offset=offset,
                    index=sort_by
                )
                hits = result.get('hits', [])
                total_hits = result.get('total_hits', 0)
                QTimer.singleShot(0, lambda: self._on_modrinth_search_finished(hits, total_hits))
            except Exception as e:
                logger.error(f"Modrinth search failed: {e}")
                QTimer.singleShot(0, lambda: self._on_search_error(str(e)))

        QTimer.singleShot(50, do_search)

    def _clear_search_results(self):
        """清除搜索结果"""
        if hasattr(self.builder.window, 'download_scroll_layout'):
            layout = self.builder.window.download_scroll_layout

            widgets_to_skip = set()
            if hasattr(self.builder.window, 'download_top_pagination'):
                widgets_to_skip.add(self.builder.window.download_top_pagination)
            if hasattr(self.builder.window, 'download_bottom_pagination'):
                widgets_to_skip.add(self.builder.window.download_bottom_pagination)

            for i in range(layout.count() - 1, -1, -1):
                item = layout.itemAt(i)
                if item and item.widget():
                    widget = item.widget()
                    if widget in widgets_to_skip:
                        if widget == getattr(self.builder.window, 'download_bottom_pagination', None):
                            widget.hide()
                        continue
                    if i == layout.count() - 1:
                        continue
                    widget.setParent(None)
                    widget.deleteLater()

    def _show_loading_message(self):
        """显示加载消息"""
        if hasattr(self.builder.window, 'download_scroll_layout'):
            loading_text = self.builder.window.language_manager.translate("download_searching")
            loading_label = QLabel(loading_text)
            loading_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
            loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.builder.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, loading_label)

    def _on_modrinth_search_finished(self, hits, total_hits):
        """Modrinth 搜索完成"""
        self._clear_search_results()

        if not hits:
            self._show_no_results_message()
            return

        self.builder.window.download_total_hits = total_hits
        self.builder.window.download_total_pages = (total_hits + self.builder.window.download_per_page - 1) // self.builder.window.download_per_page
        self._update_pagination_controls()

        layout = self.builder.window.download_scroll_layout

        if self.builder.window.download_total_pages > 1:
            start_index = 1
        else:
            start_index = 0

        if not hasattr(self.builder.window, 'download_cards'):
            self.builder.window.download_cards = []

        for hit in hits:
            project_data = {
                'title': hit.get('title', self.builder.window.language_manager.translate("download_unknown_title")),
                'description': hit.get('description', ''),
                'icon_url': hit.get('icon_url', ''),
                'downloads': hit.get('downloads', 0),
                'follows': hit.get('follows', 0),
                'project_id': hit.get('project_id', ''),
                'slug': hit.get('slug', '')
            }

            def make_download_handler(data):
                return lambda checked=False: self.builder._on_download_modrinth_project(data)

            download_target_path = self.builder.get_download_target_path()

            from widgets import ModrinthResultCard
            result_card = ModrinthResultCard(
                project_data,
                dpi_scale=self.builder.dpi_scale,
                on_download=make_download_handler(project_data),
                download_target_path=download_target_path,
                language_manager=self.builder.window.language_manager,
                text_renderer=self.builder.text_renderer
            )

            self.builder.window.download_cards.append(result_card)
            layout.insertWidget(start_index, result_card)
            start_index += 1

        if self.builder.window.download_total_pages > 1:
            if not hasattr(self.builder.window, 'download_bottom_pagination') or self.builder.window.download_bottom_pagination is None:
                bottom_pagination = self._create_pagination_control()
                self.builder.window.download_bottom_pagination = bottom_pagination

            self.builder.window.download_bottom_pagination.setVisible(True)
            layout.insertWidget(layout.count() - 1, self.builder.window.download_bottom_pagination)
            self._update_bottom_pagination_control()

        logger.info(f"Modrinth search completed: {len(hits)} results found")

    def _show_no_results_message(self):
        """显示无结果消息"""
        if hasattr(self.builder.window, 'download_scroll_layout'):
            no_results_text = self.builder.window.language_manager.translate("download_no_results")
            no_results_label = QLabel(no_results_text)
            no_results_label.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 14px;")
            no_results_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.builder.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, no_results_label)

    def _on_search_error(self, error):
        """搜索错误处理"""
        self._clear_search_results()
        self._show_error_message(error)
        logger.error(f"Search error: {error}")

    def _show_error_message(self, error):
        """显示错误消息"""
        if hasattr(self.builder.window, 'download_scroll_layout'):
            error_template = self.builder.window.language_manager.translate(
                "download_search_failed", default="Search failed: {error}"
            )
            error_text = error_template.format(error=error)
            error_label = QLabel(error_text)
            error_label.setStyleSheet("color: rgba(255, 100, 100, 0.9); font-size: 14px;")
            error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout = self.builder.window.download_scroll_layout
            layout.insertWidget(layout.count() - 1, error_label)

    def _create_pagination_control(self):
        """创建翻页控件"""
        pagination_container = QWidget()
        pagination_container.setStyleSheet("background: rgba(255, 255, 255, 0.05); border-radius: 8px;")
        pagination_layout = QHBoxLayout(pagination_container)
        pagination_layout.setContentsMargins(
            self.builder._scale_size(12), self.builder._scale_size(6),
            self.builder._scale_size(12), self.builder._scale_size(6)
        )
        pagination_layout.setSpacing(self.builder._scale_size(8))

        # 上一页按钮
        from utils import load_svg_icon, scale_icon_for_display
        prev_btn = QPushButton()
        prev_btn.setFixedSize(self.builder._scale_size(28), self.builder._scale_size(28))
        prev_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        prev_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        prev_pixmap = load_svg_icon("svg/caret-left.svg", self.builder.dpi_scale)
        if prev_pixmap:
            prev_btn.setIcon(QIcon(scale_icon_for_display(prev_pixmap, 14, self.builder.dpi_scale)))
            prev_btn.setIconSize(QSize(self.builder._scale_size(14), self.builder._scale_size(14)))
        prev_btn.setEnabled(False)
        prev_btn.clicked.connect(self._on_prev_page)
        pagination_layout.addWidget(prev_btn)

        # 页面信息标签
        page_info_template = self.builder.window.language_manager.translate(
            "download_page_info", default="Page {current} of {total}"
        )
        page_info_text = page_info_template.format(current=1, total=1)
        page_info_label = QLabel(page_info_text)
        page_info_label.setStyleSheet("color: rgba(255, 255, 255, 0.8); font-size: 12px; background: transparent;")
        page_info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        pagination_layout.addWidget(page_info_label)

        # 下一页按钮
        next_btn = QPushButton()
        next_btn.setFixedSize(self.builder._scale_size(28), self.builder._scale_size(28))
        next_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        next_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.2);
            }
            QPushButton:disabled {
                background: rgba(255, 255, 255, 0.05);
            }
        """)
        next_pixmap = load_svg_icon("svg/caret-right.svg", self.builder.dpi_scale)
        if next_pixmap:
            next_btn.setIcon(QIcon(scale_icon_for_display(next_pixmap, 14, self.builder.dpi_scale)))
            next_btn.setIconSize(QSize(self.builder._scale_size(14), self.builder._scale_size(14)))
        next_btn.setEnabled(False)
        next_btn.clicked.connect(self._on_next_page)
        pagination_layout.addWidget(next_btn)

        pagination_layout.addStretch()

        # 页码输入框
        page_input = QLineEdit()
        page_input.setFixedHeight(self.builder._scale_size(24))
        page_input.setMaximumWidth(self.builder._scale_size(80))
        page_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        page_input.setPlaceholderText("1")
        page_input.setText("1")
        page_input.setStyleSheet(f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {self.builder._scale_size(4)}px;
                padding: {self.builder._scale_size(2)}px {self.builder._scale_size(6)}px;
                color: white;
                font-size: 11px;
            }}
            QLineEdit:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QLineEdit:focus {{
                border: 1px solid rgba(255, 255, 255, 0.4);
            }}
        """)
        page_input.returnPressed.connect(lambda: self._on_page_selected(page_input))
        pagination_layout.addWidget(page_input)

        pagination_container.prev_btn = prev_btn
        pagination_container.next_btn = next_btn
        pagination_container.page_info_label = page_info_label
        pagination_container.page_input = page_input

        return pagination_container

    def _update_pagination_controls(self):
        """更新顶部翻页控件状态"""
        if self.builder.window.download_total_pages > 1:
            self.builder.window.download_top_pagination.setVisible(True)
            page_info_template = self.builder.window.language_manager.translate(
                "download_page_info", default="Page {current} of {total}"
            )
            page_info_text = page_info_template.format(
                current=self.builder.window.download_current_page,
                total=self.builder.window.download_total_pages
            )
            self.builder.window.download_top_pagination.page_info_label.setText(page_info_text)
            self.builder.window.download_top_pagination.prev_btn.setEnabled(
                self.builder.window.download_current_page > 1
            )
            self.builder.window.download_top_pagination.next_btn.setEnabled(
                self.builder.window.download_current_page < self.builder.window.download_total_pages
            )
            self.builder.window.download_top_pagination.page_input.blockSignals(True)
            self.builder.window.download_top_pagination.page_input.setText(
                str(self.builder.window.download_current_page)
            )
            self.builder.window.download_top_pagination.page_input.blockSignals(False)
        else:
            self.builder.window.download_top_pagination.setVisible(False)

    def _update_bottom_pagination_control(self):
        """更新底部翻页控件状态"""
        if (hasattr(self.builder.window, 'download_bottom_pagination') and
                self.builder.window.download_bottom_pagination):
            page_info_template = self.builder.window.language_manager.translate(
                "download_page_info", default="Page {current} of {total}"
            )
            page_info_text = page_info_template.format(
                current=self.builder.window.download_current_page,
                total=self.builder.window.download_total_pages
            )
            self.builder.window.download_bottom_pagination.page_info_label.setText(page_info_text)
            self.builder.window.download_bottom_pagination.prev_btn.setEnabled(
                self.builder.window.download_current_page > 1
            )
            self.builder.window.download_bottom_pagination.next_btn.setEnabled(
                self.builder.window.download_current_page < self.builder.window.download_total_pages
            )
            self.builder.window.download_bottom_pagination.page_input.blockSignals(True)
            self.builder.window.download_bottom_pagination.page_input.setText(
                str(self.builder.window.download_current_page)
            )
            self.builder.window.download_bottom_pagination.page_input.blockSignals(False)

    def _on_prev_page(self):
        """上一页"""
        if self.builder.window.download_current_page > 1:
            self._search_modrinth(
                self.builder.window.download_last_query,
                self.builder.window.download_current_page - 1
            )

    def _on_next_page(self):
        """下一页"""
        if self.builder.window.download_current_page < self.builder.window.download_total_pages:
            self._search_modrinth(
                self.builder.window.download_last_query,
                self.builder.window.download_current_page + 1
            )

    def _on_page_selected(self, input_widget):
        """跳转到输入的页码"""
        try:
            page_input = input_widget.text().strip()
            if not page_input:
                return
            page = int(page_input)
            if page < 1:
                page = 1
            elif page > self.builder.window.download_total_pages:
                page = self.builder.window.download_total_pages
            if page != self.builder.window.download_current_page:
                self._search_modrinth(self.builder.window.download_last_query, page)
        except ValueError:
            pass

    def get_download_target_path(self):
        """获取下载目标路径（基于下拉框选择）"""
        try:
            minecraft_path = self.builder.window.config.get("minecraft_path", "")
            if not minecraft_path or not os.path.exists(minecraft_path):
                logger.warning(f"Invalid minecraft_path: {minecraft_path}")
                return None

            # 如果版本隔离关闭，直接返回根目录的resourcepacks路径
            if not self.builder.window.config.get("version_isolation", True):
                root_resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
                logger.info(f"Version isolation OFF, target path: {normalize_path(root_resourcepacks_path)}")
                return root_resourcepacks_path

            # 版本隔离开启时，根据下拉框选择返回对应路径
            selected_version = self.builder.window.download_version_combo.currentText()
            logger.info(f"Version isolation ON, selected version: {selected_version}")

            if selected_version:
                root_text = self.builder.window.language_manager.translate("instance_version_root")
                if selected_version == root_text:
                    root_resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
                    logger.info(f"Root directory selected, target path: {normalize_path(root_resourcepacks_path)}")
                    return root_resourcepacks_path
                else:
                    version_resourcepacks_path = os.path.join(minecraft_path, "versions", selected_version, "resourcepacks")
                    logger.info(f"Version selected, target path: {normalize_path(version_resourcepacks_path)}")
                    return version_resourcepacks_path

            root_resourcepacks_path = os.path.join(minecraft_path, "resourcepacks")
            logger.info(f"No version selected, default to root, target path: {normalize_path(root_resourcepacks_path)}")
            return root_resourcepacks_path
        except Exception as e:
            logger.error(f"Error getting download target path: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _load_versions_to_download_combo(self):
        """从.minecraft路径加载版本列表到下载页面的下拉框"""
        import os
        try:
            if not self.builder.window.config.get("version_isolation", True):
                self.builder.window.download_version_combo.clear()
                return

            minecraft_path = self.builder.window.config.get("minecraft_path", "")
            if minecraft_path and os.path.exists(minecraft_path):
                versions_path = os.path.join(minecraft_path, "versions")
                if os.path.exists(versions_path) and os.path.isdir(versions_path):
                    self.builder.window.download_version_combo.clear()
                    versions = []
                    for item in sorted(os.listdir(versions_path)):
                        item_path = os.path.join(versions_path, item)
                        if os.path.isdir(item_path):
                            versions.append(item)

                    for version in versions:
                        self.builder.window.download_version_combo.addItem(version)
                    logger.info(f"Loaded {len(versions)} versions to download combo")
        except Exception as e:
            logger.error(f"Error loading versions to download combo: {e}")
