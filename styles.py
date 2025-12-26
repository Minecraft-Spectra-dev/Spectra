"""样式定义"""

STYLE_BTN = "QPushButton{background:transparent;border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.2);}"
STYLE_BTN_ACTIVE = "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:8px;}QPushButton:hover{background:rgba(255,255,255,0.1);}"
STYLE_ICON = "color:white;background:transparent;font-size:16px;font-family:'Segoe Fluent Icons';"
STYLE_TEXT = "color:white;background:transparent;font-size:14px;font-family:'微软雅黑';"

SLIDER_STYLE = """
QSlider::groove:horizontal {
    height: 4px;
    background: rgba(255,255,255,0.2);
    border-radius: 2px;
}
QSlider::handle:horizontal {
    width: 16px;
    height: 16px;
    background: rgba(255,255,255,0.9);
    border-radius: 8px;
    margin: -6px 0;
}
QSlider::sub-page:horizontal {
    background: #ffffff;
    border-radius: 2px;
}
"""
