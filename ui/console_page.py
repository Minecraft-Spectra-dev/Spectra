"""控制台页面模块

提供控制台/日志页面的创建功能
"""

import logging
from PyQt6.QtWidgets import QTextEdit, QLineEdit, QWidget, QVBoxLayout

logger = logging.getLogger(__name__)


class ConsolePageBuilder:
    """控制台页面构建器"""

    def __init__(self, builder):
        self.builder = builder

    def create_console_page(self):
        """创建控制台/日志页面"""
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        console_layout.setContentsMargins(
            self.builder._scale_size(20), self.builder._scale_size(10),
            self.builder._scale_size(20), self.builder._scale_size(20)
        )
        console_layout.setSpacing(self.builder._scale_size(15))

        title = self.builder._create_page_title("page_console")
        self.builder.text_renderer.register_widget(title, "page_console", group="console_page")
        console_layout.addWidget(title)

        # 计算背景透明度（主页透明度 + 20）
        blur_opacity = self.builder.window.config.get("blur_opacity", 150)
        bg_opacity = min(255, blur_opacity + 20)

        # 背景容器
        bg_container = QWidget()
        bg_container.setStyleSheet(f"""
            QWidget {{
                background: rgba(0, 0, 0, {bg_opacity});
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: {self.builder._scale_size(8)}px;
            }}
        """)
        bg_layout = QVBoxLayout(bg_container)
        bg_layout.setContentsMargins(
            self.builder._scale_size(10), self.builder._scale_size(10),
            self.builder._scale_size(10), self.builder._scale_size(10)
        )
        bg_layout.setSpacing(self.builder._scale_size(10))

        # 创建日志文本框
        self.builder.window.console_text = QTextEdit()
        self.builder.window.console_text.setReadOnly(True)
        self.builder.window.console_text.setStyleSheet(f"""
            QTextEdit {{
                background: transparent;
                border: none;
                color: rgba(255, 255, 255, 0.9);
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: {self.builder._scale_size(12)}px;
                padding: 0px;
            }}
            QScrollBar:vertical {{
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
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
            QScrollBar:horizontal {{
                background: rgba(255, 255, 255, 0.1);
                height: 8px;
                border-radius: 4px;
                margin: 0px;
            }}
            QScrollBar::handle:horizontal {{
                background: rgba(255, 255, 255, 0.3);
                min-width: 20px;
                border-radius: 4px;
            }}
            QScrollBar::handle:horizontal:hover {{
                background: rgba(255, 255, 255, 0.5);
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                border: none;
                background: none;
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        bg_layout.addWidget(self.builder.window.console_text, 1)

        # 输入框
        self.builder.window.console_input = QLineEdit()
        self.builder.window.console_input.setStyleSheet(self.builder._get_lineedit_stylesheet())
        self.builder.text_renderer.register_widget(
            self.builder.window.console_input,
            "console_input_placeholder",
            update_method="setPlaceholderText",
            group="console_page"
        )

        # 监听回车键
        def handle_command():
            command = self.builder.window.console_input.text().strip()
            self.builder.window.console_input.clear()
            self._handle_command(command)

        self.builder.window.console_input.returnPressed.connect(handle_command)
        bg_layout.addWidget(self.builder.window.console_input)
        console_layout.addWidget(bg_container, 1)

        # 加载日志
        self.builder.window._load_console_logs()
        return console_widget

    def _handle_command(self, command):
        """处理控制台命令"""
        cmd_lower = command.lower()
        if cmd_lower == "restart":
            # 重启程序
            import sys
            import os
            self.builder.window.close()
            python = sys.executable
            os.execl(python, python, *sys.argv)
        elif cmd_lower in ["exit", "quit"]:
            # 退出程序
            from PyQt6.QtWidgets import QApplication
            QApplication.instance().quit()
        elif cmd_lower == "clear":
            # 清空日志显示
            self.builder.window.console_text.clear()
        elif cmd_lower == "reload":
            # 重新加载日志
            self.builder.window._load_console_logs()
        elif cmd_lower == "help":
            # 显示帮助信息
            help_text = """
Available commands:
  restart  - Restart the program
  exit     - Exit the program
  quit     - Exit the program (same as exit)
  clear    - Clear the console display
  reload   - Reload log files
  info     - Show program information
  help     - Show this help message
"""
            self.builder.window.console_text.append(help_text)
        elif cmd_lower == "info":
            # 显示程序信息
            import sys
            from managers import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.config
            info_text = f"""
Spectra Information:
  Python Version: {sys.version.split()[0]}
  Window Size: {self.builder.window.width()}x{self.builder.window.height()}
  DPI Scale: {self.builder.window.dpi_scale:.2f}
  Background Mode: {config.get('background_mode', 'blur')}
  Blur Opacity: {config.get('blur_opacity', 150)}
  Language: {config.get('language', 'en_US')}
"""
            self.builder.window.console_text.append(info_text)
        else:
            # 未知指令
            self.builder.window.console_text.append(f"Unknown command: {command}")
            self.builder.window.console_text.append("Type 'help' to see available commands.")

    def update_page_title(self):
        """更新控制台页面标题"""
        console_page = self.builder.window.stack.widget(3)
        if console_page and console_page.layout():
            title = console_page.layout().itemAt(0).widget()
            if title and hasattr(title, 'setText'):
                title.setText(self.builder.window.language_manager.translate("page_console"))

    def update_page_font(self, font_family):
        """更新控制台页面字体"""
        console_page = self.builder.window.stack.widget(3)
        if console_page and console_page.layout():
            title = console_page.layout().itemAt(0).widget()
            if title:
                escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
                font_family_quoted = f'"{escaped_font}"'
                title.setStyleSheet(
                    f"color:white;font-size:{self.builder._scale_size(20)}px;"
                    f"font-family:{font_family_quoted};font-weight:bold;"
                )
