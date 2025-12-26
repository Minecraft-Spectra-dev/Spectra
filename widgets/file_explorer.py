"""文件浏览器组件"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTreeWidget, QTreeWidgetItem, QHeaderView, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
import os


class FileExplorer(QWidget):
    """文件浏览器组件"""
    
    file_selected = pyqtSignal(str)  # 文件选择信号
    
    def __init__(self, parent=None, dpi_scale=1.0):
        super().__init__(parent)
        self.dpi_scale = dpi_scale
        self.current_path = None
        self.root_path = None
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
        
        # 当前路径标签
        self.path_label = QLabel("未选择路径")
        self.path_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.7);
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
        self.file_tree.setHeaderHidden(False)
        self.file_tree.setColumnCount(2)
        self.file_tree.setHeaderLabels(["名称", "大小"])
        self.file_tree.setStyleSheet(f"""
            QTreeWidget {{
                background: rgba(0, 0, 0, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {int(4 * self.dpi_scale)}px;
                color: rgba(255, 255, 255, 0.9);
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
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
                font-size: {int(13 * self.dpi_scale)}px;
                padding: {int(40 * self.dpi_scale)}px;
            }}
        """)
        self.empty_label.hide()
        layout.addWidget(self.empty_label, 1)
    
    def set_minecraft_path(self, path):
        """设置Minecraft路径"""
        self.root_path = path
        # 根目录应该是 .minecraft/resourcepacks
        resourcepacks_path = os.path.join(path, "resourcepacks")
        self.current_path = resourcepacks_path if os.path.exists(resourcepacks_path) else path
        # 统一使用反斜杠显示路径
        display_path = self._format_path_display(self.current_path)
        self.path_label.setText(display_path)
        self.back_btn.setEnabled(False)

        if os.path.exists(self.current_path):
            self.empty_label.hide()
            self.file_tree.show()
            self._load_directory(self.current_path)
        else:
            self.empty_label.setText(f"路径不存在: {self.current_path}")
            self.empty_label.show()
            self.file_tree.hide()

    def _format_path_display(self, path):
        """格式化路径显示（统一使用反斜杠）"""
        if len(path) < 50:
            return path.replace("/", "\\")
        else:
            return "..." + path[-47:].replace("/", "\\")
    
    def navigate_to_root(self):
        """返回根目录（resourcepacks文件夹）"""
        if self.root_path:
            # 根目录应该是 .minecraft/resourcepacks
            resourcepacks_path = os.path.join(self.root_path, "resourcepacks")
            self.current_path = resourcepacks_path if os.path.exists(resourcepacks_path) else self.root_path
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

            for name, is_dir, full_path in items:
                item = QTreeWidgetItem()
                item.setText(0, name)

                if is_dir:
                    # 只在图标不为None时才设置图标
                    folder_icon = self._get_folder_icon()
                    if folder_icon is not None:
                        item.setIcon(0, folder_icon)
                    item.setData(0, Qt.ItemDataRole.UserRole, full_path)
                    # 添加占位子项
                    QTreeWidgetItem(item).setText(0, "...")
                else:
                    item.setText(1, self._format_size(os.path.getsize(full_path)))
                    item.setData(0, Qt.ItemDataRole.UserRole, full_path)

                self.file_tree.addTopLevelItem(item)

        except PermissionError:
            self.empty_label.setText("无权限访问此目录")
            self.empty_label.show()
            self.file_tree.hide()
        except Exception as e:
            self.empty_label.setText(f"加载目录失败: {str(e)}")
            self.empty_label.show()
            self.file_tree.hide()
    
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
                color: rgba(255, 255, 255, 0.7);
                background: transparent;
                font-size: {int(12 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
        """)
        
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
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
                border: 1px solid rgba(255, 255, 255, 0.1);
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
                color: rgba(255, 255, 255, 0.5);
                background: transparent;
                font-size: {int(13 * self.dpi_scale)}px;
                padding: {int(40 * self.dpi_scale)}px;
                font-family: {font_family_quoted};
            }}
        """)
