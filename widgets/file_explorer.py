"""文件浏览器组件"""

import os
import logging
import zipfile
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtWidgets import (QFileDialog, QHBoxLayout, QHeaderView, QLabel,
                             QPushButton, QTreeWidget, QTreeWidgetItem,
                             QVBoxLayout, QWidget)
from utils import load_svg_icon, scale_icon_for_display

logger = logging.getLogger(__name__)


class ResourcepackItemWidget(QWidget):
    """资源包项目部件，支持收藏按钮"""
    
    def __init__(self, parent=None, on_favorite_clicked=None, is_favorited=False, dpi_scale=1.0):
        super().__init__(parent)
        self.dpi_scale = dpi_scale
        self.on_favorite_clicked = on_favorite_clicked
        self.is_favorited = is_favorited
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 标签（用于显示资源包名称）
        self.name_label = QLabel()
        self.name_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: transparent;
            }
        """)
        layout.addWidget(self.name_label)
        
        # 收藏按钮
        self.bookmark_btn = QPushButton()
        self.bookmark_btn.setFixedSize(int(20 * dpi_scale), int(20 * dpi_scale))
        self.bookmark_btn.setStyleSheet("""
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
        self.bookmark_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.bookmark_btn.clicked.connect(self._on_bookmark_clicked)
        
        # 设置初始图标状态
        self._update_bookmark_icon()
        
        layout.addWidget(self.bookmark_btn)
    
    def set_name(self, name):
        """设置资源包名称"""
        self.name_label.setText(name)
    
    def _on_bookmark_clicked(self):
        """收藏按钮点击事件"""
        if self.on_favorite_clicked:
            self.on_favorite_clicked()
    
    def _update_bookmark_icon(self):
        """更新收藏图标"""
        if self.is_favorited:
            bookmark_pixmap = load_svg_icon("svg/bookmarks-fill.svg", self.dpi_scale)
        else:
            bookmark_pixmap = load_svg_icon("svg/bookmarks.svg", self.dpi_scale)
        
        if bookmark_pixmap:
            self.bookmark_btn.setIcon(QIcon(scale_icon_for_display(bookmark_pixmap, 16, self.dpi_scale)))
        else:
            self.bookmark_btn.setIcon(QIcon())
    
    def set_favorited(self, is_favorited):
        """设置收藏状态"""
        self.is_favorited = is_favorited
        self._update_bookmark_icon()


