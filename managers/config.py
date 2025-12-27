"""配置管理器"""

import json
import os
import logging
import sys

from utils import get_resource_path

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file="config.json"):
        # 获取配置文件的绝对路径
        # config.json 始终从当前工作目录读取，不从 _MEIPASS 读取
        if hasattr(sys, '_MEIPASS'):
            # 打包后环境，使用当前工作目录
            self.config_file = os.path.join(os.getcwd(), config_file)
        else:
            # 开发环境
            self.config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', config_file)
            self.config_file = os.path.abspath(self.config_file)
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                logger.info(f"配置文件加载成功: {self.config_file}")
                return {
                    "background_mode": config.get("background_mode", "solid"),
                    "background_image_path": config.get("background_image_path", ""),
                    "background_color": config.get("background_color", "#000000"),
                    "window_width": config.get("window_width", 900),
                    "window_height": config.get("window_height", 600),
                    "blur_opacity": config.get("blur_opacity", 80),
                    "background_blur_enabled": config.get("background_blur_enabled", True),
                    "font_mode": config.get("font_mode", 0),
                    "custom_font_family": config.get("custom_font_family", "Microsoft YaHei UI"),
                    "custom_font_path": config.get("custom_font_path", ""),
                    "language": config.get("language", "zh_CN"),
                    "minecraft_path": config.get("minecraft_path", ""),
                    "favorited_versions": config.get("favorited_versions", []),
                    "favorited_resourcepacks": config.get("favorited_resourcepacks", []),
                    "version_aliases": config.get("version_aliases", {}),
                    "version_isolation": config.get("version_isolation", True),
                    "dev_console_enabled": config.get("dev_console_enabled", False)
                }
        except:
            logger.warning(f"配置文件加载失败，使用默认配置: {self.config_file}")
            return {
                "background_mode": "solid",
                "background_image_path": "",
                "background_color": "#000000",
                "window_width": 900,
                "window_height": 600,
                "blur_opacity": 80,
                "background_blur_enabled": True,
                "font_mode": 0,
                "custom_font_family": "Microsoft YaHei UI",
                "custom_font_path": "",
                "language": "zh_CN",
                "minecraft_path": "",
                "favorited_versions": [],
                "favorited_resourcepacks": [],
                "version_aliases": {},
                "version_isolation": True,
                "dev_console_enabled": False
            }

    def save_config(self):
        """保存配置，保留所有现有配置"""
        try:
            # 读取现有配置
            existing_config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    existing_config = json.load(f)

            # 合并配置：self.config优先，但保留existing_config中的其他字段
            if existing_config is None:
                existing_config = {}
            existing_config.update(self.config)

            # 保存合并后的配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置保存成功: {self.config_file}")
        except:
            # 如果读取失败，使用原始保存方式
            logger.error(f"配置保存失败，使用原始保存方式: {self.config_file}")
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
