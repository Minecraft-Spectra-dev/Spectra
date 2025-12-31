"""资源包配置编辑器页面组件"""

import os
import json
import logging
import zipfile
import shutil
import tempfile
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QCheckBox, QComboBox, QFrame, QMessageBox
)
from ui.components import ToggleSwitch
from utils import load_svg_icon, scale_icon_for_display

logger = logging.getLogger(__name__)


class ZipResourcePackHelper:
    """压缩包资源包辅助类"""

    def __init__(self, zip_path):
        """初始化压缩包辅助类

        Args:
            zip_path: 压缩包文件路径
        """
        self.zip_path = zip_path
        self.temp_dir = None

    def __enter__(self):
        """上下文管理器入口"""
        self.temp_dir = tempfile.mkdtemp(prefix="packset_")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def close(self):
        """关闭并清理临时文件"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def extract_all(self):
        """解压所有文件到临时目录"""
        with zipfile.ZipFile(self.zip_path, 'r') as zip_ref:
            zip_ref.extractall(self.temp_dir)

    def save(self):
        """将临时目录重新打包成压缩包"""
        with zipfile.ZipFile(self.zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_dir)
                    zip_ref.write(file_path, arcname)

    def file_exists(self, relative_path):
        """检查文件是否存在"""
        full_path = os.path.join(self.temp_dir, relative_path)
        return os.path.exists(full_path)

    def rename_file(self, src, dst):
        """重命名文件"""
        src_full = os.path.join(self.temp_dir, src)
        dst_full = os.path.join(self.temp_dir, dst)

        if os.path.exists(src_full):
            if os.path.exists(dst_full):
                os.remove(dst_full)
            os.rename(src_full, dst_full)

    def read_json(self, relative_path):
        """读取 JSON 文件"""
        full_path = os.path.join(self.temp_dir, relative_path)
        with open(full_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def write_json(self, relative_path, data):
        """写入 JSON 文件

        Args:
            relative_path: 相对路径
            data: 要写入的数据（字典或列表）
        """
        full_path = os.path.join(self.temp_dir, relative_path)
        # 确保目录存在
        dir_path = os.path.dirname(full_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


class ResourcepackConfigEditorPage(QWidget):
    """资源包配置编辑器页面"""

    def __init__(self, parent=None, full_path="", name="", dpi_scale=1.0, text_renderer=None, on_back=None):
        super().__init__(parent)
        self.full_path = full_path
        self.name = name
        self.dpi_scale = dpi_scale
        self.text_renderer = text_renderer
        self.on_back = on_back
        self.packset_data = None
        self.config_widgets = {}  # 存储配置项部件 {config_id: widget}
        self.feature_config_map = {}  # 存储配置数据 {feature_name: feature_config}
        self.zip_helper = None  # 压缩包辅助类
        self.packset_lang = {}  # 存储资源包自定义本地化 {lang_code: translations}

        self._init_ui()
        self._load_packset_data()

    def translate(self, key, default=None, **kwargs):
        """翻译辅助方法（资源包专用）

        仅用于资源包配置界面的本地化翻译：

        翻译键格式：
        - category.{category_id}.name
        - category.{category_id}.description
        - feature.{feature_name}

        优先级：
        1. 资源包自定义本地化（packset_lang）
        2. 默认值
        3. 翻译键本身

        Args:
            key: 翻译键
            default: 默认值（可选）
            **kwargs: 格式化参数

        Returns:
            翻译后的文本
        """
        # 获取当前语言代码
        current_lang = None
        if self.text_renderer and hasattr(self.text_renderer, 'language_manager'):
            current_lang = self.text_renderer.language_manager.get_language()

        # 尝试从当前语言的资源包本地化获取
        if current_lang and current_lang in self.packset_lang:
            packset_translations = self.packset_lang[current_lang]
            if key in packset_translations:
                text = packset_translations[key]
                # 支持简单的格式化
                if kwargs:
                    try:
                        text = text.format(**kwargs)
                    except (KeyError, ValueError):
                        pass
                return text

        # 回退到默认值
        if default is not None:
            return default

        # 最后回退到键名本身
        return key

    def _format_path(self, full_path):
        """格式化路径，移除资源包根路径前缀

        Args:
            full_path: 完整路径

        Returns:
            简化后的路径
        """
        if self.full_path and full_path.startswith(self.full_path):
            return full_path[len(self.full_path):].lstrip(os.sep)
        return full_path

    def _init_ui(self):
        """初始化UI"""
        self.setStyleSheet("background:transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(int(12 * self.dpi_scale))
        
        # 标题和返回按钮容器
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_layout = QHBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(int(12 * self.dpi_scale))
        
        # 返回按钮
        back_btn = QPushButton()
        back_btn.setFixedSize(int(24 * self.dpi_scale), int(24 * self.dpi_scale))
        back_btn.setStyleSheet(f"""
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
        back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        back_btn.clicked.connect(self._on_back_clicked)
        
        # 设置返回按钮图标
        back_icon = load_svg_icon("svg/x.svg", self.dpi_scale)
        if back_icon:
            back_btn.setIcon(QIcon(scale_icon_for_display(back_icon, 16, self.dpi_scale)))
        
        title_layout.addWidget(back_btn)
        
        # 标题
        title_label = QLabel()
        title_label.setStyleSheet(
            f"color:white;font-size:{int(20 * self.dpi_scale)}px;"
            f"font-family:'Microsoft YaHei UI';font-weight:bold;"
        )
        title_layout.addWidget(title_label)
        if self.text_renderer:
            self.text_renderer.register_widget(title_label, "resourcepack_config_title", group="resourcepack_config")
        title_layout.addStretch()

        # 保存按钮
        self.save_button = QPushButton()
        self.save_button_applied = False  # 是否显示"已应用"状态
        if self.text_renderer:
            self.save_button.setText(self.text_renderer.translate("resourcepack_config_save"))
        else:
            self.save_button.setText("保存并应用")
        self.save_button.setFixedHeight(int(36 * self.dpi_scale))
        self.save_button.setMinimumWidth(int(80 * self.dpi_scale))
        self.save_button.setStyleSheet(f"""
            QPushButton {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: {int(6 * self.dpi_scale)}px;
                color: white;
                padding: {int(8 * self.dpi_scale)}px {int(16 * self.dpi_scale)}px;
                font-size: {int(12 * self.dpi_scale)}px;
            }}
            QPushButton:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QPushButton:pressed {{
                background: rgba(255, 255, 255, 0.05);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.05);
                color: rgba(255, 255, 255, 0.5);
            }}
        """)
        self.save_button.clicked.connect(self._on_save_clicked)
        # 添加一个spacing使保存按钮左移一些
        title_layout.addWidget(self.save_button)
        title_layout.addSpacing(int(16 * self.dpi_scale))
        
        layout.addWidget(title_container)
        
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
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background: transparent;
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
        
        # 配置项内容区域
        self.config_content = QWidget()
        self.config_content.setStyleSheet("background: transparent;")
        self.config_layout = QVBoxLayout(self.config_content)
        self.config_layout.setContentsMargins(
            int(20 * self.dpi_scale), 0,
            int(20 * self.dpi_scale), 0
        )
        self.config_layout.setSpacing(int(12 * self.dpi_scale))
        self.config_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll_area.setWidget(self.config_content)
        layout.addWidget(scroll_area, 1)

    def _load_packset_lang(self):
        """加载资源包自定义本地化文件

        从 packset_lang 目录加载所有语言的本地化文件
        """
        self.packset_lang = {}

        try:
            if os.path.isdir(self.full_path):
                # 文件夹形式的资源包
                lang_dir = os.path.join(self.full_path, "packset_lang")
                if os.path.exists(lang_dir):
                    for filename in os.listdir(lang_dir):
                        if filename.endswith('.json'):
                            lang_code = filename[:-5]  # 移除 .json 后缀
                            lang_file = os.path.join(lang_dir, filename)
                            try:
                                with open(lang_file, 'r', encoding='utf-8') as f:
                                    self.packset_lang[lang_code] = json.load(f)
                                logger.debug(f"加载资源包本地化文件: {filename} ({lang_code})")
                            except json.JSONDecodeError as e:
                                logger.warning(f"资源包本地化文件格式错误: {filename} - {e}")

            elif self.full_path.endswith('.zip'):
                # 压缩包形式的资源包
                try:
                    with zipfile.ZipFile(self.full_path, 'r') as zip_ref:
                        # 查找 packset_lang 目录下的所有 .json 文件
                        lang_files = [f for f in zip_ref.namelist()
                                     if f.startswith('packset_lang/') and f.endswith('.json')]
                        for lang_file in lang_files:
                            # 提取语言代码 (例如: packset_lang/zh_CN.json -> zh_CN)
                            lang_code = os.path.basename(lang_file)[:-5]
                            try:
                                with zip_ref.open(lang_file) as f:
                                    self.packset_lang[lang_code] = json.load(f)
                                logger.debug(f"加载资源包本地化文件: {lang_file} ({lang_code})")
                            except json.JSONDecodeError as e:
                                logger.warning(f"资源包本地化文件格式错误: {lang_file} - {e}")
                except Exception as e:
                    logger.error(f"读取资源包本地化文件失败: {e}")

            logger.debug(f"资源包自定义本地化加载完成，共 {len(self.packset_lang)} 种语言")
        except Exception as e:
            logger.error(f"加载资源包本地化失败: {e}")

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
                # 加载资源包自定义本地化
                self._load_packset_lang()
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

        # 验证通过，创建配置项 UI（支持分类）
        category = self.packset_data.get("category")
        if category and isinstance(category, dict):
            self._create_category_items_ui(category, feature, config)
        else:
            self._create_config_items_ui(feature, config)

    def _create_config_items_ui(self, feature, config):
        """创建配置项 UI（无分类）"""
        # 加载已保存的配置
        saved_config = self._load_saved_config()

        # 创建单个功能组容器，包含所有配置项
        group_container = QWidget()
        group_container.setStyleSheet(f"background: rgba(255, 255, 255, 0.05); border-radius: {int(8 * self.dpi_scale)}px;")
        group_layout = QVBoxLayout(group_container)
        group_layout.setContentsMargins(int(12 * self.dpi_scale), int(12 * self.dpi_scale), int(12 * self.dpi_scale), int(12 * self.dpi_scale))
        group_layout.setSpacing(int(8 * self.dpi_scale))

        # 遍历 feature，根据类型创建对应的配置项
        for feature_name, feature_type in feature.items():
            if feature_name not in config:
                continue

            feature_config = config[feature_name]
            feature_type = feature_type.strip().lower()

            # 存储配置数据
            self.feature_config_map[feature_name] = feature_config

            # 根据 feature 类型创建配置项
            if feature_type == "bool":
                # switch 功能：开关类型
                self._create_switch_items(group_layout, feature_name, feature_config, saved_config)
            elif feature_type == "toggle":
                # status 功能：下拉菜单类型
                self._create_status_items(group_layout, feature_name, feature_config, saved_config)

        self.config_layout.addWidget(group_container)

    def _create_category_items_ui(self, category, feature, config):
        """创建配置项 UI（带分类）"""
        # 加载已保存的配置
        saved_config = self._load_saved_config()

        category_list = category.get("list", [])
        category_data = category.get("data", {})

        # 遍历分类列表
        for category_id in category_list:
            if category_id not in category_data:
                continue

            cat_info = category_data[category_id]
            # 使用自定义本地化键获取分类名称和描述
            cat_name = self.translate(f"category.{category_id}.name", default=cat_info.get("name", category_id))
            cat_description = self.translate(f"category.{category_id}.description", default=cat_info.get("description", ""))
            cat_features = cat_info.get("list", [])

            # 创建可展开的分类卡片
            category_container = self._create_expandable_category(
                category_id, cat_name, cat_description
            )

            # 获取分类的内容区域布局（使用下划线代替连字符）
            safe_category_id = category_id.replace('-', '_')
            content_layout = getattr(self, f"category_{safe_category_id}_content_layout", None)
            if content_layout is None:
                self.config_layout.addWidget(category_container)
                continue

            # 遍历该分类下的所有 feature
            for feature_name in cat_features:
                if feature_name not in feature or feature_name not in config:
                    continue

                feature_config = config[feature_name]
                feature_type = feature.get(feature_name, "").strip().lower()

                # 存储配置数据
                self.feature_config_map[feature_name] = feature_config

                # 根据 feature 类型创建配置项
                if feature_type == "bool":
                    # switch 功能：开关类型
                    self._create_switch_items(content_layout, feature_name, feature_config, saved_config)
                elif feature_type == "toggle":
                    # status 功能：下拉菜单类型
                    self._create_status_items(content_layout, feature_name, feature_config, saved_config)

            self.config_layout.addWidget(category_container)

    def _create_expandable_category(self, category_id, title, description):
        """创建可展开的分类卡片（参考设置页面样式）"""
        container = QWidget()
        container.setStyleSheet(f"background: rgba(255, 255, 255, 0.08); border-radius: {int(8 * self.dpi_scale)}px;")
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建分类头部按钮
        from widgets import CardButton
        header = CardButton()
        header.setFixedHeight(int(56 * self.dpi_scale))
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        border_radius = int(8 * self.dpi_scale)
        header.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"border-top-left-radius:{border_radius}px;border-top-right-radius:{border_radius}px;}}"
            f"QPushButton:hover{{background:rgba(255,255,255,0.05);}}"
            f"QPushButton:pressed{{background:rgba(255,255,255,0.02);}}"
        )

        # 点击事件处理 - 使用闭包捕获 category_id
        def make_toggle_handler(cid):
            return lambda: self._toggle_category(cid)
        header.clicked.connect(make_toggle_handler(category_id))

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(
            int(15 * self.dpi_scale), int(10 * self.dpi_scale),
            int(15 * self.dpi_scale), int(10 * self.dpi_scale)
        )
        header_layout.setSpacing(int(12 * self.dpi_scale))

        # 标题和描述布局
        text_layout = QVBoxLayout()
        text_layout.setSpacing(int(2 * self.dpi_scale))
        text_layout.setContentsMargins(0, 0, 0, 0)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(
            f"color:white;font-size:{int(14 * self.dpi_scale)}px;"
            f"font-family:'Microsoft YaHei UI';background:transparent;"
        )
        title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(title_lbl)

        desc_lbl = QLabel(description)
        desc_lbl.setStyleSheet(
            f"color:rgba(255,255,255,0.6);font-size:{int(12 * self.dpi_scale)}px;"
            f"font-family:'Microsoft YaHei UI';background:transparent;"
        )
        desc_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        text_layout.addWidget(desc_lbl)

        header_layout.addLayout(text_layout)
        header_layout.addStretch()

        main_layout.addWidget(header)

        # 内容区域容器
        content_container = QWidget()
        content_container.setStyleSheet("background:transparent;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(
            int(15 * self.dpi_scale), int(12 * self.dpi_scale),
            int(15 * self.dpi_scale), int(12 * self.dpi_scale)
        )
        content_layout.setSpacing(int(8 * self.dpi_scale))
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        content_container.setVisible(False)  # 默认收起

        main_layout.addWidget(content_container)

        # 保存引用（使用下划线代替连字符，避免属性名问题）
        safe_id = category_id.replace('-', '_')
        setattr(self, f"category_{safe_id}_content_layout", content_layout)
        setattr(self, f"category_{safe_id}_header", header)
        setattr(self, f"category_{safe_id}_content_widget", content_container)
        setattr(self, f"category_{safe_id}_visible", False)

        return container

    def _toggle_category(self, category_id):
        """切换分类展开/收起状态"""
        safe_category_id = category_id.replace('-', '_')
        content_widget = getattr(self, f"category_{safe_category_id}_content_widget", None)

        if content_widget:
            current_visible = getattr(self, f"category_{safe_category_id}_visible", True)
            new_visible = not current_visible
            content_widget.setVisible(new_visible)
            setattr(self, f"category_{safe_category_id}_visible", new_visible)

    def _load_saved_config(self):
        """加载已保存的配置"""
        config_file_path = os.path.join(self.full_path, "packset_config.json")
        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
        return {}

    def _create_switch_items(self, layout, feature_name, feature_config, saved_config=None):
        """创建开关类型的配置项"""
        # 使用自定义本地化键获取功能名称
        display_name = self.translate(f"feature.{feature_name}", default=feature_name)
        item_label = QLabel(display_name)
        item_label.setStyleSheet(
            f"background: transparent;"
            f"color: rgba(255, 255, 255, 0.9);"
            f"font-size: {int(12 * self.dpi_scale)}px;"
            f"font-family: 'Microsoft YaHei UI';"
        )

        # 获取默认值或已保存的值
        if saved_config and feature_name in saved_config:
            # 使用已保存的值
            default_value = saved_config[feature_name]
            if isinstance(default_value, str):
                default_value = default_value.lower() == "true"
        else:
            # 使用配置文件中的默认值
            default_value = feature_config.get("default", "false").lower() == "true"

        # 创建切换开关
        toggle_switch = ToggleSwitch(checked=default_value, dpi_scale=self.dpi_scale)
        # 存储配置项部件，使用 feature_name 作为键
        self.config_widgets[f"{feature_name}_bool"] = toggle_switch

        # 添加到布局
        item_layout = QHBoxLayout()
        item_layout.setSpacing(int(10 * self.dpi_scale))
        item_layout.addWidget(item_label, 1)
        item_layout.addWidget(toggle_switch, 0, Qt.AlignmentFlag.AlignRight)
        layout.addLayout(item_layout)

    def _create_status_items(self, layout, feature_name, feature_config, saved_config=None):
        """创建状态切换类型的配置项"""
        # 使用自定义本地化键获取功能名称
        display_name = self.translate(f"feature.{feature_name}", default=feature_name)
        item_label = QLabel(display_name)
        item_label.setStyleSheet(
            f"background: transparent;"
            f"color: rgba(255, 255, 255, 0.9);"
            f"font-size: {int(12 * self.dpi_scale)}px;"
            f"font-family: 'Microsoft YaHei UI';"
        )

        # 获取选项列表
        scope = feature_config.get("scope", [])

        # 创建下拉菜单，参考下载界面的排序按钮样式
        combobox = QComboBox()
        combobox.setMinimumWidth(int(150 * self.dpi_scale))
        combobox.setFixedHeight(int(32 * self.dpi_scale))
        padding = int(6 * self.dpi_scale)
        border_radius = int(4 * self.dpi_scale)

        combobox.setStyleSheet(f"""
            QComboBox {{
                background: rgba(255, 255, 255, 0.1);
                border: none;
                border-radius: {border_radius}px;
                padding: {padding}px;
                color: rgba(255, 255, 255, 0.95);
                font-size: {int(12 * self.dpi_scale)}px;
                font-family: 'Microsoft YaHei UI';
            }}
            QComboBox:hover {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QComboBox:focus {{
                background: rgba(255, 255, 255, 0.15);
            }}
            QComboBox::drop-down {{
                border: none;
                width: {int(28 * self.dpi_scale)}px;
                background: transparent;
            }}
            QComboBox QAbstractItemView {{
                background: rgba(0, 0, 0, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {border_radius}px;
                selection-background-color: rgba(255, 255, 255, 0.3);
                selection-color: white;
                outline: none;
                padding: {int(2 * self.dpi_scale)}px;
            }}
            QComboBox QAbstractItemView::item {{
                height: {int(28 * self.dpi_scale)}px;
                padding: {int(6 * self.dpi_scale)}px {int(8 * self.dpi_scale)}px;
                color: rgba(255, 255, 255, 0.85);
                border-radius: {border_radius - 1}px;
                font-family: 'Microsoft YaHei UI';
            }}
            QComboBox QAbstractItemView::item:selected {{
                background: rgba(255, 255, 255, 0.3);
                color: white;
            }}
            QComboBox QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.05);
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QComboBox QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }}
        """)
        combobox.addItems(scope)
        # 设置默认选中项（优先使用已保存的值，否则使用第一个）
        default_index = 0
        if saved_config and feature_name in saved_config:
            saved_value = saved_config[feature_name]
            if saved_value in scope:
                default_index = scope.index(saved_value)
        if scope:
            combobox.setCurrentIndex(default_index)

        # 存储配置项部件，使用 feature_name 作为键
        self.config_widgets[f"{feature_name}_status"] = combobox

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
                font-family: 'Microsoft YaHei UI';
                padding: {int(16 * self.dpi_scale)}px;
                background: rgba(255, 100, 100, 0.1);
                border-radius: {int(4 * self.dpi_scale)}px;
                border: 1px solid rgba(255, 100, 100, 0.3);
            }}
        """)
        self.config_layout.addWidget(error_label)

    def _on_back_clicked(self):
        """返回按钮点击事件"""
        if self.on_back:
            self.on_back()

    def _on_save_clicked(self):
        """保存按钮点击事件"""
        try:
            self._save_config()
            # 3秒内显示"已应用"
            self.save_button_applied = True
            self.save_button.setText(self.text_renderer.translate("resourcepack_config_applied") if self.text_renderer else "已应用")
            self.save_button.setEnabled(False)

            from PyQt6.QtCore import QTimer
            QTimer.singleShot(3000, self._restore_save_button)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            import traceback
            traceback.print_exc()

    def _restore_save_button(self, original_text):
        """恢复保存按钮状态"""
        if hasattr(self, 'save_button') and self.save_button:
            self.save_button_applied = False
            self._update_save_button_text()
            self.save_button.setEnabled(True)

    def _update_save_button_text(self):
        """更新保存按钮的文本（根据当前状态和语言）"""
        if self.save_button_applied:
            text = self.text_renderer.translate("resourcepack_config_applied") if self.text_renderer else "已应用"
        else:
            text = self.text_renderer.translate("resourcepack_config_save") if self.text_renderer else "保存并应用"
        self.save_button.setText(text)

    def update_language(self):
        """更新页面语言"""
        if self.text_renderer:
            self.text_renderer.update_group_language("resourcepack_config")
            # 手动更新保存按钮文本
            self._update_save_button_text()

    def _save_config(self):
        """保存配置到 packset_config.json"""
        # 读取当前配置
        config_data = {}
        config_file_path = os.path.join(self.full_path, "packset_config.json")

        if os.path.exists(config_file_path):
            try:
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.error(f"读取配置文件失败: {e}")
                config_data = {}

        # 遍历所有配置项并更新
        for feature_name, feature_config in self.feature_config_map.items():
            feature_type = self.packset_data.get("feature", {}).get(feature_name, "")

            if feature_type == "bool":
                # 处理 bool 类型的配置
                widget = self.config_widgets.get(f"{feature_name}_bool")
                if widget:
                    is_enabled = widget.checked
                    # 获取父开关的默认值
                    switch_feature_default = feature_config.get("default", "false").lower() == "true"
                    toggle_list = feature_config.get("toggle", [])
                    self._process_bool_config(toggle_list, is_enabled, switch_feature_default)
                    config_data[feature_name] = is_enabled
            elif feature_type == "toggle":
                # 处理 toggle 类型的配置
                widget = self.config_widgets.get(f"{feature_name}_status")
                if widget:
                    selected_value = widget.currentText()
                    paths = feature_config.get("paths", [])
                    self._process_toggle_config(paths, selected_value)
                    config_data[feature_name] = selected_value

        # 保存配置到文件
        try:
            with open(config_file_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存到: {config_file_path.replace('\\', '/')}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")
            raise

    def _process_bool_config(self, toggle_list, is_enabled, switch_feature_default):
        """处理 bool 类型的配置

        Args:
            toggle_list: 配置项列表
            is_enabled: 父开关的当前状态
            switch_feature_default: 父开关的默认值
        """
        # 判断是否与默认值相同（显示默认状态）
        is_default = (is_enabled == switch_feature_default)

        # 如果是压缩包，使用压缩包辅助类
        if self.full_path.endswith('.zip'):
            with ZipResourcePackHelper(self.full_path) as zip_helper:
                zip_helper.extract_all()
                for item in toggle_list:
                    item_type = item.get("type", "")
                    file_path = item.get("file_path", "")
                    if not file_path:
                        continue

                    if item_type == "bool":
                        # 直接重命名文件
                        self._process_bool_file_zip(zip_helper, file_path, is_default)
                    elif item_type == "toggle":
                        # 处理子 packset.json 文件
                        self._process_sub_packset_zip(zip_helper, file_path, is_default, switch_feature_default)

                zip_helper.save()
            return

        # 文件夹形式的处理
        for item in toggle_list:
            item_type = item.get("type", "")
            file_path = item.get("file_path", "")

            if not file_path:
                continue

            if item_type == "bool":
                # 直接重命名文件
                self._process_bool_file(file_path, is_default)
            elif item_type == "toggle":
                # 处理子 packset.json 文件
                self._process_sub_packset(file_path, is_default, switch_feature_default)

    def _process_bool_file(self, file_path, is_enabled):
        """处理 bool 类型的文件：重命名文件

        Args:
            file_path: 文件路径
            is_enabled: True 表示启用（无后缀），False 表示禁用（添加 .packset.old）
        """
        full_file_path = os.path.join(self.full_path, file_path)
        old_file_path = full_file_path + ".packset.old"

        if is_enabled:
            # 启用：恢复原文件
            if os.path.exists(old_file_path):
                try:
                    if os.path.exists(full_file_path):
                        os.remove(full_file_path)
                    os.rename(old_file_path, full_file_path)
                    logger.info(f"恢复文件: {self._format_path(file_path)}")
                except Exception as e:
                    logger.error(f"恢复文件失败 {self._format_path(file_path)}: {e}")
        else:
            # 禁用：重命名文件为 .packset.old
            if os.path.exists(full_file_path):
                try:
                    os.rename(full_file_path, old_file_path)
                    logger.info(f"重命名文件: {self._format_path(file_path)} -> {self._format_path(file_path)}.packset.old")
                except Exception as e:
                    logger.error(f"重命名文件失败 {self._format_path(file_path)}: {e}")

    def _process_bool_file_zip(self, zip_helper, file_path, is_enabled):
        """处理 bool 类型的文件：重命名文件（压缩包版本）

        Args:
            zip_helper: 压缩包辅助类
            file_path: 文件路径
            is_enabled: True 表示启用（无后缀），False 表示禁用（添加 .packset.old）
        """
        old_file_path = file_path + ".packset.old"

        if is_enabled:
            # 启用：恢复原文件
            if zip_helper.file_exists(old_file_path):
                try:
                    if zip_helper.file_exists(file_path):
                        # 先删除当前文件
                        full_path = os.path.join(zip_helper.temp_dir, file_path)
                        os.remove(full_path)
                    zip_helper.rename_file(old_file_path, file_path)
                    logger.info(f"恢复文件: {file_path}")
                except Exception as e:
                    logger.error(f"恢复文件失败 {file_path}: {e}")
        else:
            # 禁用：重命名文件为 .packset.old
            if zip_helper.file_exists(file_path):
                try:
                    zip_helper.rename_file(file_path, old_file_path)
                    logger.info(f"重命名文件: {file_path} -> {file_path}.packset.old")
                except Exception as e:
                    logger.error(f"重命名文件失败 {file_path}: {e}")

    def _process_sub_packset(self, file_path, is_default, switch_feature_default):
        """处理子 packset.json 文件

        Args:
            file_path: 子 packset 文件路径
            is_default: 是否显示默认状态
            switch_feature_default: 父开关的默认值
        """
        full_file_path = os.path.join(self.full_path, file_path)

        if not os.path.exists(full_file_path):
            logger.warning(f"子 packset 文件不存在: {self._format_path(file_path)}")
            return

        try:
            with open(full_file_path, 'r', encoding='utf-8') as f:
                sub_packset_data = json.load(f)
        except Exception as e:
            logger.error(f"读取子 packset 文件失败 {self._format_path(file_path)}: {e}")
            return

        # 检查 schema_version
        if sub_packset_data.get("schema_version") != 1:
            logger.warning(f"子 packset schema_version 不支持: {self._format_path(file_path)}")
            return

        packset_type = sub_packset_data.get("type")
        if packset_type == "bool":
            # 处理 bool 类型的子 packset
            self._process_bool_subpackset(sub_packset_data, is_default, switch_feature_default)
        else:
            logger.warning(f"不支持的子 packset 类型: {packset_type}")

    def _process_sub_packset_zip(self, zip_helper, file_path, is_default, switch_feature_default):
        """处理子 packset.json 文件（压缩包版本）

        Args:
            zip_helper: 压缩包辅助类
            file_path: 子 packset 文件路径
            is_default: 是否显示默认状态
            switch_feature_default: 父开关的默认值
        """
        if not zip_helper.file_exists(file_path):
            logger.warning(f"子 packset 文件不存在: {file_path}")
            return

        try:
            sub_packset_data = zip_helper.read_json(file_path)
        except Exception as e:
            logger.error(f"读取子 packset 文件失败 {file_path}: {e}")
            return

        # 检查 schema_version
        if sub_packset_data.get("schema_version") != 1:
            logger.warning(f"子 packset schema_version 不支持: {file_path}")
            return

        packset_type = sub_packset_data.get("type")
        if packset_type == "bool":
            # 处理 bool 类型的子 packset
            self._process_bool_subpackset_zip(zip_helper, sub_packset_data, is_default, switch_feature_default)
        else:
            logger.warning(f"不支持的子 packset 类型: {packset_type}")

    def _process_bool_subpackset(self, packset_data, is_default, switch_feature_default):
        """处理 bool 类型的子 packset

        Args:
            packset_data: 子 packset 数据
            is_default: 是否显示默认状态
            switch_feature_default: 父开关的默认值
        """
        assets = packset_data.get("assets", [])
        toggles = packset_data.get("toggles", [])

        # 处理 assets 类型的项目
        for asset in assets:
            asset_file_path = asset.get("file_path", "")
            default_state = asset.get("default", "off")

            if not asset_file_path:
                continue

            # assets 类型：default="on" 时，is_default 为 True 则 on，False 则 off
            #           default="off" 时，is_default 为 True 则 off，False 则 on
            is_asset_on = (default_state == "on") == is_default
            self._process_bool_file(asset_file_path, is_asset_on)

        # 处理 toggles 类型的项目
        for toggle_item in toggles:
            toggle_name = toggle_item.get("name", "")
            path = toggle_item.get("path", "")
            toggle_path = toggle_item.get("toggle_path", "")

            if not path or not toggle_path:
                continue

            self._process_toggle_files(path, toggle_path, is_default)

    def _process_bool_subpackset_zip(self, zip_helper, packset_data, is_default, switch_feature_default):
        """处理 bool 类型的子 packset（压缩包版本）

        Args:
            zip_helper: 压缩包辅助类
            packset_data: 子 packset 数据
            is_default: 是否显示默认状态
            switch_feature_default: 父开关的默认值
        """
        assets = packset_data.get("assets", [])
        toggles = packset_data.get("toggles", [])

        # 处理 assets 类型的项目
        for asset in assets:
            asset_file_path = asset.get("file_path", "")
            default_state = asset.get("default", "off")

            if not asset_file_path:
                continue

            # assets 类型：default="on" 时，is_default 为 True 则 on，False 则 off
            #           default="off" 时，is_default 为 True 则 off，False 则 on
            is_asset_on = (default_state == "on") == is_default
            self._process_bool_file_zip(zip_helper, asset_file_path, is_asset_on)

        # 处理 toggles 类型的项目
        for toggle_item in toggles:
            toggle_name = toggle_item.get("name", "")
            path = toggle_item.get("path", "")
            toggle_path = toggle_item.get("toggle_path", "")

            if not path or not toggle_path:
                continue

            self._process_toggle_files_zip(zip_helper, path, toggle_path, is_default)

    def _process_toggle_files(self, default_path, toggle_path, is_on):
        """处理 toggles 类型：根据状态切换文件

        Args:
            default_path: 默认文件路径（path）
            toggle_path: 切换文件路径（toggle_path）
            is_on: True 表示显示默认状态，False 表示切换状态
        """
        if self.full_path.endswith('.zip'):
            logger.warning("压缩包形式的资源包暂不支持修改")
            return

        full_default_path = os.path.join(self.full_path, default_path)
        full_toggle_path = os.path.join(self.full_path, toggle_path)
        default_old_path = full_default_path + ".packset.old"

        # 检查当前状态：is_on=True 表示默认状态（无 .packset.old），False 表示切换状态
        is_currently_on = not os.path.exists(default_old_path)

        if is_on == is_currently_on:
            return

        if is_on:
            # 恢复默认状态
            if os.path.exists(full_default_path) and os.path.exists(default_old_path):
                try:
                    if os.path.exists(full_toggle_path):
                        os.remove(full_toggle_path)
                    os.rename(full_default_path, full_toggle_path)
                    logger.info(f"移动: {self._format_path(default_path)} -> {self._format_path(toggle_path)}")

                    os.rename(default_old_path, full_default_path)
                    logger.info(f"恢复: {self._format_path(default_path)}")
                except Exception as e:
                    logger.error(f"恢复默认状态失败 {self._format_path(default_path)}: {e}")
        else:
            # 切换状态：先重命名，再移动
            if os.path.exists(full_default_path):
                try:
                    os.rename(full_default_path, default_old_path)
                    logger.info(f"重命名: {self._format_path(default_path)} -> {self._format_path(default_path)}.packset.old")
                except Exception as e:
                    logger.error(f"重命名文件失败 {self._format_path(default_path)}: {e}")
                    return

            if os.path.exists(full_toggle_path):
                try:
                    if os.path.exists(full_default_path):
                        os.remove(full_default_path)
                    os.rename(full_toggle_path, full_default_path)
                    logger.info(f"移动: {self._format_path(toggle_path)} -> {self._format_path(default_path)}")
                except Exception as e:
                    logger.error(f"移动文件失败 {self._format_path(toggle_path)} -> {self._format_path(default_path)}: {e}")

    def _process_toggle_files_zip(self, zip_helper, default_path, toggle_path, is_on):
        """处理 toggles 类型：根据状态切换文件（压缩包版本）

        Args:
            zip_helper: 压缩包辅助类
            default_path: 默认文件路径（path）
            toggle_path: 切换文件路径（toggle_path）
            is_on: True 表示显示默认状态，False 表示切换状态
        """
        default_old_path = default_path + ".packset.old"

        # 检查当前状态：is_on=True 表示默认状态（无 .packset.old），False 表示切换状态
        is_currently_on = not zip_helper.file_exists(default_old_path)

        if is_on == is_currently_on:
            return

        if is_on:
            # 恢复默认状态
            if zip_helper.file_exists(default_path) and zip_helper.file_exists(default_old_path):
                try:
                    if zip_helper.file_exists(toggle_path):
                        # 删除 toggle_path 的旧文件
                        full_toggle_path = os.path.join(zip_helper.temp_dir, toggle_path)
                        os.remove(full_toggle_path)
                    zip_helper.rename_file(default_path, toggle_path)
                    logger.info(f"移动: {default_path} -> {toggle_path}")

                    zip_helper.rename_file(default_old_path, default_path)
                    logger.info(f"恢复: {default_path}")
                except Exception as e:
                    logger.error(f"恢复默认状态失败 {default_path}: {e}")
        else:
            # 切换状态：先重命名，再移动
            if zip_helper.file_exists(default_path):
                try:
                    zip_helper.rename_file(default_path, default_old_path)
                    logger.info(f"重命名: {default_path} -> {default_path}.packset.old")
                except Exception as e:
                    logger.error(f"重命名文件失败 {default_path}: {e}")
                    return

            if zip_helper.file_exists(toggle_path):
                try:
                    full_default_path = os.path.join(zip_helper.temp_dir, default_path)
                    if os.path.exists(full_default_path):
                        os.remove(full_default_path)
                    zip_helper.rename_file(toggle_path, default_path)
                    logger.info(f"移动: {toggle_path} -> {default_path}")
                except Exception as e:
                    logger.error(f"移动文件失败 {toggle_path} -> {default_path}: {e}")

    def _copy_file(self, src, dst):
        """复制文件"""
        try:
            import shutil
            shutil.copy2(src, dst)
        except Exception as e:
            logger.error(f"复制文件失败 {src} -> {dst}: {e}")
            raise

    def _process_toggle_config(self, paths, selected_value):
        """处理 toggle 类型的配置：根据选择值切换文件

        Args:
            paths: 路径配置列表
            selected_value: 当前选中的状态值
        """
        # 读取保存的配置以获取上一个状态
        saved_config = self._load_saved_config()

        # 处理每个 path 配置项
        for path_item in paths:
            file_path = path_item.get("file_path", "")
            if not file_path:
                continue

            # 构建完整路径
            if self.full_path.endswith('.zip'):
                logger.warning("压缩包形式的资源包暂不支持修改")
                continue

            # 读取子 packset.json 文件
            full_packset_path = os.path.join(self.full_path, file_path)

            if not os.path.exists(full_packset_path):
                logger.warning(f"子 packset 文件不存在: {file_path}")
                continue

            try:
                with open(full_packset_path, 'r', encoding='utf-8') as f:
                    sub_packset_data = json.load(f)
            except Exception as e:
                logger.error(f"读取子 packset 文件失败 {file_path}: {e}")
                continue

            # 检查 schema_version 和 type
            if sub_packset_data.get("schema_version") != 1:
                logger.warning(f"子 packset schema_version 不支持: {file_path}")
                continue

            if sub_packset_data.get("type") != "toggle":
                logger.warning(f"子 packset 类型不匹配: {file_path}")
                continue

            # 获取默认状态和状态列表
            states = sub_packset_data.get("states", [])
            if not states:
                logger.warning(f"子 packset 没有状态定义: {file_path}")
                continue

            # 获取父配置中的默认值
            feature_name = None
            for name, config in self.feature_config_map.items():
                if "paths" in config and file_path in [p.get("file_path", "") for p in config.get("paths", [])]:
                    feature_name = name
                    break

            if not feature_name:
                logger.warning(f"无法找到对应的 feature_name: {file_path}")
                continue

            feature_config = self.feature_config_map.get(feature_name, {})
            default_state = feature_config.get("default", "")
            scope = feature_config.get("scope", [])

            # 获取上一个状态
            previous_state = saved_config.get(feature_name, default_state)

            # 获取当前选中状态、上一个状态和默认状态的索引
            current_index = 0
            previous_index = 0
            default_index = 0
            for i, state in enumerate(states):
                if state.get("name") == selected_value:
                    current_index = i
                if state.get("name") == previous_state:
                    previous_index = i
                if state.get("name") == default_state:
                    default_index = i

            logger.info(f"切换: {self._format_path(file_path)} {previous_state} -> {selected_value}")

            # 执行状态切换
            self._process_toggle_states(states, current_index, previous_index, default_index)

    def _process_toggle_states(self, states, current_index, previous_index, default_index):
        """处理状态切换

        Args:
            states: 状态列表
            current_index: 当前状态索引
            previous_index: 上一个状态索引
            default_index: 默认状态索引
        """
        # 获取默认状态的文件路径
        default_state_file = states[default_index].get("file_path", "")
        full_default_path = os.path.join(self.full_path, default_state_file)
        default_old_path = full_default_path + ".packset.old"

        # 判断当前激活的状态
        # 如果默认状态的 .packset.old 不存在，说明默认状态被激活
        # 如果默认状态的 .packset.old 存在，说明其他状态被激活
        is_default_active = not os.path.exists(default_old_path)

        if current_index == default_index:
            # 切换到默认状态
            if is_default_active:
                return
            # 恢复默认状态
            self._restore_default_state(states, previous_index, default_index, full_default_path, default_old_path)
        else:
            # 切换到非默认状态
            target_state_file = states[current_index].get("file_path", "")
            full_target_path = os.path.join(self.full_path, target_state_file)

            # 检查是否已经是目标状态
            # 目标状态的文件应该在默认位置
            if os.path.exists(full_target_path) and not os.path.exists(full_default_path):
                # 检查目标状态的原始位置是否有 .packset.old
                target_old_path = full_target_path + ".packset.old"
                if not os.path.exists(target_old_path):
                    # 目标状态的文件在它的原始位置，说明还没有被移动过
                    # 需要执行切换
                    pass
                else:
                    # 目标状态已经有 .packset.old，说明已经被移动到默认位置了
                    return

            # 执行状态切换
            self._switch_to_state(states, current_index, previous_index, default_index, full_default_path, default_old_path)

    def _process_toggle_states_zip(self, zip_helper, states, current_index, previous_index, default_index):
        """处理状态切换（压缩包版本）

        Args:
            zip_helper: 压缩包辅助类
            states: 状态列表
            current_index: 当前状态索引
            previous_index: 上一个状态索引
            default_index: 默认状态索引
        """
        # 获取默认状态的文件路径
        default_state_file = states[default_index].get("file_path", "")
        default_old_path = default_state_file + ".packset.old"

        # 判断当前激活的状态
        # 如果默认状态的 .packset.old 不存在，说明默认状态被激活
        # 如果默认状态的 .packset.old 存在，说明其他状态被激活
        is_default_active = not zip_helper.file_exists(default_old_path)

        if current_index == default_index:
            # 切换到默认状态
            if is_default_active:
                return
            # 恢复默认状态
            self._restore_default_state_zip(zip_helper, states, previous_index, default_index, default_state_file, default_old_path)
        else:
            # 切换到非默认状态
            target_state_file = states[current_index].get("file_path", "")

            # 检查是否已经是目标状态
            # 目标状态的文件应该在默认位置
            if zip_helper.file_exists(target_state_file) and not zip_helper.file_exists(default_state_file):
                # 检查目标状态的原始位置是否有 .packset.old
                target_old_path = target_state_file + ".packset.old"
                if not zip_helper.file_exists(target_old_path):
                    # 目标状态的文件在它的原始位置，说明还没有被移动过
                    # 需要执行切换
                    pass
                else:
                    # 目标状态已经有 .packset.old，说明已经被移动到默认位置了
                    return

            # 执行状态切换
            self._switch_to_state_zip(zip_helper, states, current_index, previous_index, default_index, default_state_file, default_old_path)

    def _restore_default_state(self, states, previous_index, default_index, full_default_path, default_old_path):
        """恢复到默认状态：先将当前激活的文件移回原位，再恢复默认状态的重命名"""
        # 1. 如果默认位置有文件且默认文件被重命名了，说明需要先移回当前激活的文件
        if os.path.exists(full_default_path) and os.path.exists(default_old_path):
            # 将默认位置的文件移回上一个状态的原始位置
            previous_state_file = states[previous_index].get("file_path", "")
            full_previous_path = os.path.join(self.full_path, previous_state_file)

            try:
                os.rename(full_default_path, full_previous_path)
                logger.info(f"移回: {self._format_path(previous_state_file)}")
            except Exception as e:
                logger.error(f"移回原位失败: {e}")
                return

        # 2. 再恢复默认状态的重命名
        if os.path.exists(default_old_path):
            try:
                os.rename(default_old_path, full_default_path)
                logger.info(f"恢复: {self._format_path(states[default_index].get('file_path', ''))}")
            except Exception as e:
                logger.error(f"恢复默认文件失败: {e}")

    def _switch_to_state(self, states, current_index, previous_index, default_index, full_default_path, default_old_path):
        """切换到指定状态"""
        target_state_file = states[current_index].get("file_path", "")
        full_target_path = os.path.join(self.full_path, target_state_file)

        # 步骤1：重命名默认状态文件（如果还没有重命名）
        if os.path.exists(full_default_path) and not os.path.exists(default_old_path):
            try:
                os.rename(full_default_path, default_old_path)
                logger.info(f"重命名: {self._format_path(states[default_index].get('file_path', ''))}")
            except Exception as e:
                logger.error(f"重命名默认文件失败: {e}")
                return

        # 步骤2：如果上一个状态不是默认状态，先将默认位置的文件移回上一个状态
        if previous_index != default_index and os.path.exists(full_default_path):
            previous_state_file = states[previous_index].get("file_path", "")
            full_previous_path = os.path.join(self.full_path, previous_state_file)

            try:
                os.rename(full_default_path, full_previous_path)
                logger.info(f"移回: {self._format_path(previous_state_file)}")
            except Exception as e:
                logger.error(f"移回原位失败: {e}")
                return

        # 步骤3：移动目标状态文件到默认位置
        if os.path.exists(full_target_path):
            try:
                os.rename(full_target_path, full_default_path)
                logger.info(f"移动: {self._format_path(target_state_file)} -> {self._format_path(states[default_index].get('file_path', ''))}")
            except Exception as e:
                logger.error(f"移动文件失败: {e}")

    def _restore_default_state_zip(self, zip_helper, states, previous_index, default_index, default_state_file, default_old_path):
        """恢复到默认状态（压缩包版本）：先将当前激活的文件移回原位，再恢复默认状态的重命名"""
        # 1. 如果默认位置有文件且默认文件被重命名了，说明需要先移回当前激活的文件
        if zip_helper.file_exists(default_state_file) and zip_helper.file_exists(default_old_path):
            # 将默认位置的文件移回上一个状态的原始位置
            previous_state_file = states[previous_index].get("file_path", "")

            try:
                zip_helper.rename_file(default_state_file, previous_state_file)
                logger.info(f"移回: {previous_state_file}")
            except Exception as e:
                logger.error(f"移回原位失败: {e}")
                return

        # 2. 再恢复默认状态的重命名
        if zip_helper.file_exists(default_old_path):
            try:
                zip_helper.rename_file(default_old_path, default_state_file)
                logger.info(f"恢复: {states[default_index].get('file_path', '')}")
            except Exception as e:
                logger.error(f"恢复默认文件失败: {e}")

    def _switch_to_state_zip(self, zip_helper, states, current_index, previous_index, default_index, default_state_file, default_old_path):
        """切换到指定状态（压缩包版本）"""
        target_state_file = states[current_index].get("file_path", "")

        # 步骤1：重命名默认状态文件（如果还没有重命名）
        if zip_helper.file_exists(default_state_file) and not zip_helper.file_exists(default_old_path):
            try:
                zip_helper.rename_file(default_state_file, default_old_path)
                logger.info(f"重命名: {states[default_index].get('file_path', '')}")
            except Exception as e:
                logger.error(f"重命名默认文件失败: {e}")
                return

        # 步骤2：如果上一个状态不是默认状态，先将默认位置的文件移回上一个状态
        if previous_index != default_index and zip_helper.file_exists(default_state_file):
            previous_state_file = states[previous_index].get("file_path", "")

            try:
                zip_helper.rename_file(default_state_file, previous_state_file)
                logger.info(f"移回: {previous_state_file}")
            except Exception as e:
                logger.error(f"移回原位失败: {e}")
                return

        # 步骤3：移动目标状态文件到默认位置
        if zip_helper.file_exists(target_state_file):
            try:
                zip_helper.rename_file(target_state_file, default_state_file)
                logger.info(f"移动: {target_state_file} -> {states[default_index].get('file_path', '')}")
            except Exception as e:
                logger.error(f"移动文件失败: {e}")
