"""文件浏览器组件"""

import os
import logging
import zipfile
from PyQt6.QtCore import Qt, pyqtSignal, QSize, QEvent
from PyQt6.QtGui import QFont, QIcon, QPixmap, QWheelEvent
from PyQt6.QtWidgets import (QFileDialog, QGridLayout, QHBoxLayout, QHeaderView, QLabel,
                             QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QWidget)
from utils import load_svg_icon, scale_icon_for_display

logger = logging.getLogger(__name__)


class ResourcepackItemWidget(QWidget):
    """资源包项目部件，支持收藏按钮，使用卡片样式（类似下载页面）"""

    def __init__(self, parent=None, on_favorite_clicked=None, on_edit_clicked=None, is_favorited=False, dpi_scale=1.0, resourcepack_name="", icon=None, is_editable=False, text_renderer=None, description="", file_size="", modified_time=""):
        super().__init__(parent)
        self.dpi_scale = dpi_scale
        self.on_favorite_clicked = on_favorite_clicked
        self.on_edit_clicked = on_edit_clicked
        self.is_favorited = is_favorited
        self.resourcepack_name = resourcepack_name
        self.icon = icon
        self.is_editable = is_editable
        self.text_renderer = text_renderer
        self.description = description
        self.file_size = file_size
        self.modified_time = modified_time

        # 设置固定高度为80px
        self.setFixedHeight(int(80 * dpi_scale))

        # 使用布局管理器来定位按钮
        from PyQt6.QtWidgets import QGridLayout
        layout = QGridLayout(self)
        layout.setContentsMargins(int(12 * dpi_scale), int(6 * dpi_scale), int(12 * dpi_scale), int(6 * dpi_scale))
        layout.setHorizontalSpacing(int(12 * dpi_scale))  # 水平间距，图标和文字之间的间距
        layout.setVerticalSpacing(int(4 * dpi_scale))  # 垂直间距
        layout.setColumnStretch(0, 0)  # 第0列（图标）不拉伸
        layout.setColumnStretch(1, 1)  # 第1列（文字）占据剩余空间
        layout.setColumnStretch(2, 0)  # 第2列（编辑按钮）不拉伸
        layout.setColumnStretch(3, 0)  # 第3列（书签按钮）不拉伸

        # 图标和文字的容器
        icon_wrapper = QWidget()
        icon_wrapper_layout = QVBoxLayout(icon_wrapper)
        icon_wrapper_layout.setContentsMargins(0, 0, 0, 0)  # 没有内边距
        icon_wrapper_layout.setSpacing(int(2 * dpi_scale))
        icon_wrapper_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)  # 左对齐

        # 图标容器（固定大小，缩小图标）
        icon_label = QLabel()
        icon_label.setFixedSize(int(64 * dpi_scale), int(64 * dpi_scale))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if icon is not None:
            # icon 是 QPixmap，缩放到64x64
            scaled_icon = icon.scaled(
                int(64 * dpi_scale), int(64 * dpi_scale),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(scaled_icon)
        else:
            # 默认图标，缩放到64x64
            default_icon = load_svg_icon("svg/unknown_pack.png", self.dpi_scale)
            if default_icon:
                scaled_default = scale_icon_for_display(default_icon, 64, self.dpi_scale)
                if scaled_default:
                    scaled_final = scaled_default.scaled(
                        int(64 * dpi_scale), int(64 * dpi_scale),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    icon_label.setPixmap(scaled_final)

        icon_wrapper_layout.addWidget(icon_label)

        # 设置wrapper的固定宽度
        icon_wrapper.setFixedWidth(int(64 * dpi_scale))

        # 添加图标到左上角（左对齐，顶部对齐）
        layout.addWidget(icon_wrapper, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 信息区域（使用VBoxLayout，文字独立）
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(0, 0, 0, 0)  # 没有内边距
        info_layout.setSpacing(int(2 * dpi_scale))  # 减小标题和描述之间的间距
        info_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)

        # 资源包名称（仅一行，在图标右侧上方）
        name_label = QLabel(resourcepack_name)
        name_font = QFont()
        name_font.setFamily("Microsoft YaHei UI")
        name_font.setWeight(QFont.Weight.Bold)
        name_font.setPointSize(int(10 * dpi_scale))  # 字号从12减小到10
        name_label.setFont(name_font)
        name_label.setStyleSheet("color: white; background: transparent;")
        name_label.setWordWrap(False)
        name_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        info_layout.addWidget(name_label)

        # 描述（在资源包标题下方）
        if description:
            # 将 \n 替换为实际的换行符，并移除 Minecraft 颜色代码（§ 开头的颜色代码）
            import re
            clean_desc = re.sub(r'§[0-9a-fk-or]', '', description)
            description_label = QLabel(clean_desc)
            desc_font = QFont()
            desc_font.setFamily("Microsoft YaHei UI")
            desc_font.setWeight(QFont.Weight.Normal)
            desc_font.setPointSize(int(8 * dpi_scale))  # 描述字号缩小到8
            description_label.setFont(desc_font)
            description_label.setStyleSheet("color: rgba(255, 255, 255, 0.6); background: transparent;")
            description_label.setWordWrap(True)  # 允许换行
            description_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            info_layout.addWidget(description_label)

        # 文件大小和修改时间（横向布局，右对齐）
        metadata_layout = QHBoxLayout()
        metadata_layout.setContentsMargins(0, 0, 0, 0)
        metadata_layout.setSpacing(int(8 * dpi_scale))

        metadata_layout.addStretch()

        if file_size:
            size_label = QLabel(file_size)
            size_font = QFont()
            size_font.setFamily("Microsoft YaHei UI")
            size_font.setWeight(QFont.Weight.Normal)
            size_font.setPointSize(int(7 * dpi_scale))
            size_label.setFont(size_font)
            size_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent;")
            metadata_layout.addWidget(size_label)

        if modified_time:
            time_label = QLabel(modified_time)
            time_font = QFont()
            time_font.setFamily("Microsoft YaHei UI")
            time_font.setWeight(QFont.Weight.Normal)
            time_font.setPointSize(int(7 * dpi_scale))
            time_label.setFont(time_font)
            time_label.setStyleSheet("color: rgba(255, 255, 255, 0.5); background: transparent;")
            metadata_layout.addWidget(time_label)

        # 添加信息区域到第0行第1列，占据多列，左上对齐
        layout.addLayout(info_layout, 0, 1, 1, 1, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)

        # 编辑按钮（在收藏按钮左侧，仅可编辑时显示）
        edit_btn = QPushButton()
        edit_btn.setFixedSize(int(28 * dpi_scale), int(28 * dpi_scale))
        edit_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {int(6 * dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
        edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        edit_btn.clicked.connect(self._on_edit_clicked)

        # 设置编辑图标
        self._update_edit_icon(edit_btn)

        # 如果不可编辑，隐藏编辑按钮
        if not self.is_editable:
            edit_btn.hide()

        # 初始隐藏编辑按钮（鼠标进入时显示）- 仅对可编辑的资源包生效
        if self.is_editable:
            edit_btn.hide()

        # 保存编辑按钮引用
        self.edit_btn = edit_btn

        # 添加编辑按钮到收藏按钮左侧
        layout.addWidget(edit_btn, 0, 2, 1, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

        # 添加元数据到第0行，跨越第2-3列（在按钮右侧）
        metadata_wrapper = QWidget()
        metadata_wrapper.setLayout(metadata_layout)
        metadata_wrapper.setFixedHeight(int(20 * dpi_scale))  # 限制高度避免挤压
        metadata_wrapper.setStyleSheet("background: transparent;")  # 去除背景
        layout.addWidget(metadata_wrapper, 0, 2, 1, 2, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom)

        # 收藏按钮（放在右上角，第0行第3列）
        bookmark_btn = QPushButton()
        bookmark_btn.setFixedSize(int(28 * dpi_scale), int(28 * dpi_scale))
        bookmark_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: {int(6 * dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.18);
                border: 1px solid rgba(255, 255, 255, 0.25);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.12);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)
        bookmark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        bookmark_btn.clicked.connect(self._on_bookmark_clicked)

        # 初始隐藏收藏按钮
        bookmark_btn.hide()

        # 设置初始图标状态
        self._update_bookmark_icon(bookmark_btn)

        # 保存按钮引用
        self.bookmark_btn = bookmark_btn

        # 添加收藏按钮到右上角（第3列）
        layout.addWidget(bookmark_btn, 0, 3, 1, 1, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)

    def enterEvent(self, event):
        """鼠标进入事件"""
        # 只有在可收藏时才显示收藏按钮
        if hasattr(self, 'bookmark_btn') and self.on_favorite_clicked is not None:
            self.bookmark_btn.show()
        # 如果资源包可编辑，显示编辑按钮
        if hasattr(self, 'edit_btn') and self.is_editable and self.on_edit_clicked is not None:
            self.edit_btn.show()
        super().enterEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        # 隐藏收藏按钮
        if hasattr(self, 'bookmark_btn'):
            self.bookmark_btn.hide()
        # 隐藏编辑按钮
        if hasattr(self, 'edit_btn'):
            self.edit_btn.hide()
        super().leaveEvent(event)

    def _on_edit_clicked(self):
        """编辑按钮点击事件"""
        if self.on_edit_clicked:
            self.on_edit_clicked()

    def _on_bookmark_clicked(self):
        """收藏按钮点击事件"""
        if self.on_favorite_clicked:
            self.on_favorite_clicked()

    def _update_edit_icon(self, btn):
        """更新编辑图标"""
        edit_pixmap = load_svg_icon("svg/sliders.svg", self.dpi_scale)
        if edit_pixmap:
            btn.setIcon(QIcon(scale_icon_for_display(edit_pixmap, 16, self.dpi_scale)))
        else:
            btn.setIcon(QIcon())

    def _update_bookmark_icon(self, btn):
        """更新收藏图标"""
        if self.is_favorited:
            bookmark_pixmap = load_svg_icon("svg/bookmarks-fill.svg", self.dpi_scale)
        else:
            bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self.dpi_scale)

        if bookmark_pixmap:
            btn.setIcon(QIcon(scale_icon_for_display(bookmark_pixmap, 16, self.dpi_scale)))
        else:
            btn.setIcon(QIcon())

    def set_favorited(self, is_favorited):
        """设置收藏状态"""
        self.is_favorited = is_favorited
        # 直接更新收藏按钮图标
        if hasattr(self, 'bookmark_btn'):
            self._update_bookmark_icon(self.bookmark_btn)


class FileExplorer(QWidget):
    """文件浏览器组件"""

    file_selected = pyqtSignal(str)  # 文件选择信号
    close_requested = pyqtSignal()  # 关闭请求信号

    def __init__(self, parent=None, dpi_scale=1.0, config_manager=None, language_manager=None, text_renderer=None, no_scroll=False, show_close_button=True):
        super().__init__(parent)
        self.dpi_scale = dpi_scale
        self.config_manager = config_manager
        self.language_manager = language_manager
        self.text_renderer = text_renderer  # 新增 text_renderer 参数
        self.no_scroll = no_scroll  # 无滚动模式：让file_tree根据内容自动调整大小
        self.show_close_button = show_close_button  # 是否显示关闭按钮
        self.current_path = None
        self.root_path = None  # 保存minecraft路径
        self.base_path = None  # 保存当前resourcepacks路径作为返回的根目录
        self.resourcepack_mode = False  # 是否为资源包浏览模式
        self._item_widgets = {}  # 存储资源包项目部件：{full_path: widget}
        self._search_text = ""  # 搜索文本
        self._filter_favorites_only = False  # 是否仅显示收藏的资源包
        self._sort_by = "name"  # 排序方式: name, size, time
        self._sort_order = "asc"  # 排序顺序: asc, desc
        self._cached_resourcepacks = []  # 缓存的资源包数据: [(name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable)]
        self._cached_folders = []  # 缓存的文件夹数据: [(name, is_dir, full_path)]
        self._cache_valid = False  # 缓存是否有效
        self._search_timer = None  # 搜索防抖定时器
        self._init_ui()

    def translate(self, key, **kwargs):
        """翻译辅助方法"""
        if self.text_renderer:
            return self.text_renderer.translate(key, **kwargs)
        elif self.language_manager:
            text = self.language_manager.translate(key)
            # 支持字符串格式化
            if kwargs:
                try:
                    text = text.format(**kwargs)
                except:
                    pass
            return text
        # 如果没有 language_manager，返回键本身或默认值
        return key

    def update_language(self):
        """更新界面语言"""
        # 更新页面标题
        if hasattr(self, 'page_title'):
            self.page_title.setText(self.translate("page_resourcepacks"))

        # 更新路径标签
        if self.current_path:
            self.path_label.setText(self._format_path_display(self.current_path))
        else:
            self.path_label.setText(self.translate("file_explorer_no_path"))

    def eventFilter(self, obj, event):
        """事件过滤器：调整滚轮滚动步进值"""
        if obj == self.file_tree.viewport():
            if event.type() == QEvent.Type.Wheel:
                if self.no_scroll:
                    # 无滚动模式：拦截滚轮事件并传递给父级滚动区域
                    # 找到父级滚动区域
                    scroll_area = self.parent()
                    while scroll_area and not hasattr(scroll_area, 'widgetResizable'):
                        scroll_area = scroll_area.parent()

                    # 如果找到滚动区域，传递事件
                    if scroll_area:
                        scroll_area.wheelEvent(event)
                    return True
                else:
                    # 正常模式：调整滚动步进值
                    # 获取垂直滚动条
                    scroll_bar = self.file_tree.verticalScrollBar()
                    if scroll_bar:
                        # 设置滚动步进值为较小值（原来的 2/3）
                        scroll_bar.setSingleStep(int(13 * self.dpi_scale))
                        scroll_bar.setPageStep(int(53 * self.dpi_scale))
        return super().eventFilter(obj, event)

    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(int(12 * self.dpi_scale))

        # 页面标题和关闭按钮容器
        self.title_container = QWidget()
        self.title_container.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(self.title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(int(12 * self.dpi_scale))

        # 关闭按钮（返回到版本界面）
        if self.show_close_button:
            self.close_btn = QPushButton()
            self.close_btn.setFixedSize(int(24 * self.dpi_scale), int(24 * self.dpi_scale))
            self.close_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: {int(12 * self.dpi_scale)}px;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.15);
                    border: 1px solid rgba(255, 255, 255, 0.5);
                }}
                QPushButton:pressed {{
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.4);
                }}
            """)
            self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            self.close_btn.clicked.connect(self.close_explorer)

            # 设置关闭按钮图标
            close_icon = load_svg_icon("svg/x.svg", self.dpi_scale)
            if close_icon:
                self.close_btn.setIcon(QIcon(scale_icon_for_display(close_icon, 18, self.dpi_scale)))

            title_layout.addWidget(self.close_btn)

        # 页面标题
        self.page_title = QLabel(self.translate("page_resourcepacks"))
        self.page_title.setStyleSheet(f"""
            QLabel {{
                color: white;
                background: transparent;
                font-size: {int(20 * self.dpi_scale)}px;
                font-weight: bold;
            }}
        """)
        title_layout.addWidget(self.page_title)
        title_layout.addStretch()

        layout.addWidget(self.title_container)

        # 如果不显示关闭按钮，隐藏标题容器
        if not self.show_close_button:
            self.title_container.hide()

        # 路径卡片（现在作为主卡片的顶部区域）
        self.path_card = QWidget()
        self.path_card.setFixedHeight(int(44 * self.dpi_scale))
        self.path_card.setStyleSheet(f"""
            QWidget {{
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-top-left-radius: {int(8 * self.dpi_scale)}px;
                border-top-right-radius: {int(8 * self.dpi_scale)}px;
            }}
        """)
        path_card_layout = QHBoxLayout(self.path_card)
        path_card_layout.setContentsMargins(int(12 * self.dpi_scale), int(6 * self.dpi_scale), int(12 * self.dpi_scale), int(6 * self.dpi_scale))
        path_card_layout.setSpacing(int(10 * self.dpi_scale))

        # 当前路径标签
        self.path_label = QLabel(self.translate("file_explorer_no_path"))
        self.path_label.setWordWrap(False)
        self.path_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                border: none;
                font-size: {int(13 * self.dpi_scale)}px;
            }}
        """)
        path_card_layout.addWidget(self.path_label)
        path_card_layout.addStretch()

        # 返回根目录按钮
        self.back_btn = QPushButton()
        self.back_btn.setFixedSize(int(36 * self.dpi_scale), int(32 * self.dpi_scale))
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.back_btn.clicked.connect(self.navigate_to_root)
        self.back_btn.setEnabled(False)
        
        # 设置返回根目录按钮图标
        back_icon = load_svg_icon("svg/arrow-90deg-left.svg", self.dpi_scale)
        if back_icon:
            self.back_btn.setIcon(QIcon(scale_icon_for_display(back_icon, 16, self.dpi_scale)))

        path_card_layout.addWidget(self.back_btn)

        # 刷新按钮
        self.refresh_btn = QPushButton()
        self.refresh_btn.setFixedSize(int(36 * self.dpi_scale), int(32 * self.dpi_scale))
        self.refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._on_refresh_clicked)
        # 设置刷新按钮图标
        refresh_icon = load_svg_icon("svg/arrow-repeat.svg", self.dpi_scale)
        if refresh_icon:
            self.refresh_btn.setIcon(QIcon(scale_icon_for_display(refresh_icon, 16, self.dpi_scale)))
        path_card_layout.addWidget(self.refresh_btn)

        # 在文件资源管理器中打开按钮
        self.open_explorer_btn = QPushButton()
        self.open_explorer_btn.setFixedSize(int(36 * self.dpi_scale), int(32 * self.dpi_scale))
        self.open_explorer_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.open_explorer_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.open_explorer_btn.clicked.connect(self.open_in_explorer)
        
        # 设置文件资源管理器按钮图标
        explorer_icon = load_svg_icon("svg/folder2.svg", self.dpi_scale)
        if explorer_icon:
            self.open_explorer_btn.setIcon(QIcon(scale_icon_for_display(explorer_icon, 16, self.dpi_scale)))

        path_card_layout.addWidget(self.open_explorer_btn)

        # 搜索框和筛选排序按钮（仅在有资源包时显示）
        self.search_container = QWidget()
        self.search_container.setStyleSheet("background: transparent; border: none;")
        search_layout = QHBoxLayout(self.search_container)
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(int(8 * self.dpi_scale))
        search_layout.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # 搜索输入框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(self.translate("resourcepack_search_placeholder"))
        self.search_input.setFixedHeight(int(32 * self.dpi_scale))
        self.search_input.setStyleSheet(self.builder._get_lineedit_stylesheet() if hasattr(self, 'builder') else f"""
            QLineEdit {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(16 * self.dpi_scale)}px;
                padding: 0 {int(10 * self.dpi_scale)}px;
                color: rgba(255, 255, 255, 0.9);
                font-size: {int(12 * self.dpi_scale)}px;
            }}
            QLineEdit:focus {{
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(100, 150, 255, 0.6);
            }}
            /* 隐藏清除按钮背景 */
            QLineEdit * {{
                background: transparent;
                border: none;
                border-radius: 0px;
                margin: 0px;
                padding: 0px;
            }}
            QToolButton {{
                background: transparent;
                border: none;
                border-radius: 0px;
                padding: 0px;
                margin: 0px;
            }}
            QToolButton:hover {{
                background: transparent;
                border: none;
            }}
            QToolButton:pressed {{
                background: transparent;
                border: none;
            }}
        """)
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_input, 1)

        # 筛选按钮（仅收藏）
        self.filter_btn = QPushButton()
        self.filter_btn.setFixedSize(int(32 * self.dpi_scale), int(32 * self.dpi_scale))
        self.filter_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.filter_btn.clicked.connect(self._toggle_filter_favorites)
        search_layout.addWidget(self.filter_btn)

        # 设置筛选按钮图标
        filter_icon = load_svg_icon("svg/funnel.svg", self.dpi_scale)
        if filter_icon:
            self.filter_btn.setIcon(QIcon(scale_icon_for_display(filter_icon, 16, self.dpi_scale)))

        # 排序按钮
        self.sort_btn = QPushButton()
        self.sort_btn.setFixedSize(int(32 * self.dpi_scale), int(32 * self.dpi_scale))
        self.sort_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                padding: 0;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
        """)
        self.sort_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.sort_btn.clicked.connect(self._show_sort_menu)
        search_layout.addWidget(self.sort_btn)

        # 设置排序按钮图标
        sort_icon = load_svg_icon("svg/sort-down.svg", self.dpi_scale)
        if sort_icon:
            self.sort_btn.setIcon(QIcon(scale_icon_for_display(sort_icon, 16, self.dpi_scale)))

        # 将搜索容器添加到路径卡片中
        path_card_layout.addWidget(self.search_container)
        self.search_container.hide()  # 初始隐藏，在资源包模式下显示

        # 大卡片容器（包含路径栏和资源包列表）
        self.main_card = QWidget()
        self.main_card.setStyleSheet(f"""
            QWidget {{
                background: rgba(0, 0, 0, 0.3);
                border-radius: {int(8 * self.dpi_scale)}px;
            }}
        """)
        main_card_layout = QVBoxLayout(self.main_card)
        main_card_layout.setContentsMargins(0, 0, int(8 * self.dpi_scale), int(8 * self.dpi_scale))
        main_card_layout.setSpacing(0)
        main_card_layout.setAlignment(Qt.AlignmentFlag.AlignTop)  # 顶部对齐

        # 将路径卡片添加到主卡片中
        main_card_layout.addWidget(self.path_card)

        # 空标签（用于显示无内容或路径不存在的情况）
        self.empty_label = QLabel()
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
                border: none;
                padding: {int(8 * self.dpi_scale)}px {int(12 * self.dpi_scale)}px;
                font-size: {int(12 * self.dpi_scale)}px;
                text-align: center;
            }}
        """)
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        main_card_layout.addWidget(self.empty_label)

        # 文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)  # 隐藏表头（包含名称和大小列）
        self.file_tree.setColumnCount(1)  # 只显示一列（名称）

        # 禁用选择模式
        self.file_tree.setSelectionMode(QTreeWidget.SelectionMode.NoSelection)

        # 根据模式设置滚动条策略
        if self.no_scroll:
            # 无滚动模式：禁用内部滚动条（由外部容器处理）
            self.file_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.file_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            # 正常模式：使用默认滚动条策略，并设置为像素滚动模式
            self.file_tree.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
            self.file_tree.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            # 设置为像素滚动模式（平滑滚动，不按项目数量滚动）
            self.file_tree.setHorizontalScrollMode(self.file_tree.ScrollMode.ScrollPerPixel)
            self.file_tree.setVerticalScrollMode(self.file_tree.ScrollMode.ScrollPerPixel)

        # 安装事件过滤器（用于调整滚轮滚动步进值）
        self.file_tree.viewport().installEventFilter(self)

        # 设置图标大小（适配新的64x64资源包图标）
        self.file_tree.setIconSize(QSize(int(64 * self.dpi_scale), int(64 * self.dpi_scale)))

        # 设置资源包项目的样式
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.9);
            }}
            QTreeWidget::item {{
                padding: {int(8 * self.dpi_scale)}px;
                height: {int(80 * self.dpi_scale)}px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
            QTreeWidget::branch:has-children:closed {{
                image: none;
            }}
            QTreeWidget::branch:has-children:open {{
                image: none;
            }}
            QTreeWidget::viewport {{
                background: transparent;
            }}
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.7);
                padding: {int(6 * self.dpi_scale)}px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                font-size: {int(11 * self.dpi_scale)}px;
                font-weight: bold;
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.1);
                width: {int(10 * self.dpi_scale)}px;
                border-radius: {int(5 * self.dpi_scale)}px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                min-height: {int(20 * self.dpi_scale)}px;
                border-radius: {int(5 * self.dpi_scale)}px;
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
        """)

        header = self.file_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)

        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        main_card_layout.addWidget(self.file_tree, 1)

        layout.addWidget(self.main_card, 1)
    
    def set_minecraft_path(self, path):
        """设置Minecraft路径（根目录使用resourcepacks文件夹）"""
        self.root_path = path
        # 根目录应该是 .minecraft/resourcepacks
        resourcepacks_path = os.path.join(path, "resourcepacks")
        self.current_path = resourcepacks_path if os.path.exists(resourcepacks_path) else path
        self.base_path = self.current_path  # 设置返回根目录的基础路径
        # 统一使用反斜杠显示路径
        display_path = self._format_path_display(self.current_path)
        self.path_label.setText(display_path)
        self.back_btn.setEnabled(False)
        self.resourcepack_mode = True  # 启用资源包模式
        if os.path.exists(self.current_path):
            self.path_card.show()
            self.file_tree.show()
            self._load_directory(self.current_path, use_cache=False)
        else:
            self.path_card.hide()
            self.file_tree.hide()

    def _format_path_display(self, path):
        """格式化路径显示（使用 . 表示根目录）"""
        # 在资源包模式下，只显示base_path内的路径
        if self.resourcepack_mode and self.base_path:
            if path.startswith(self.base_path):
                # 只显示base_path文件夹内的路径
                sub_path = path[len(self.base_path):].lstrip(os.sep).lstrip("/").lstrip("\\")
                # 统一使用反斜杠
                sub_path = sub_path.replace("/", "\\")
                # 根目录显示 .，子目录显示 .\文件夹名
                if not sub_path:
                    return "."
                else:
                    return ".\\" + sub_path

        # 默认显示完整路径
        full_path = path.replace("/", "\\")
        if len(full_path) < 50:
            return full_path
        else:
            return "..." + full_path[-47:]
    def navigate_to_root(self):
        """返回根目录（base_path，即当前选定的resourcepacks文件夹）"""
        # 如果有保存的原始base_path，则恢复它
        if hasattr(self, '_original_base_path'):
            self.base_path = self._original_base_path
            delattr(self, '_original_base_path')

        if self.base_path and os.path.exists(self.base_path):
            self.current_path = self.base_path
            display_path = self._format_path_display(self.current_path)
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(False)
            self.path_card.show()
            self._load_directory(self.current_path, use_cache=False)

    def open_in_explorer(self):
        """在文件资源管理器中打开当前路径"""
        if self.current_path and os.path.exists(self.current_path):
            import subprocess
            import sys
            try:
                if sys.platform == 'win32':
                    subprocess.Popen(['explorer', self.current_path])
                elif sys.platform == 'darwin':
                    subprocess.Popen(['open', self.current_path])
                else:
                    subprocess.Popen(['xdg-open', self.current_path])
            except Exception as e:
                logger.error(f"Failed to open in file explorer: {e}")

    def close_explorer(self):
        """关闭文件浏览器（发出关闭请求信号）"""
        self.close_requested.emit()

    def _on_refresh_clicked(self):
        """刷新当前目录"""
        if self.current_path and os.path.exists(self.current_path):
            # 清除缓存，强制重新加载
            self._cache_valid = False
            self._load_directory(self.current_path, use_cache=False)
            logger.info(f"Refreshed directory: {self.current_path}")

    def navigate_to_directory(self, path):
        """导航到指定目录"""
        if not os.path.exists(path):
            self.file_tree.hide()
            return

        self.current_path = path
        display_path = self._format_path_display(path)
        self.path_label.setText(display_path)
        self.back_btn.setEnabled(True)
        self.path_card.show()
        self.file_tree.show()
        self._load_directory(path, use_cache=False)

    def set_resourcepacks_path(self, path, minecraft_path):
        """直接设置resourcepacks路径（用于多层级导航）"""
        self.root_path = minecraft_path
        self.base_path = path  # 当前resourcepacks路径作为返回的根目录
        self.current_path = path
        self.resourcepack_mode = True
        if os.path.exists(self.current_path):
            display_path = self._format_path_display(self.current_path)
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(False)
            self.path_card.show()
            self.file_tree.show()
            self._load_directory(self.current_path, use_cache=False)
        else:
            self.path_card.hide()
            self.file_tree.hide()
    
    def navigate_to_version_resourcepacks(self, version_name):
        """导航到指定版本的resourcepacks文件夹"""
        if not self.root_path:
            return

        version_path = os.path.join(self.root_path, "versions", version_name)
        if not os.path.exists(version_path):
            self.file_tree.hide()
            return

        # 查找版本jar文件或目录
        version_dir = os.path.join(version_path, version_name + ".jar")
        if not os.path.exists(version_dir):
            version_dir = os.path.join(version_path, version_name)

        # 检查是否有resourcepacks目录
        resourcepacks_path = os.path.join(version_path, "resourcepacks")

        if os.path.exists(resourcepacks_path):
            self.current_path = resourcepacks_path
            # 统一使用反斜杠显示路径
            display_path = "...\\versions\\" + version_name + "\\resourcepacks"
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(True)
            self.path_card.show()
            self.file_tree.show()
            self._load_directory(resourcepacks_path, use_cache=False)
        else:
            self.path_card.hide()
            self.file_tree.hide()
    
    def _load_directory(self, path, use_cache=False):
        """加载目录内容
        
        Args:
            path: 目录路径
            use_cache: 是否使用缓存的数据（用于搜索/筛选/排序时）
        """
        # 如果使用缓存且缓存有效，直接从缓存刷新显示
        if use_cache and self._cache_valid and self.resourcepack_mode:
            self._refresh_display_from_cache()
            return
        
        # 不使用缓存或缓存失效，重新加载文件系统
        self.file_tree.clear()
        self._item_widgets = {}  # 清空项目部件缓存
        self._cached_resourcepacks = []  # 清空资源包缓存
        self._cached_folders = []  # 清空文件夹缓存
        self._cache_valid = False  # 标记缓存无效

        self.file_tree.show()

        # 确保base_path已设置
        if not hasattr(self, 'base_path') or self.base_path is None:
            self.base_path = path

        if not os.path.exists(path):
            self.file_tree.hide()
            return

        if not os.path.isdir(path):
            self.file_tree.hide()
            return

        try:
            items = []
            for item in os.listdir(path):
                full_path = os.path.join(path, item)
                if os.path.isdir(full_path):
                    # 如果是versions目录，只显示子目录
                    if os.path.basename(path) == "versions" and os.path.isdir(full_path):
                        items.append((item, True, full_path))
                    # 如果是其他目录，显示所有文件夹
                    elif os.path.basename(path) != "versions":
                        items.append((item, True, full_path))
                else:
                    # 显示文件
                    items.append((item, False, full_path))

            # 排序：文件夹在前，文件在后
            items.sort(key=lambda x: (not x[1], x[0]))

            # 获取收藏的资源包列表
            favorited_resourcepacks = []
            if self.config_manager and self.resourcepack_mode:
                config = self.config_manager.config if hasattr(self.config_manager, 'config') else self.config_manager
                favorited_resourcepacks = config.get("favorited_resourcepacks", [])

            # 在资源包模式下，显示文件夹和有效的资源包
            if self.resourcepack_mode:
                # 显示搜索、筛选和排序控件
                self.search_container.show()

                resourcepack_items = []
                non_resourcepack_dirs = []

                for name, is_dir, full_path in items:
                    if is_dir:
                        # 检查是否是有效的资源包（必须包含pack.mcmeta）
                        if self._is_valid_resourcepack(full_path, is_dir):
                            resourcepack_items.append((name, is_dir, full_path))
                        else:
                            # 不是资源包的文件夹
                            non_resourcepack_dirs.append((name, is_dir, full_path))
                    elif name.endswith('.zip'):
                        # 检查zip文件是否是有效的资源包
                        if self._is_valid_resourcepack(full_path, False):
                            resourcepack_items.append((name, is_dir, full_path))

                logger.info(f"Resourcepack mode: found {len(resourcepack_items)} valid resourcepacks and {len(non_resourcepack_dirs)} folders out of {len(items)} items")

                # 缓存所有资源包数据（包括图标、描述等）
                self._cache_resourcepack_data(resourcepack_items, non_resourcepack_dirs, favorited_resourcepacks)

                # 从缓存中刷新显示
                self._refresh_display_from_cache()
            else:
                # 非资源包模式，正常显示
                self.search_container.hide()
                for name, is_dir, full_path in items:
                    self._add_item(name, is_dir, full_path)

            # 检查当前路径是否为版本隔离的子路径
            is_version_subpath = self.base_path and self.current_path != self.base_path and "versions" in self.current_path

            # 如果没有内容，显示空标签并隐藏 file_tree
            if self.file_tree.topLevelItemCount() == 0:
                self.file_tree.hide()
                self.empty_label.setText(self.translate("file_explorer_empty"))
                self.empty_label.show()
            else:
                self.empty_label.hide()
                self.file_tree.show()

            # 在无滚动模式下，根据内容更新file_tree的高度
            if self.no_scroll:
                # 主路径：使用最小高度，允许内容超出时父级容器滚动
                # 计算实际内容高度
                item_count = self.file_tree.topLevelItemCount()
                # ResourcepackItemWidget 的高度是 80 * dpi_scale
                # 每个项目的总高度 = widget高度(80) + padding(8+8) + border-bottom(1)
                item_height = int(80 * self.dpi_scale) + int(16 * self.dpi_scale) + 1
                total_height = max(1, item_count * item_height)  # 至少为1
                self.file_tree.setMinimumHeight(total_height)
                self.file_tree.setMaximumHeight(total_height)

        except PermissionError:
            self.file_tree.hide()
            self.path_card.hide()
        except Exception as e:
            logger.error(f"Error loading directory: {e}", exc_info=True)
            self.file_tree.hide()
            self.path_card.hide()

    def _add_item(self, name, is_dir, full_path):
        """添加普通项目（文件夹使用ResourcepackItemWidget样式）"""
        if is_dir:
            # 文件夹：使用ResourcepackItemWidget样式（不可收藏，无描述）
            item = QTreeWidgetItem()
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            self.file_tree.addTopLevelItem(item)

            # 获取文件夹图标（使用与资源包相同的渲染逻辑）
            icon_pixmap = self._get_resourcepack_icon_pixmap(full_path, is_dir)

            # 创建ResourcepackItemWidget（文件夹不显示收藏按钮和编辑按钮）
            widget = ResourcepackItemWidget(
                parent=self.file_tree,
                on_favorite_clicked=None,
                on_edit_clicked=None,
                is_favorited=False,
                dpi_scale=self.dpi_scale,
                resourcepack_name=name,
                icon=icon_pixmap,
                is_editable=False,
                text_renderer=self.text_renderer,
                description="",
                file_size="文件夹",
                modified_time=""
            )

            # 设置项目部件
            self.file_tree.setItemWidget(item, 0, widget)

            # 添加占位子项
            QTreeWidgetItem(item).setText(0, "...")
        else:
            # 文件：使用普通样式
            item = QTreeWidgetItem()
            item.setText(0, name)
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            self.file_tree.addTopLevelItem(item)

    def _add_resourcepack_item(self, name, is_dir, full_path, is_favorited):
        """添加资源包项目（带收藏按钮，使用卡片样式）"""
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, full_path)
        self.file_tree.addTopLevelItem(item)

        # 获取pack.png图标（用于卡片显示）
        icon_pixmap = self._get_resourcepack_icon_pixmap(full_path, is_dir)

        # 检查资源包是否可编辑
        is_editable = self._is_resourcepack_editable(full_path, is_dir)

        # 获取资源包描述
        description = self._get_resourcepack_description(full_path, is_dir)

        # 获取文件大小和修改时间
        file_size = ""
        modified_time = ""
        try:
            if is_dir:
                # 文件夹：显示"文件夹"文字
                file_size = "文件夹"
            else:
                # 文件：显示文件大小
                size = os.path.getsize(full_path)
                file_size = self._format_size(size)
            # 获取修改时间（文件夹和文件都显示）
            mtime = os.path.getmtime(full_path)
            import datetime
            modified_time = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
        except Exception:
            pass

        logger.debug(f"Adding resourcepack item: {name}, icon_pixmap: {icon_pixmap is not None}, is_editable: {is_editable}")

        # 创建自定义部件并设置为项目的部件
        def on_favorite_clicked():
            self._toggle_favorite_resourcepack(full_path, name)

        def on_edit_clicked():
            self._edit_resourcepack(full_path, name)

        widget = ResourcepackItemWidget(
            parent=self.file_tree,
            on_favorite_clicked=on_favorite_clicked,
            on_edit_clicked=on_edit_clicked,
            is_favorited=is_favorited,
            dpi_scale=self.dpi_scale,
            resourcepack_name=name,
            icon=icon_pixmap,
            is_editable=is_editable,
            text_renderer=self.text_renderer,
            description=description,
            file_size=file_size,
            modified_time=modified_time
        )

        # 存储部件引用
        self._item_widgets[full_path] = widget

        # 设置项目部件
        self.file_tree.setItemWidget(item, 0, widget)

        if is_dir:
            # 添加占位子项
            QTreeWidgetItem(item).setText(0, "...")
    
    def _toggle_favorite_resourcepack(self, full_path, name):
        """切换资源包的收藏状态"""
        if not self.config_manager:
            return
        
        # 获取配置
        config = self.config_manager.config if hasattr(self.config_manager, 'config') else self.config_manager
        favorited_resourcepacks = config.get("favorited_resourcepacks", [])
        
        if full_path in favorited_resourcepacks:
            # 取消收藏
            favorited_resourcepacks.remove(full_path)
            logger.info(f"Removing resourcepack from favorites: {name}")
        else:
            # 添加收藏
            favorited_resourcepacks.append(full_path)
            logger.info(f"Adding resourcepack to favorites: {name}")
        
        # 更新配置
        if hasattr(self.config_manager, 'set'):
            self.config_manager.set("favorited_resourcepacks", favorited_resourcepacks)
        else:
            config["favorited_resourcepacks"] = favorited_resourcepacks
            if hasattr(self.config_manager, 'save_config'):
                self.config_manager.save_config()
        
        # 更新项目的收藏状态
        if full_path in self._item_widgets:
            is_favorited = full_path in favorited_resourcepacks
            self._item_widgets[full_path].set_favorited(is_favorited)
        
        # 使用缓存刷新显示以使收藏的资源包置顶
        if self.current_path:
            self._refresh_display_from_cache()

    def _edit_resourcepack(self, full_path, name):
        """编辑资源包"""
        logger.info(f"Edit resourcepack: {name}")
        # 这里可以添加编辑资源包的逻辑
        # 例如：打开编辑器、编辑packset.json等

    def _cache_resourcepack_data(self, resourcepack_items, non_resourcepack_dirs, favorited_resourcepacks):
        """缓存资源包和文件夹数据
        
        Args:
            resourcepack_items: 资源包列表 [(name, is_dir, full_path)]
            non_resourcepack_dirs: 非资源包文件夹列表 [(name, is_dir, full_path)]
            favorited_resourcepacks: 收藏的资源包路径列表
        """
        self._cached_folders = list(non_resourcepack_dirs)  # 缓存文件夹
        
        # 缓存资源包数据（包括图标、描述等）
        for name, is_dir, full_path in resourcepack_items:
            # 获取pack.png图标（用于卡片显示）
            icon_pixmap = self._get_resourcepack_icon_pixmap(full_path, is_dir)
            
            # 检查资源包是否可编辑
            is_editable = self._is_resourcepack_editable(full_path, is_dir)
            
            # 获取资源包描述
            description = self._get_resourcepack_description(full_path, is_dir)
            
            # 获取文件大小和修改时间
            file_size = ""
            modified_time = ""
            try:
                if is_dir:
                    # 文件夹：显示"文件夹"文字
                    file_size = "文件夹"
                else:
                    # 文件：显示文件大小
                    size = os.path.getsize(full_path)
                    file_size = self._format_size(size)
                # 获取修改时间（文件夹和文件都显示）
                mtime = os.path.getmtime(full_path)
                import datetime
                modified_time = datetime.datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            
            # 检查是否收藏
            is_favorited = full_path in favorited_resourcepacks
            
            # 缓存资源包数据
            self._cached_resourcepacks.append((name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable))
        
        self._cache_valid = True  # 标记缓存有效
        logger.info(f"Cached {len(self._cached_resourcepacks)} resourcepacks and {len(self._cached_folders)} folders")

    def _refresh_display_from_cache(self):
        """从缓存中刷新显示（不重新读取文件系统）"""
        self.file_tree.clear()
        self._item_widgets = {}  # 清空项目部件缓存
        
        # 应用搜索过滤（按名称）
        filtered_folders = self._cached_folders
        filtered_resourcepacks = self._cached_resourcepacks
        
        if self._search_text:
            search_lower = self._search_text.lower()
            filtered_folders = [(n, d, p) for n, d, p in filtered_folders if search_lower in n.lower()]
            filtered_resourcepacks = [(n, d, p, i, desc, fs, mt, fav, ed) for n, d, p, i, desc, fs, mt, fav, ed in filtered_resourcepacks if search_lower in n.lower()]
        
        # 获取最新的收藏状态
        favorited_resourcepacks = []
        if self.config_manager:
            config = self.config_manager.config if hasattr(self.config_manager, 'config') else self.config_manager
            favorited_resourcepacks = config.get("favorited_resourcepacks", [])
        
        # 分离收藏和非收藏的资源包
        favorites = []
        non_favorites = []
        for item in filtered_resourcepacks:
            name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable = item
            # 更新收藏状态
            is_favorited = full_path in favorited_resourcepacks
            if is_favorited:
                favorites.append((name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable))
            else:
                non_favorites.append((name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable))
        
        # 应用筛选（仅显示收藏）
        if self._filter_favorites_only:
            non_favorites = []
        
        # 应用排序
        def get_sort_key(item):
            name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable = item
            if self._sort_by == "name":
                return name.lower()
            elif self._sort_by == "size":
                # 从缓存的 file_size 解析大小
                if is_dir:
                    return 0
                try:
                    # 解析文件大小字符串
                    size_str = file_size.replace(" B", "").replace(" KB", "").replace(" MB", "").replace(" GB", "").strip()
                    size = float(size_str)
                    if "KB" in file_size:
                        size *= 1024
                    elif "MB" in file_size:
                        size *= 1024 * 1024
                    elif "GB" in file_size:
                        size *= 1024 * 1024 * 1024
                    return int(size)
                except:
                    return 0
            elif self._sort_by == "time":
                # 解析修改时间
                try:
                    import datetime
                    dt = datetime.datetime.strptime(modified_time, "%Y-%m-%d %H:%M")
                    return dt.timestamp()
                except:
                    return 0
            return item[0]
        
        # 排序收藏和非收藏的资源包
        reverse = (self._sort_order == "desc")
        favorites.sort(key=get_sort_key, reverse=reverse)
        non_favorites.sort(key=get_sort_key, reverse=reverse)
        
        # 文件夹置顶显示（按名称排序）
        filtered_folders.sort(key=lambda x: x[0])
        
        # 添加文件夹
        for name, is_dir, full_path in filtered_folders:
            self._add_item(name, is_dir, full_path)
        
        # 先添加收藏的资源包
        for name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable in favorites:
            self._add_resourcepack_item_from_cache(name, is_dir, full_path, is_favorited, icon_pixmap, description, file_size, modified_time, is_editable)
        
        # 再添加非收藏的资源包
        for name, is_dir, full_path, icon_pixmap, description, file_size, modified_time, is_favorited, is_editable in non_favorites:
            self._add_resourcepack_item_from_cache(name, is_dir, full_path, is_favorited, icon_pixmap, description, file_size, modified_time, is_editable)
        
        # 检查当前路径是否为版本隔离的子路径
        is_version_subpath = self.base_path and self.current_path != self.base_path and "versions" in self.current_path
        
        # 如果没有内容，显示空标签并隐藏 file_tree
        if self.file_tree.topLevelItemCount() == 0:
            self.file_tree.hide()
            self.empty_label.setText(self.translate("file_explorer_empty"))
            self.empty_label.show()
        else:
            self.empty_label.hide()
            self.file_tree.show()
        
        # 在无滚动模式下，根据内容更新file_tree的高度
        if self.no_scroll:
            # 主路径：使用最小高度，允许内容超出时父级容器滚动
            # 计算实际内容高度
            item_count = self.file_tree.topLevelItemCount()
            # ResourcepackItemWidget 的高度是 80 * dpi_scale
            # 每个项目的总高度 = widget高度(80) + padding(8+8) + border-bottom(1)
            item_height = int(80 * self.dpi_scale) + int(16 * self.dpi_scale) + 1
            total_height = max(1, item_count * item_height)  # 至少为1
            self.file_tree.setMinimumHeight(total_height)
            self.file_tree.setMaximumHeight(total_height)
    
    def _add_resourcepack_item_from_cache(self, name, is_dir, full_path, is_favorited, icon_pixmap, description, file_size, modified_time, is_editable):
        """从缓存添加资源包项目（带收藏按钮，使用卡片样式）"""
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, full_path)
        self.file_tree.addTopLevelItem(item)
        
        logger.debug(f"Adding resourcepack item from cache: {name}, icon_pixmap: {icon_pixmap is not None}, is_editable: {is_editable}")
        
        # 创建自定义部件并设置为项目的部件
        def on_favorite_clicked():
            self._toggle_favorite_resourcepack(full_path, name)
        
        def on_edit_clicked():
            self._edit_resourcepack(full_path, name)
        
        widget = ResourcepackItemWidget(
            parent=self.file_tree,
            on_favorite_clicked=on_favorite_clicked,
            on_edit_clicked=on_edit_clicked,
            is_favorited=is_favorited,
            dpi_scale=self.dpi_scale,
            resourcepack_name=name,
            icon=icon_pixmap,
            is_editable=is_editable,
            text_renderer=self.text_renderer,
            description=description,
            file_size=file_size,
            modified_time=modified_time
        )
        
        # 存储部件引用
        self._item_widgets[full_path] = widget
        
        # 设置项目部件
        self.file_tree.setItemWidget(item, 0, widget)
        
        if is_dir:
            # 添加占位子项
            QTreeWidgetItem(item).setText(0, "...")

    def _on_search_changed(self, text):
        """搜索框内容变化时触发（使用防抖优化性能）"""
        self._search_text = text.strip()
        
        # 如果已有定时器，先停止它
        if self._search_timer is not None:
            self._search_timer.stop()
        
        # 创建防抖定时器（300ms 延迟）
        from PyQt6.QtCore import QTimer
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._perform_search)
        self._search_timer.start(300)  # 300ms 防抖延迟
    
    def _perform_search(self):
        """执行实际的搜索操作"""
        if self.current_path:
            # 使用缓存的资源包数据，不重新加载文件系统
            self._refresh_display_from_cache()

    def _toggle_filter_favorites(self):
        """切换筛选（仅显示收藏）"""
        self._filter_favorites_only = not self._filter_favorites_only
        # 更新筛选按钮样式
        if self._filter_favorites_only:
            self.filter_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(100, 150, 255, 0.6);
                    border: 1px solid rgba(100, 150, 255, 0.8);
                    border-radius: {int(6 * self.dpi_scale)}px;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: rgba(100, 150, 255, 0.8);
                }}
            """)
        else:
            self.filter_btn.setStyleSheet(f"""
                QPushButton {{
                    background: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: {int(6 * self.dpi_scale)}px;
                    padding: 0;
                }}
                QPushButton:hover {{
                    background: rgba(255, 255, 255, 0.2);
                }}
            """)
        if self.current_path:
            # 使用缓存刷新显示
            self._refresh_display_from_cache()

    def _show_sort_menu(self):
        """显示排序菜单"""
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)

        # 创建排序方式子菜单
        sort_by_menu = menu.addMenu(self.translate("resourcepack_sort_name"))

        # 排序选项
        sort_options = [
            ("name", self.translate("resourcepack_sort_name")),
            ("size", self.translate("resourcepack_sort_size")),
            ("time", self.translate("resourcepack_sort_time")),
        ]

        for sort_type, text in sort_options:
            action = sort_by_menu.addAction(text)
            if sort_type == self._sort_by:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, st=sort_type: self._on_sort_by_selected(st))

        # 创建排序顺序子菜单
        sort_order_menu = menu.addMenu(self.translate("resourcepack_sort_asc"))

        order_options = [
            ("asc", self.translate("resourcepack_sort_asc")),
            ("desc", self.translate("resourcepack_sort_desc")),
        ]

        for order_type, text in order_options:
            action = sort_order_menu.addAction(text)
            if order_type == self._sort_order:
                action.setCheckable(True)
                action.setChecked(True)
            action.triggered.connect(lambda checked, ot=order_type: self._on_sort_order_selected(ot))

        # 在排序按钮下方显示菜单
        button = self.sort_btn
        global_pos = button.mapToGlobal(button.rect().bottomLeft())
        menu.exec(global_pos)

    def _on_sort_by_selected(self, sort_type):
        """排序方式选择"""
        self._sort_by = sort_type
        if self.current_path:
            # 使用缓存刷新显示
            self._refresh_display_from_cache()

    def _on_sort_order_selected(self, order_type):
        """排序顺序选择"""
        self._sort_order = order_type
        if self.current_path:
            # 使用缓存刷新显示
            self._refresh_display_from_cache()

    def on_item_double_clicked(self, item, column):
        """双击项目事件"""
        full_path = item.data(0, Qt.ItemDataRole.UserRole)
        if full_path and os.path.isdir(full_path):
            self.current_path = full_path
            display_path = self._format_path_display(full_path)
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(True)
            self.path_card.show()
            self._load_directory(full_path)
        elif full_path:
            self.file_selected.emit(full_path)
    
    def _get_folder_icon(self):
        """获取文件夹图标"""
        # 可以根据需要返回不同的图标
        return None

    def _get_resourcepack_icon(self, full_path, is_dir):
        """获取资源包图标（pack.png），图标大小适配卡片高度96px"""
        pixmap = self._get_resourcepack_icon_pixmap(full_path, is_dir)
        if pixmap:
            return QIcon(pixmap)
        return None

    def _get_resourcepack_icon_pixmap(self, full_path, is_dir):
        """获取资源包图标（pack.png）作为QPixmap，图标大小适配卡片高度90px"""
        try:
            is_valid_pack = False  # 标记是否是有效的材质包

            # 检查是否有pack.mcmeta文件来判断是否是材质包
            if is_dir:
                is_valid_pack = os.path.exists(os.path.join(full_path, "pack.mcmeta"))
            elif full_path.endswith('.zip'):
                try:
                    with zipfile.ZipFile(full_path, 'r') as zip_ref:
                        pack_mcmeta_files = [f for f in zip_ref.namelist() if f.lower().endswith('pack.mcmeta')]
                        is_valid_pack = len(pack_mcmeta_files) > 0
                except Exception:
                    pass

            if is_dir:
                # 文件夹形式的资源包
                icon_path = os.path.join(full_path, "pack.png")
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # 缩放图标以适配卡片高度（64px，与ResourcepackItemWidget一致）
                        icon_size = int(64 * self.dpi_scale)
                        scaled_pixmap = pixmap.scaled(
                            icon_size, icon_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        return scaled_pixmap
            elif full_path.endswith('.zip'):
                # 压缩包形式的资源包
                try:
                    with zipfile.ZipFile(full_path, 'r') as zip_ref:
                        # 查找pack.png（不区分大小写）
                        pack_png_files = [f for f in zip_ref.namelist() if f.lower().endswith('pack.png')]
                        if pack_png_files:
                            pack_png_path = pack_png_files[0]
                            with zip_ref.open(pack_png_path) as img_file:
                                img_data = img_file.read()
                                pixmap = QPixmap()
                                if pixmap.loadFromData(img_data):
                                    # 缩放图标以适配卡片高度（64px）
                                    icon_size = int(64 * self.dpi_scale)
                                    scaled_pixmap = pixmap.scaled(
                                        icon_size, icon_size,
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation
                                    )
                                    return scaled_pixmap
                except Exception:
                    pass

            # 没有找到pack.png时，根据是否是有效材质包返回默认图标
            if is_valid_pack:
                # 是材质包但没有图标，使用unknown_pack.png
                default_icon_path = "png/unknown_pack.png"
                if os.path.exists(default_icon_path):
                    pixmap = QPixmap(default_icon_path)
                    if not pixmap.isNull():
                        icon_size = int(64 * self.dpi_scale)
                        scaled_pixmap = pixmap.scaled(
                            icon_size, icon_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        return scaled_pixmap
            elif is_dir:
                # 不是材质包的文件夹，使用folder2.svg
                folder_icon = load_svg_icon("svg/folder2.svg", self.dpi_scale)
                if folder_icon:
                    icon_size = int(64 * self.dpi_scale)
                    scaled_pixmap = folder_icon.scaled(
                        icon_size, icon_size,
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    return scaled_pixmap

            return None
        except Exception:
            return None
    
    def _format_size(self, size):
        """格式化文件大小"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} GB"

    def _is_valid_resourcepack(self, full_path, is_dir):
        """检查文件/文件夹是否是有效的资源包（存在 pack.mcmeta）"""
        try:
            if is_dir:
                # 文件夹形式的资源包
                return os.path.exists(os.path.join(full_path, "pack.mcmeta"))
            elif full_path.endswith('.zip'):
                # 压缩包形式的资源包
                try:
                    with zipfile.ZipFile(full_path, 'r') as zip_ref:
                        pack_mcmeta_files = [f for f in zip_ref.namelist() if f.lower().endswith('pack.mcmeta')]
                        return len(pack_mcmeta_files) > 0
                except Exception:
                    pass
            return False
        except Exception:
            return False

    def _is_resourcepack_editable(self, full_path, is_dir):
        """检查资源包是否可编辑（存在 packset.json）"""
        try:
            # 首先检查是否是有效的材质包（存在pack.mcmeta）
            is_valid_pack = self._is_valid_resourcepack(full_path, is_dir)

            # 只有有效的材质包才检查是否可编辑
            if not is_valid_pack:
                return False

            if is_dir:
                # 文件夹形式的资源包，检查根目录是否有packset.json
                return os.path.exists(os.path.join(full_path, "packset.json"))
            elif full_path.endswith('.zip'):
                # 压缩包形式的资源包，检查根目录是否有packset.json
                try:
                    with zipfile.ZipFile(full_path, 'r') as zip_ref:
                        # 查找根目录的packset.json（不区分大小写）
                        pack_rst_files = [f for f in zip_ref.namelist() if f.lower().endswith('packset.json') and f.count('/') == 0]
                        return len(pack_rst_files) > 0
                except Exception:
                    pass
            return False
        except Exception:
            return False

    def _get_resourcepack_description(self, full_path, is_dir):
        """从 pack.mcmeta 中获取资源包描述"""
        import json
        try:
            if is_dir:
                # 文件夹形式的资源包
                mcmeta_path = os.path.join(full_path, "pack.mcmeta")
                if os.path.exists(mcmeta_path):
                    with open(mcmeta_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        description = data.get("pack", {}).get("description", "")
                        return self._parse_minecraft_text_component(description)
            elif full_path.endswith('.zip'):
                # 压缩包形式的资源包
                try:
                    with zipfile.ZipFile(full_path, 'r') as zip_ref:
                        # 查找根目录的pack.mcmeta（不区分大小写）
                        pack_mcmeta_files = [f for f in zip_ref.namelist() if f.lower().endswith('pack.mcmeta') and f.count('/') == 0]
                        if pack_mcmeta_files:
                            pack_mcmeta_path = pack_mcmeta_files[0]
                            with zip_ref.open(pack_mcmeta_path) as mcmeta_file:
                                mcmeta_data = mcmeta_file.read().decode('utf-8')
                                data = json.loads(mcmeta_data)
                                description = data.get("pack", {}).get("description", "")
                                return self._parse_minecraft_text_component(description)
                except Exception:
                    pass
            return ""
        except Exception:
            return ""

    def _parse_minecraft_text_component(self, component):
        """解析Minecraft文本组件，支持字符串、对象和数组格式"""
        if isinstance(component, str):
            # 简单字符串
            return component
        elif isinstance(component, dict):
            # 单个文本组件
            text = component.get("text", "")
            # 如果有嵌套的额外文本（如 with、extra 等），可以递归处理
            if "extra" in component:
                extra_text = self._parse_minecraft_text_component(component["extra"])
                text = text + extra_text
            return text
        elif isinstance(component, list):
            # 文本组件数组
            result = []
            for item in component:
                result.append(self._parse_minecraft_text_component(item))
            return "".join(result)
        return ""

    def update_font(self, font_family):
        """更新字体"""
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'
        
        # 更新页面标题字体
        if hasattr(self, 'page_title'):
            self.page_title.setStyleSheet(f"""
                QLabel {{
                    color: white;
                    background: transparent;
                    font-size: {int(20 * self.dpi_scale)}px;
                    font-weight: bold;
                    font-family: {font_family_quoted};
                }}
            """)
        
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255,255,255, 0.7);
                background: transparent;
                font-size: {int(13 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
        """)
        
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: rgba(0, 0, 0, 0.2);
                border:1px solid rgba(255, 255, 255, 0.1);
                border-radius: {int(4 * self.dpi_scale)}px;
                color: rgba(255, 255, 255, 0.9);
                font-family: {font_family_quoted};
            }}
            QTreeWidget::item {{
                padding: {int(4 * self.dpi_scale)}px;
            }}
            QTreeWidget::item:hover {{
                background: rgba(255, 255, 255, 0.1);
            }}
            QTreeWidget::item:selected {{
                background: rgba(100, 150, 255, 0.3);
                color: white;
            }}
            QTreeWidget::branch {{
                background: transparent;
            }}
            QTreeWidget::branch:has-children:closed {{
                image: none;
            }}
            QTreeWidget::branch:has-children:open {{
                image: none;
            }}
            QHeaderView::section {{
                background: rgba(255, 255, 255, 0.08);
                color: rgba(255, 255, 255, 0.7);
                padding: {int(6 * self.dpi_scale)}px;
                border: none;
                border-right: 1px solid rgba(255, 255, 255, 0.1);
                font-size: {int(11 * self.dpi_scale)}px;
                font-weight: bold;
                font-family: {font_family_quoted};
            }}
        """)
