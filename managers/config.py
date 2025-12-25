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
                    "blur_opacity": config.get("blur_opacity", 80)
                }
        except:
            return {
                "background_mode": "blur",
                "background_image_path": "",
                "background_color": "#00000000",
                "window_width": 900,
                "window_height": 600,
                "blur_opacity": 80
            }

    def save_config(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save_config()
