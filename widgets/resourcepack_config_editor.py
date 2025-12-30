"""资源包配置编辑器组件"""

import os
import json
import logging
import zipfile
from PyQt6.QtCore import Qt, pyqtSignal, QUrl
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QWidget, QCheckBox, QComboBox, QLineEdit,
    QFrame, QSizePolicy, QMessageBox, QGridLayout
)
from utils import load_svg_icon, scale_icon_for_display

logger = logging.getLogger(__name__)


class ResourcepackConfigEditor(QDialog):
    """资源包配置编辑对话框"""

    def __init__(self, parent=None, full_path="", name="", dpi_scale=1.0, text_renderer=None):
        super().__init__(parent)
        self.full_path = full_path
        self.name = name
        self.dpi_scale = dpi_scale
        self.text_renderer = text_renderer
        self.packset_data = None
        self.config_widgets = {}  # 存储配置项部件 {config_id: widget}
        
        self._init_ui()
        self._load_packset_data()

    def translate(self, key, **kwargs):
        """翻译辅助方法"""
        if self.text_renderer:
            return self.text_renderer.translate(key, **kwargs)
        return key

    def _init_ui(self):
        """初始化UI"""
        self.setWindowTitle(f"资源包配置 - {self.name}")
        self.setFixedWidth(int(600 * self.dpi_scale))
        self.setMinimumHeight(int(400 * self.dpi_scale))
        
        # 设置窗口样式
        self.setStyleSheet(f"""
            QDialog {{
                background-color: #1a1a2e;
                color: white;
            }}
            QLabel {{
                color: white;
            }}
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                color: white;
                padding: {int(8 * self.dpi_scale)}px {int(16 * self.dpi_scale)}px;
                font-size: {int(12 * self.dpi_scale)}px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: rgba(255, 255, 255, 0.3);
            }}
            QScrollArea {{
                border: none;
                background: transparent;
            }}
            QCheckBox {{
                color: white;
                font-size: {int(12 * self.dpi_scale)}px;
                spacing: {int(8 * self.dpi_scale)}px;
            }}
            QCheckBox::indicator {{
                width: {int(18 * self.dpi_scale)}px;
                height: {int(18 * self.dpi_scale)}px;
                border: 2px solid rgba(255, 255, 255, 0.3);
                border-radius: {int(4 * self.dpi_scale)}px;
                background: rgba(255, 255, 255, 0.1);
            }}
            QCheckBox::indicator:checked {{
                background: rgba(100, 150, 255, 0.8);
                border: 2px solid rgba(100, 150, 255, 1.0);
            }}
            QCheckBox::indicator:hover {{
                border: 2px solid rgba(255, 255, 255, 0.5);
            }}
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                color: white;
                padding: {int(6 * self.dpi_scale)}px {int(10 * self.dpi_scale)}px;
                font-size: {int(12 * self.dpi_scale)}px;
                min-height: {int(32 * self.dpi_scale)}px;
            }}
            QComboBox:hover {{
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
            QComboBox::drop-down {{
                border: none;
                width: {int(24 * self.dpi_scale)}px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border: {int(3 * self.dpi_scale)}px solid rgba(255, 255, 255, 0.7);
                margin-top: {int(4 * self.dpi_scale)}px;
                margin-bottom: {int(4 * self.dpi_scale)}px;
                border-left: none;
                border-top: none;
                border-right: none;
                width: {int(8 * self.dpi_scale)}px;
            }}
            QComboBox QAbstractItemView {{
                background: #1a1a2e;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(6 * self.dpi_scale)}px;
                selection-background-color: rgba(100, 150, 255, 0.5);
                selection-color: white;
                padding: {int(4 * self.dpi_scale)}px;
            }}
        """)
        
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(int(20 * self.dpi_scale), int(20 * self.dpi_scale), int(20 * self.dpi_scale), int(20 * self.dpi_scale))
        layout.setSpacing(int(16 * self.dpi_scale))
        
        # 标题
        title_label = QLabel("资源包配置")
        title_font = QFont()
        title_font.setFamily("Microsoft YaHei UI")
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setPointSize(int(18 * self.dpi_scale))
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 分隔线
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        separator.setStyleSheet(f"""
            QFrame {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                max-height: 1px;
            }}
        """)
        layout.addWidget(separator)
        
        # 配置项容器（带滚动）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # 配置项内容区域
        self.config_content = QWidget()
        self.config_layout = QVBoxLayout(self.config_content)
        self.config_layout.setContentsMargins(0, 0, 0, 0)
        self.config_layout.setSpacing(int(12 * self.dpi_scale))
        self.config_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.config_content)
        layout.addWidget(scroll_area, 1)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(int(10 * self.dpi_scale))
        
        save_button = QPushButton("保存")
        save_button.setFixedHeight(int(36 * self.dpi_scale))
        save_button.clicked.connect(self._on_save_clicked)
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.setFixedHeight(int(36 * self.dpi_scale))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)

    def _load_packset_data(self):
        """加载 packset.json 数据"""
        try:
            packset_json = None
            
            if os.path.isdir(self.full_path):
                # 文件夹形式的资源包
                packset_path = os.path.join(self.full_path, "packset.json")
                if os.path.exists(packset_path):
                    with open(packset_path, 'r', encoding='utf-8') as f:
                        packset_json = f.read()
            elif self.full_path.endswith('.zip'):
                # 压缩包形式的资源包
                try:
                    with zipfile.ZipFile(self.full_path, 'r') as zip_ref:
                        # 查找根目录的packset.json
                        packset_files = [f for f in zip_ref.namelist() if f.lower().endswith('packset.json') and f.count('/') == 0]
                        if packset_files:
                            with zip_ref.open(packset_files[0]) as packset_file:
                                packset_json = packset_file.read().decode('utf-8')
                except Exception as e:
                    logger.error(f"Error reading packset.json from zip: {e}")
            
            if packset_json:
                self.packset_data = json.loads(packset_json)
                self._validate_and_create_ui()
            else:
                self._show_error_message("格式不正确：未找到 packset.json 文件")
        except json.JSONDecodeError as e:
            self._show_error_message(f"格式不正确：JSON 解析失败 - {str(e)}")
        except Exception as e:
            self._show_error_message(f"格式不正确：{str(e)}")

    def _validate_and_create_ui(self):
        """验证 packset.json 格式并创建 UI"""
        if not self.packset_data:
            self._show_error_message("格式不正确：数据为空")
            return
        
        # 检查必需的字段
        if not isinstance(self.packset_data, dict):
            self._show_error_message("格式不正确：根对象必须是字典")
            return
        
        schema_version = self.packset_data.get("schema_version")
        if schema_version != 1:
            self._show_error_message(f"格式不正确：不支持的 schema_version {schema_version}，当前仅支持版本 1")
            return
        
        feature = self.packset_data.get("feature")
        if not isinstance(feature, dict):
            self._show_error_message("格式不正确：feature 必须是字典")
            return
        
        config = self.packset_data.get("config")
        if not isinstance(config, dict):
            self._show_error_message("格式不正确：config 必须是字典")
            return
        
        # 验证通过，创建配置项 UI
        self._create_config_items_ui(feature, config)

    def _create_config_items_ui(self, feature, config):
        """创建配置项 UI"""
        # 遍历 feature，创建对应的功能组
        for feature_name, feature_type in feature.items():
            if feature_name not in config:
                continue
            
            feature_config = config[feature_name]
            feature_type = feature_type.strip().lower()
            
            # 创建功能组标题
            group_title = QLabel(feature_name)
            title_font = QFont()
            title_font.setFamily("Microsoft YaHei UI")
            title_font.setWeight(QFont.Weight.Bold)
            title_font.setPointSize(int(14 * self.dpi_scale))
            group_title.setFont(title_font)
            group_title.setStyleSheet("color: rgba(255, 255, 255, 0.9); margin-top: 8px;")
            self.config_layout.addWidget(group_title)
            
            # 创建功能组容器
            group_container = QWidget()
            group_container.setStyleSheet(f"""
                QWidget {{
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: {int(8 * self.dpi_scale)}px;
                }}
            """)
            group_layout = QVBoxLayout(group_container)
            group_layout.setContentsMargins(int(12 * self.dpi_scale), int(12 * self.dpi_scale), int(12 * self.dpi_scale), int(12 * self.dpi_scale))
            group_layout.setSpacing(int(8 * self.dpi_scale))
            
            # 根据 feature 类型创建配置项
            if feature_type == "bool":
                # switch 功能：开关（勾选框）
                self._create_switch_items(group_layout, feature_config)
            elif feature_type == "toggle":
                # status 功能：切换（下拉菜单）
                self._create_status_items(group_layout, feature_config)
            
            self.config_layout.addWidget(group_container)

    def _create_switch_items(self, layout, feature_config):
        """创建开关类型的配置项"""
        toggle_list = feature_config.get("toggle", [])
        default_value = feature_config.get("default", "false").lower() == "true"
        
        for item in toggle_list:
            item_id = item.get("id", "")
            file_path = item.get("file_path", "")
            
            # 使用 id 作为配置项名称
            item_label = QLabel(f"{item_id}")
            item_font = QFont()
            item_font.setFamily("Microsoft YaHei UI")
            item_font.setWeight(QFont.Weight.Normal)
            item_font.setPointSize(int(12 * self.dpi_scale))
            item_label.setFont(item_font)
            item_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            
            # 创建勾选框
            checkbox = QCheckBox()
            checkbox.setChecked(default_value)
            checkbox.setMinimumHeight(int(24 * self.dpi_scale))
            
            # 存储配置项部件
            self.config_widgets[f"{item_id}_bool"] = checkbox
            
            # 添加到布局
            item_layout = QHBoxLayout()
            item_layout.setSpacing(int(10 * self.dpi_scale))
            item_layout.addWidget(item_label, 1)
            item_layout.addWidget(checkbox, 0, Qt.AlignmentFlag.AlignRight)
            layout.addLayout(item_layout)

    def _create_status_items(self, layout, feature_config):
        """创建状态切换类型的配置项"""
        scope = feature_config.get("scope", [])
        paths = feature_config.get("paths", [])
        
        for item in paths:
            item_id = item.get("id", "")
            file_path = item.get("file_path", "")
            
            # 使用 id 作为配置项名称
            item_label = QLabel(f"{item_id}")
            item_font = QFont()
            item_font.setFamily("Microsoft YaHei UI")
            item_font.setWeight(QFont.Weight.Normal)
            item_font.setPointSize(int(12 * self.dpi_scale))
            item_label.setFont(item_font)
            item_label.setStyleSheet("color: rgba(255, 255, 255, 0.8);")
            
            # 创建下拉菜单
            combobox = QComboBox()
            combobox.setMinimumWidth(int(150 * self.dpi_scale))
            combobox.addItems(scope)
            if scope:
                combobox.setCurrentIndex(0)
            
            # 存储配置项部件
            self.config_widgets[f"{item_id}_status"] = combobox
            
            # 添加到布局
            item_layout = QHBoxLayout()
            item_layout.setSpacing(int(10 * self.dpi_scale))
            item_layout.addWidget(item_label, 1)
            item_layout.addWidget(combobox, 0, Qt.AlignmentFlag.AlignRight)
            layout.addLayout(item_layout)

    def _show_error_message(self, message):
        """显示错误消息"""
        error_label = QLabel(message)
        error_label.setWordWrap(True)
        error_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 100, 100, 0.9);
                font-size: {int(12 * self.dpi_scale)}px;
                padding: {int(16 * self.dpi_scale)}px;
                background: rgba(255, 100, 100, 0.1);
                border-radius: {int(6 * self.dpi_scale)}px;
                border: 1px solid rgba(255, 100, 100, 0.3);
            }}
        """)
        self.config_layout.addWidget(error_label)

    def _on_save_clicked(self):
        """保存按钮点击事件"""
        # 暂时没有实际保存功能，只显示提示
        QMessageBox.information(self, "提示", "保存功能暂未实现")
        self.accept()
