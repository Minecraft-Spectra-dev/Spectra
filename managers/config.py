"""配置管理器"""

import json
import os


class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()

    def load_config(self):
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
                return {
                    "background_mode": config.get("background_mode", "blur"),
                    "background_image_path": config.get("background_image_path", ""),
                    "background_color": config.get("background_color", "#00000000"),
                    "window_width": config.get("window_width", 900),
                    "window_height": config.get("window_height", 600),
                    "blur_opacity": config.get("blur_opacity", 80),
                    "font_mode": config.get("font_mode", 0),
                    "custom_font_family": config.get("custom_font_family", "Microsoft YaHei UI"),
                    "custom_font_path": config.get("custom_font_path", ""),
                    "language": config.get("language", "zh_CN")
                }
        except:
            return {
                "background_mode": "blur",
                "background_image_path": "",
                "background_color": "#00000000",
                "window_width": 900,
                "window_height": 600,
                "blur_opacity": 80,
                "font_mode": 0,
                "custom_font_family": "Microsoft YaHei UI",
                "custom_font_path": "",
                "language": "zh_CN"
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
        except:
            # 如果读取失败，使用原始保存方式
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
