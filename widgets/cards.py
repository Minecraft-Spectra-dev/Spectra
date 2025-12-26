"""自定义卡片组件"""

from PyQt6.QtCore import (QPropertyAnimation, QEasingCurve, QTimer, Qt)
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (QGraphicsOpacityEffect, QHBoxLayout, QLabel,
                             QPushButton, QVBoxLayout, QWidget)


# 全局字体变量
_current_font_family = "Microsoft YaHei UI"


def get_current_font():
    """获取当前字体系列"""
    global _current_font_family
    return _current_font_family


def set_current_font(font_family):
    """设置当前字体系列"""
    global _current_font_family
    _current_font_family = font_family


class NewsCard(QWidget):
    def __init__(self, title, content, on_close=None, dpi_scale=1.0, parent=None):
        super().__init__(parent)
        self.on_close = on_close
        self.dpi_scale = dpi_scale
        self._scale = 1.0
        self._opacity = 0.0
        
        self.setMouseTracking(True)
        
        # 卡片容器
        self.card_container = QWidget(self)
        self.card_container.setMouseTracking(True)
        self.card_container.setObjectName("card_container")
        self.card_layout = QVBoxLayout(self)
        self.card_layout.setContentsMargins(0, 0, 0, 0)
        self.card_layout.setSpacing(0)
        self.card_layout.addWidget(self.card_container)
        
        # 主内容布局
        layout = QVBoxLayout(self.card_container)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        # 顶部区域：标题和关闭按钮
        top_layout = QHBoxLayout()
        top_layout.setSpacing(12)
        
        # 标题标签
        self.title_label = QLabel(title)
        title_font = QFont()
        title_font.setFamily(get_current_font())
        title_font.setWeight(QFont.Weight.Bold)
        title_font.setPointSize(int(13 * dpi_scale))
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("""
            QLabel {
                color: white;
                background: transparent;
            }
        """)
        self.title_label.setWordWrap(True)
        top_layout.addWidget(self.title_label, 1)
        
        # 关闭按钮
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(int(24 * dpi_scale), int(24 * dpi_scale))
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: rgba(255, 255, 255, 0.15);
                border-radius: 12px;
            }
        """)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.clicked.connect(self.close)
        top_layout.addWidget(self.close_btn)
        
        layout.addLayout(top_layout)
        
        # 内容标签
        self.content_label = QLabel(content)
        content_font = QFont()
        content_font.setFamily(get_current_font())
        content_font.setPointSize(int(11 * dpi_scale))
        self.content_label.setFont(content_font)
        self.content_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.85);
                background: transparent;
            }
        """)
        self.content_label.setWordWrap(True)
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.content_label)
        
        # 卡片样式
        self._update_card_style()
        
        # 创建透明度效果
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(0.0)
        self.setGraphicsEffect(self.opacity_effect)
    
    def _update_card_style(self):
        self.card_container.setStyleSheet(f"""
            #card_container {{
                background: rgba(0, 0, 0, 0.45);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: {int(12 * self.dpi_scale)}px;
            }}
            #card_container:hover {{
                background: rgba(0, 0, 0, 0.55);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }}
        """)
    
    def set_content(self, title, content):
        self.title_label.setText(title)
        self.content_label.setText(content)

    def set_on_close(self, on_close):
        self.on_close = on_close

    def update_font(self, font_family):
        """更新卡片字体"""
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        # 使用双引号包裹字体名称，避免单引号问题
        font_family_quoted = f'"{escaped_font}"'

        # 使用样式表设置字体（优先级高于 setFont）
        title_font_size = int(13 * self.dpi_scale)
        content_font_size = int(11 * self.dpi_scale)

        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                background: transparent;
                font-family: {font_family_quoted};
                font-size: {title_font_size}px;
                font-weight: bold;
            }}
        """)

        self.content_label.setStyleSheet(f"""
            QLabel {{
                color: rgba(255, 255, 255, 0.85);
                background: transparent;
                font-family: {font_family_quoted};
                font-size: {content_font_size}px;
            }}
        """)

    def fade_in(self, duration=300):
        """淡入动画"""
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(duration)
        self.anim.setStartValue(0.0)
        self.anim.setEndValue(1.0)
        self.anim.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.anim.start()
    
    def fade_out(self, duration=200, callback=None):
        """淡出动画"""
        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setDuration(duration)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)
        self.anim.setEasingCurve(QEasingCurve.Type.InQuad)
        if callback:
            self.anim.finished.connect(lambda: QTimer.singleShot(0, callback))
        self.anim.start()
    
    def close(self):
        if self.on_close:
            self.fade_out(callback=self.on_close)
        else:
            self.deleteLater()