class FileExplorer(QWidget):
    """文件浏览器组件"""

    file_selected = pyqtSignal(str)  # 文件选择信号

    def __init__(self, parent=None, dpi_scale=1.0, config_manager=None):
        super().__init__(parent)
        self.dpi_scale = dpi_scale
        self.config_manager = config_manager
        self.current_path = None
        self.root_path = None  # 保存minecraft路径
        self.base_path = None  # 保存当前resourcepacks路径作为返回的根目录
        self.resourcepack_mode = False  # 是否为资源包浏览模式
        self._item_widgets = {}  # 存储资源包项目部件：{full_path: widget}
        self._init_ui()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        toolbar = QWidget()
        toolbar.setFixedHeight(int(36 * self.dpi_scale))
        toolbar.setStyleSheet("background: rgba(255, 255, 255, 0.08);")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(int(12 * self.dpi_scale), 0, int(12 * self.dpi_scale), 0)
        toolbar_layout.setSpacing(int(8 * self.dpi_scale))

        # 当前路径标签（默认隐藏）
        self.path_label = QLabel("未选择路径")
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255,255,255, 0.7);
                background: transparent;
                font-size: {int(12 * self.dpi_scale)}px;
            }}
        """)
        toolbar_layout.addWidget(self.path_label)

        toolbar_layout.addStretch()

        # 返回按钮
        self.back_btn = QPushButton("返回根目录")
        self.back_btn.setFixedHeight(int(24 * self.dpi_scale))
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(4 * self.dpi_scale)}px;
                color: white;
                padding: 0 {int(12 * self.dpi_scale)}px;
                font-size: {int(11 * self.dpi_scale)}px;
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
        toolbar_layout.addWidget(self.back_btn)

        layout.addWidget(toolbar)
        
        # 文件树
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderHidden(True)  # 隐藏表头（包含名称和大小列）
        self.file_tree.setColumnCount(1)  # 只显示一列（名称）
        # 设置图标大小（88px，适配卡片高度96px）
        self.file_tree.setIconSize(QSize(int(88 * self.dpi_scale), int(88 * self.dpi_scale)))
        # 设置资源包项目的高度（DPI缩放前的96px）
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: rgba(0, 0, 0, 0.2);
                border:1px solid rgba(255, 255, 255, 0.1);
                border-radius: {int(4 * self.dpi_scale)}px;
                color: rgba(255, 255, 255, 0.9);
            }}
            QTreeWidget::item {{
                padding: {int(4 * self.dpi_scale)}px;
                height: {int(96 * self.dpi_scale)}px;
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
            }}
        """)
        
        header = self.file_tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        
        self.file_tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        layout.addWidget(self.file_tree)
        
        # 空状态提示
        self.empty_label = QLabel("请选择 Minecraft 安装路径")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255,255,255, 0.5);
                background: transparent;
                font-size: {int(13 * self.dpi_scale)}px;
                padding: {int(40 * self.dpi_scale)}px;
            }}
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label, 1)
    
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
            self.empty_label.hide()
            self.file_tree.show()
            self._load_directory(self.current_path)
        else:
            self.empty_label.setText(f"路径不存在: {self.current_path}")
            self.empty_label.show()
            self.file_tree.hide()

    def _format_path_display(self, path):
        """格式化路径显示（统一使用反斜杠，只显示base_path内的路径）"""
        # 在资源包模式下，只显示base_path内的路径
        if self.resourcepack_mode and self.base_path:
            if path.startswith(self.base_path):
                # 只显示base_path文件夹内的路径
                sub_path = path[len(self.base_path):].lstrip(os.sep).lstrip("/")
                # 统一使用反斜杠
                sub_path = sub_path.replace("/", "\\")
                return sub_path if sub_path else "资源包文件夹"

        # 默认显示完整路径
        full_path = path.replace("/", "\\")
        if len(full_path) < 50:
            return full_path
        else:
            return "..." + full_path[-47:]
    def navigate_to_root(self):
        """返回根目录（base_path，即当前选定的resourcepacks文件夹）"""
        if self.base_path and os.path.exists(self.base_path):
            self.current_path = self.base_path
            display_path = self._format_path_display(self.current_path)
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(False)
            self._load_directory(self.current_path)

    def navigate_to_directory(self, path):
        """导航到指定目录"""
        if not os.path.exists(path):
            self.empty_label.setText(f"路径不存在: {path}")
            self.empty_label.show()
            self.file_tree.hide()
            return

        self.current_path = path
        display_path = self._format_path_display(path)
        self.path_label.setText(display_path)
        self.back_btn.setEnabled(True)
        self.empty_label.hide()
        self.file_tree.show()
        self._load_directory(path)

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
            self.empty_label.hide()
            self.file_tree.show()
            self._load_directory(self.current_path)
        else:
            self.empty_label.setText(f"路径不存在: {self.current_path}")
            self.empty_label.show()
            self.file_tree.hide()
    
    def navigate_to_version_resourcepacks(self, version_name):
        """导航到指定版本的resourcepacks文件夹"""
        if not self.root_path:
            return

        version_path = os.path.join(self.root_path, "versions", version_name)
        if not os.path.exists(version_path):
            self.empty_label.setText(f"版本不存在: {version_name}")
            self.empty_label.show()
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
            self.empty_label.hide()
            self.file_tree.show()
            self._load_directory(resourcepacks_path)
        else:
            self.empty_label.setText(f"版本 {version_name} 没有resourcepacks文件夹")
            self.empty_label.show()
            self.file_tree.hide()
    
    def _load_directory(self, path):
        """加载目录内容"""
        self.file_tree.clear()
        self._item_widgets = {}  # 清空项目部件缓存

        # 隐藏空状态提示
        self.empty_label.hide()
        self.file_tree.show()

        if not os.path.exists(path):
            self.empty_label.setText(f"路径不存在: {path}")
            self.empty_label.show()
            self.file_tree.hide()
            return

        if not os.path.isdir(path):
            self.empty_label.setText(f"不是目录: {path}")
            self.empty_label.show()
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

            # 在资源包模式下，分离收藏和非收藏的资源包
            if self.resourcepack_mode:
                resourcepack_items = []
                for name, is_dir, full_path in items:
                    if is_dir or name.endswith('.zip'):
                        resourcepack_items.append((name, is_dir, full_path))
                
                # 分离收藏和非收藏
                favorites = []
                non_favorites = []
                for name, is_dir, full_path in resourcepack_items:
                    if full_path in favorited_resourcepacks:
                        favorites.append((name, is_dir, full_path))
                    else:
                        non_favorites.append((name, is_dir, full_path))
                
                # 先添加收藏的资源包
                for name, is_dir, full_path in favorites:
                    self._add_resourcepack_item(name, is_dir, full_path, is_favorited=True)
                
                # 再添加非收藏的资源包
                for name, is_dir, full_path in non_favorites:
                    self._add_resourcepack_item(name, is_dir, full_path, is_favorited=False)
            else:
                # 非资源包模式，正常显示
                for name, is_dir, full_path in items:
                    self._add_item(name, is_dir, full_path)

        except PermissionError:
            self.empty_label.setText("无权限访问此目录")
            self.empty_label.show()
            self.file_tree.hide()
        except Exception as e:
            self.empty_label.setText(f"加载目录失败: {str(e)}")
            self.empty_label.show()
            self.file_tree.hide()
    
    def _add_item(self, name, is_dir, full_path):
        """添加普通项目"""
        item = QTreeWidgetItem()
        item.setText(0, name)
        self.file_tree.addTopLevelItem(item)

        if is_dir:
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
            # 添加占位子项
            QTreeWidgetItem(item).setText(0, "...")
        else:
            # 文件：设置路径
            item.setData(0, Qt.ItemDataRole.UserRole, full_path)
    
    def _add_resourcepack_item(self, name, is_dir, full_path, is_favorited):
        """添加资源包项目（带收藏按钮）"""
        item = QTreeWidgetItem()
        item.setData(0, Qt.ItemDataRole.UserRole, full_path)
        self.file_tree.addTopLevelItem(item)

        # 显示pack.png图标
        icon = self._get_resourcepack_icon(full_path, is_dir)
        if icon:
            item.setIcon(0, icon)

        # 创建自定义部件并设置为项目的部件
        def on_favorite_clicked():
            self._toggle_favorite_resourcepack(full_path, name)

        widget = ResourcepackItemWidget(
            parent=self.file_tree,
            on_favorite_clicked=on_favorite_clicked,
            is_favorited=is_favorited,
            dpi_scale=self.dpi_scale
        )
        widget.set_name(name)
        
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
        
        # 重新加载目录以使收藏的资源包置顶
        if self.current_path:
            self._load_directory(self.current_path)
    
    def on_item_double_clicked(self, item, column):
        """双击项目事件"""
        full_path = item.data(0, Qt.ItemDataRole.UserRole)
        if full_path and os.path.isdir(full_path):
            self.current_path = full_path
            display_path = self._format_path_display(full_path)
            self.path_label.setText(display_path)
            self.back_btn.setEnabled(True)
            self._load_directory(full_path)
        elif full_path:
            self.file_selected.emit(full_path)
    
    def _get_folder_icon(self):
        """获取文件夹图标"""
        # 可以根据需要返回不同的图标
        return None

    def _get_resourcepack_icon(self, full_path, is_dir):
        """获取资源包图标（pack.png），图标大小适配卡片高度96px"""
        try:
            icon_path = None

            if is_dir:
                # 文件夹形式的资源包
                icon_path = os.path.join(full_path, "pack.png")
                if os.path.exists(icon_path):
                    pixmap = QPixmap(icon_path)
                    if not pixmap.isNull():
                        # 缩放图标以适配卡片高度（96px，留一些padding）
                        icon_size = int(88 * self.dpi_scale)
                        scaled_pixmap = pixmap.scaled(
                            icon_size, icon_size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        return QIcon(scaled_pixmap)
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
                                    # 缩放图标以适配卡片高度（96px，留一些padding）
                                    icon_size = int(88 * self.dpi_scale)
                                    scaled_pixmap = pixmap.scaled(
                                        icon_size, icon_size,
                                        Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation
                                    )
                                    return QIcon(scaled_pixmap)
                except Exception:
                    pass

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
    
    def update_font(self, font_family):
        """更新字体"""
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        font_family_quoted = f'"{escaped_font}"'
        
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255,255,255, 0.7);
                background: transparent;
                font-size: {int(12 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
        """)
        
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border:1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(4 * self.dpi_scale)}px;
                color: white;
                padding: 0 {int(12 * self.dpi_scale)}px;
                font-size: {int(11 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
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
        
        self.empty_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255,255,255, 0.5);
                background: transparent;
                font-size: {int(13 * self.dpi_scale)}px;
                padding: {int(40 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
        """)
