"""主窗口"""

import ctypes
import functools
import os
import sys

import json
from PyQt6.QtCore import (QEventLoop, QPoint, QPropertyAnimation,
                           QEasingCurve, QThread, QUrl, QRect, Qt, QTimer)
from PyQt6.QtGui import QColor, QCursor, QIcon
from PyQt6.QtNetwork import (QNetworkAccessManager, QNetworkReply,
                             QNetworkRequest)
from PyQt6.QtWidgets import (QApplication, QColorDialog, QFileDialog,
                             QHBoxLayout, QLabel, QStackedWidget, QVBoxLayout,
                             QWidget)
from BlurWindow.blurWindow import blur

from managers import BackgroundManager, ConfigManager, LanguageManager
from managers.log_manager import get_logger

logger = get_logger(__name__)

from styles import STYLE_BTN, STYLE_BTN_ACTIVE
from ui import UIBuilder
from utils import load_svg_icon, scale_icon_for_display
from widgets import NewsCard, make_transparent, set_current_font


class NewsFetchThread(QThread):
    """新闻获取线程"""
    
    def __init__(self, url):
        super().__init__()
        self.url = url
        self.news_data = None
        self.error = None
    
    def run(self):
        """使用 QNetworkAccessManager 进行异步网络请求"""
        self.manager = QNetworkAccessManager()
        self.manager.finished.connect(self._on_request_finished)
        request = QNetworkRequest(QUrl(self.url))
        self.reply = self.manager.get(request)
        
        # 创建事件循环等待请求完成
        self.loop = QEventLoop()
        self.exec()
    
    def _on_request_finished(self, reply):
        """请求完成回调"""
        try:
            if reply.error() == QNetworkReply.NetworkError.NoError:
                data = reply.readAll().data().decode('utf-8')
                self.news_data = json.loads(data)
            else:
                self.error = f"网络错误: {reply.errorString()}"
        except Exception as e:
            self.error = str(e)
        finally:
            reply.deleteLater()
            self.quit()


class Window(QWidget):
    EDGE = 8  # 基础边缘宽度，会在 __init__ 中根据 DPI 缩放

    def __init__(self):
        super().__init__()
        logger.info("正在初始化主窗口...")
        self.config_manager = ConfigManager()
        self.config = self.config_manager.config
        self.bg_manager = BackgroundManager(self)
        self.language_manager = LanguageManager(self.config_manager)

        self.dpi_scale = self._get_system_dpi_scale()
        logger.info(f"系统DPI缩放比例: {self.dpi_scale:.2f}")

        self.ui_builder = UIBuilder(self)
        self.edge_size = self.ui_builder._scale_size(8)

        self.setWindowTitle(self.language_manager.translate("app_title"))
        if os.path.exists("icon.png"):
            self.setWindowIcon(QIcon("icon.png"))

        self.resize(self.config.get("window_width", 900), self.config.get("window_height", 600))
        self.setMinimumSize(self.ui_builder._scale_size(400), self.ui_builder._scale_size(300))
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setMouseTracking(True)

        self._init_ui()
        self._init_nav()
        self._init_content()
        self._apply_dpi_scaling()

        self.drag_pos = None
        self.resize_edge = None
        self.current_bg_path = None
        self.switch_page(0)
        logger.info("主窗口初始化完成")

        # 应用初始字体设置（在所有 UI 初始化完成后立即应用）
        self.apply_font()

        self.cursor_timer = QTimer()
        def update_cursor_safe():
            try:
                self.update_cursor(QCursor.pos())
            except:
                pass
        self.cursor_timer.timeout.connect(update_cursor_safe)
        self.cursor_timer.start(50)

        # 根据配置加载背景
        background_mode = self.config.get("background_mode", "image")
        if background_mode == "solid":
            color = self.config.get("background_color", "#00000000")
            self.bg_manager.set_solid_color(color)
        elif background_mode == "image" and self.config.get("background_image_path"):
            if os.path.exists(self.config.get("background_image_path")):
                self.set_background_image(self.config.get("background_image_path"))

    def _get_system_dpi_scale(self):
        if sys.platform == 'win32':
            try:
                import ctypes
                user32 = ctypes.windll.user32
                shcore = ctypes.windll.shcore

                try:
                    shcore.SetProcessDpiAwarenessContext(-2)
                except:
                    try:
                        shcore.SetProcessDpiAwareness(2)
                    except:
                        pass

                try:
                    get_dpi_for_system = user32.GetDpiForSystem
                    get_dpi_for_system.argtypes = []
                    get_dpi_for_system.restype = ctypes.c_uint
                    system_dpi = get_dpi_for_system()
                    return system_dpi / 96.0
                except Exception as e:
                    pass

                try:
                    hdc = user32.GetDC(0)
                    if hdc:
                        try:
                            dpi = user32.GetDeviceCaps(hdc, 88)
                            return dpi / 96.0
                        finally:
                            user32.ReleaseDC(0, hdc)
                except Exception as e:
                    pass

            except Exception as e:
                pass

        try:
            screen = QApplication.primaryScreen()
            if screen:
                logical_dpi = screen.logicalDotsPerInch().x()
                return logical_dpi / 96.0
        except Exception as e:
            pass

        return 1.0

    def _apply_dpi_scaling(self):
        if hasattr(self, 'sidebar'):
            self.sidebar.setFixedWidth(self.ui_builder._scale_size(50))

        if hasattr(self, 'right_panel') and self.right_panel.layout() and self.right_panel.layout().itemAt(0):
            titlebar = self.right_panel.layout().itemAt(0).widget()
            titlebar.setFixedHeight(self.ui_builder._scale_size(40))

        for widget in self.findChildren(QLabel, "nav_icon"):
            widget.setFixedSize(self.ui_builder._scale_size(20), self.ui_builder._scale_size(20))

    def _init_ui(self):
        """初始化UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

    def _init_nav(self):
        """初始化导航栏"""
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(self.ui_builder._scale_size(50))
        opacity_value = self.config.get("blur_opacity", 150)
        self.sidebar.setStyleSheet(f"background:rgba(0,0,0,{opacity_value});")
        self.sidebar.setMouseTracking(True)
        self.sidebar_expanded = False
        self.nav_texts = []
        self.nav_indicators = []

        self.menu_icon_path = "svg/chevron-bar-right.svg"
        self.menu_icon_path_active = "svg/chevron-bar-left.svg"
        self.menu_icon_label = None

        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(self.ui_builder._scale_size(2), self.ui_builder._scale_size(10), self.ui_builder._scale_size(5), self.ui_builder._scale_size(10))
        sb.setSpacing(self.ui_builder._scale_size(5))

        from widgets import make_transparent
        title = make_transparent(QWidget())
        title.setFixedHeight(self.ui_builder._scale_size(30))
        tl = QHBoxLayout(title)
        tl.setContentsMargins(self.ui_builder._scale_size(42), 0, self.ui_builder._scale_size(5), 0)
        self.title_lbl = QLabel("Spectra")
        font_size = int(14 * self.dpi_scale)
        self.title_lbl.setStyleSheet(f"color:white;background:transparent;font-size:{font_size}px;font-family:'{self.ui_builder._get_font_family()}';")
        self.title_lbl.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.title_lbl.setMouseTracking(True)
        self.title_lbl.hide()
        tl.addWidget(self.title_lbl)
        sb.addWidget(title)
        menu_icon = load_svg_icon("svg/chevron-bar-right.svg", self.dpi_scale)
        menu_icon_active = load_svg_icon("svg/chevron-bar-left.svg", self.dpi_scale)
        menu_btn_container = self.ui_builder.create_nav_btn(
            menu_icon if menu_icon else "\uE700", self.language_manager.translate("nav_collapse"), self.toggle_sidebar,
            None, "svg/chevron-bar-right.svg", "svg/chevron-bar-left.svg"
        )
        self.menu_icon_label = menu_btn_container.findChild(QLabel, "nav_icon")
        sb.addWidget(menu_btn_container)

        home_icon = load_svg_icon("svg/grid-1x2.svg", self.dpi_scale)
        home_icon_active = load_svg_icon("svg/grid-1x2-fill.svg", self.dpi_scale)
        sb.addWidget(self.ui_builder.create_nav_btn(
            home_icon if home_icon else "\uE80F", self.language_manager.translate("nav_home"),
            lambda: self.switch_page(0), 0, "svg/grid-1x2.svg", "svg/grid-1x2-fill.svg"
        ))

        instance_icon = load_svg_icon("svg/box.svg")
        instance_icon_active = load_svg_icon("svg/box-fill.svg")
        sb.addWidget(self.ui_builder.create_nav_btn(
            instance_icon if instance_icon else "\uE7A8", self.language_manager.translate("nav_instances"),
            lambda: self.switch_page(1), 1, "svg/box.svg", "svg/box-fill.svg"
        ))

        download_icon = load_svg_icon("svg/arrow-down-circle.svg")
        download_icon_active = load_svg_icon("svg/arrow-down-circle-fill.svg")
        sb.addWidget(self.ui_builder.create_nav_btn(
            download_icon if download_icon else "\uE7A8", self.language_manager.translate("nav_downloads"),
            lambda: self.switch_page(2), 2, "svg/arrow-down-circle.svg", "svg/arrow-down-circle-fill.svg"
        ))

        sb.addStretch()

        settings_icon = load_svg_icon("svg/gear.svg", self.dpi_scale)
        settings_icon_active = load_svg_icon("svg/gear-fill.svg", self.dpi_scale)
        sb.addWidget(self.ui_builder.create_nav_btn(
            settings_icon if settings_icon else "\uE713", self.language_manager.translate("nav_settings"),
            lambda: self.switch_page(3), 3, "svg/gear.svg", "svg/gear-fill.svg"
        ))

        self.layout().addWidget(self.sidebar)

    def _init_content(self):
        """初始化右侧内容区"""
        self.right_panel = QWidget()
        opacity_value = self.config.get("blur_opacity", 150)
        self.right_panel.setStyleSheet(f"background:rgba(0,0,0,{opacity_value});")
        self.right_panel.setMouseTracking(True)
        rl = QVBoxLayout(self.right_panel)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        titlebar = QWidget()
        titlebar.setFixedHeight(self.ui_builder._scale_size(40))
        titlebar.setStyleSheet("background:transparent;")
        titlebar.setMouseTracking(True)
        tb = QHBoxLayout(titlebar)
        tb.setContentsMargins(0, 0, self.ui_builder._scale_size(8), 0)
        tb.addStretch()
        for t, s in [("−", self.showMinimized), ("×", self.close)]:
            tb.addWidget(self.ui_builder.create_title_btn(t, s))
        rl.addWidget(titlebar)
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background:transparent;")
        self.stack.addWidget(self._create_home_page())
        self.stack.addWidget(self.ui_builder.create_instance_page())
        self.stack.addWidget(self.ui_builder.create_download_page())
        self.stack.addWidget(self.ui_builder.create_config_page())
        rl.addWidget(self.stack, 1)

        self.layout().addWidget(self.right_panel, 1)
    
    def _create_home_page(self):
        """创建主页"""
        from PyQt6.QtWidgets import QScrollArea

        home_widget = QWidget()
        home_layout = QVBoxLayout(home_widget)
        home_layout.setContentsMargins(self.ui_builder._scale_size(20), 0, self.ui_builder._scale_size(20), self.ui_builder._scale_size(20))
        home_layout.setSpacing(self.ui_builder._scale_size(15))

        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(255, 255, 255, 0.1);
                width: 8px;
                border-radius: 4px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.3);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(255, 255, 255, 0.5);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # 滚动内容区域
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, self.ui_builder._scale_size(10), 0, 0)
        scroll_layout.setSpacing(self.ui_builder._scale_size(15))
        scroll_layout.addStretch()

        scroll_area.setWidget(scroll_content)
        home_layout.addWidget(scroll_area, 1)

        # 存储新闻卡片的列表
        scroll_content.news_cards = []

        # 启动新闻获取线程
        news_url = "https://ipv4-beta.kxcym.top:5244/d/Spectra/Spectra.json?sign=YZ_QhT44uMDWJPROfBGIjI00Or2fxkzd0QOKzPQ1um8=:0"
        self.news_thread = NewsFetchThread(news_url)
        self.news_thread.finished.connect(lambda: self._on_news_loaded(scroll_layout, self.news_thread))
        self.news_thread.start()

        return home_widget
    
    def _on_news_loaded(self, layout, thread):
        """新闻加载完成回调"""
        if thread.error:
            # 网络错误，显示错误卡片
            error_card = NewsCard(
                title="网络不可用",
                content="无法连接到服务器获取新闻信息。请检查网络连接后重试。",
                dpi_scale=self.dpi_scale
            )
            error_card.set_on_close(functools.partial(self._close_news_card, layout, error_card))
            # 在 stretch 前插入错误卡片
            layout.insertWidget(layout.count() - 1, error_card)
            QTimer.singleShot(100, error_card.fade_in)
            layout.parent().news_cards.append(error_card)
        elif thread.news_data and "news" in thread.news_data:
            # 成功获取新闻数据
            news_list = thread.news_data["news"]
            if news_list:
                for i, news in enumerate(news_list):
                    news_card = NewsCard(
                        title=news.get("title", "无标题"),
                        content=news.get("text", "无内容"),
                        dpi_scale=self.dpi_scale
                    )
                    news_card.set_on_close(functools.partial(self._close_news_card, layout, news_card))
                    # 在 stretch 前插入卡片
                    layout.insertWidget(layout.count() - 1, news_card)
                    # 延迟淡入动画
                    QTimer.singleShot(100 + i * 100, news_card.fade_in)
                    layout.parent().news_cards.append(news_card)
            else:
                # 新闻列表为空
                empty_card = NewsCard(
                    title="暂无新闻",
                    content="当前没有可显示的新闻内容。",
                    dpi_scale=self.dpi_scale
                )
                empty_card.set_on_close(functools.partial(self._close_news_card, layout, empty_card))
                layout.insertWidget(layout.count() - 1, empty_card)
                QTimer.singleShot(100, empty_card.fade_in)
                layout.parent().news_cards.append(empty_card)
    
    def _close_news_card(self, layout, card):
        """关闭新闻卡片"""
        if card and not card.isVisible():
            return  # 如果卡片已经不可见，不需要重复处理
        
        # 获取要移除卡片的索引
        card_index = -1
        news_cards = getattr(layout.parent(), 'news_cards', [])
        for i, c in enumerate(news_cards):
            if c == card:
                card_index = i
                break
        
        # 计算需要移动的高度
        card_height = card.height() + int(15 * self.dpi_scale)  # 卡片高度 + 间距
        
        # 为剩余的卡片添加向上移动动画
        if card_index >= 0:
            for i in range(card_index, len(news_cards)):
                remaining_card = news_cards[i]
                current_pos = remaining_card.pos()
                target_pos = QPoint(current_pos.x(), current_pos.y() - card_height)
                
                # 创建位移动画
                pos_anim = QPropertyAnimation(remaining_card, b"pos")
                pos_anim.setDuration(200)
                pos_anim.setEasingCurve(QEasingCurve.Type.OutQuad)
                pos_anim.setStartValue(current_pos)
                pos_anim.setEndValue(target_pos)
                pos_anim.start()
        
        # 移除卡片
        layout.removeWidget(card)
        if card in news_cards:
            news_cards.remove(card)
        card.deleteLater()

    def showEvent(self, event):
        super().showEvent(event)
        blur(self.winId())
        ctypes.windll.dwmapi.DwmSetWindowAttribute(int(self.winId()), 33, ctypes.byref(ctypes.c_int(2)), 4)
        self.apply_opacity()

    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        for item in self.nav_indicators:
            if len(item) == 3:
                i, ind, btn = item
                icon_path, icon_path_active = None, None
                container = None
            else:
                i, ind, btn, icon_path, icon_path_active, container = item

            if i == index:
                ind.setStyleSheet(f"background:#a0a0ff;border-radius:{self.ui_builder._scale_size(1)}px;")
                btn.setStyleSheet(STYLE_BTN_ACTIVE)
                if icon_path_active and container:
                    icon_pixmap = load_svg_icon(icon_path_active, self.dpi_scale)
                    if icon_pixmap:
                        icon_lbl = container.findChild(QLabel, "nav_icon")
                        if icon_lbl:
                            icon_lbl.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))
            else:
                ind.setStyleSheet(f"background:transparent;border-radius:{self.ui_builder._scale_size(1)}px;")
                btn.setStyleSheet(STYLE_BTN)
                if icon_path and container:
                    icon_pixmap = load_svg_icon(icon_path, self.dpi_scale)
                    if icon_pixmap:
                        icon_lbl = container.findChild(QLabel, "nav_icon")
                        if icon_lbl:
                            icon_lbl.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))

    def toggle_sidebar(self):
        self.anim = QPropertyAnimation(self.sidebar, b"minimumWidth")
        self.anim2 = QPropertyAnimation(self.sidebar, b"maximumWidth")
        for a in (self.anim, self.anim2):
            a.setDuration(200)
            a.setEasingCurve(QEasingCurve.Type.InOutQuad)
            a.setStartValue(self.ui_builder._scale_size(140) if self.sidebar_expanded else self.ui_builder._scale_size(50))
            a.setEndValue(self.ui_builder._scale_size(50) if self.sidebar_expanded else self.ui_builder._scale_size(140))
        if self.sidebar_expanded:
            self.anim.finished.connect(lambda: [t.hide() for t in self.nav_texts])
            self.anim.finished.connect(lambda: self.title_lbl.hide())
            if self.menu_icon_label and self.menu_icon_path:
                icon_pixmap = load_svg_icon(self.menu_icon_path, self.dpi_scale)
                if icon_pixmap:
                    self.menu_icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))
        else:
            [t.show() for t in self.nav_texts]
            self.title_lbl.show()
            if self.menu_icon_label and self.menu_icon_path_active:
                icon_pixmap = load_svg_icon(self.menu_icon_path_active, self.dpi_scale)
                if icon_pixmap:
                    self.menu_icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))
        self.anim.start()
        self.anim2.start()
        self.sidebar_expanded = not self.sidebar_expanded

    def toggle_appearance_menu(self):
        """切换外观设置菜单"""
        content = self.appearance_container.layout().itemAt(1).widget()
        is_visible = content.isVisible()

        if is_visible:
            content.setVisible(False)
            if self.appearance_icon_label and self.appearance_icon_path:
                icon_pixmap = load_svg_icon(self.appearance_icon_path, self.dpi_scale)
                if icon_pixmap:
                    self.appearance_icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))
        else:
            content.setVisible(True)
            if self.appearance_icon_label and self.appearance_icon_path_active:
                icon_pixmap = load_svg_icon(self.appearance_icon_path_active, self.dpi_scale)
                if icon_pixmap:
                    self.appearance_icon_label.setPixmap(scale_icon_for_display(icon_pixmap, 20, self.dpi_scale))

    def toggle_language_menu(self):
        content = self.language_container.layout().itemAt(1).widget()
        is_visible = content.isVisible()

        if is_visible:
            content.setVisible(False)
        else:
            content.setVisible(True)
    
    def change_language(self, index):
        """切换语言"""
        languages = self.language_manager.get_all_languages()
        if 0 <= index < len(languages):
            lang_code = languages[index][0]
            self.language_manager.set_language(lang_code)
            self.update_ui_language()
    
    def update_ui_language(self):
        """更新界面语言"""
        # 更新窗口标题
        self.setWindowTitle(self.language_manager.translate("app_title"))
        
        # 更新导航栏文本
        nav_texts = [
            self.language_manager.translate("nav_collapse"),
            self.language_manager.translate("nav_home"),
            self.language_manager.translate("nav_instances"),
            self.language_manager.translate("nav_downloads"),
            self.language_manager.translate("nav_settings")
        ]
        
        for i, text_widget in enumerate(self.nav_texts):
            if i < len(nav_texts):
                text_widget.setText(nav_texts[i])
        
        # 更新页面标题
        self.ui_builder._update_page_titles()
        
        # 更新设置页面内容
        self.ui_builder._update_settings_page()

    def set_background(self, mode):
        self.config["background_mode"] = mode
        self.config_manager.save_config()

        # 样式表常量
        bg_card_selected = "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.05);}"
        bg_card_unselected = "QPushButton{background:rgba(255,255,255,0.05);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.03);}"

        def set_card_selected(card, selected):
            card.setStyleSheet(bg_card_selected if selected else bg_card_unselected)
            if selected:
                check_pixmap = load_svg_icon("svg/check-lg.svg", self.dpi_scale)
                if check_pixmap:
                    card.check_label.setPixmap(scale_icon_for_display(check_pixmap, 20, self.dpi_scale))
            else:
                card.check_label.clear()

        if mode == "blur":
            set_card_selected(self.blur_card, True)
            if hasattr(self, 'solid_card'):
                set_card_selected(self.solid_card, False)
                self.color_widget.setVisible(False)
            set_card_selected(self.image_card, False)
            self.path_widget.setVisible(False)
            self.opacity_widget.setVisible(True)
            self.apply_opacity()
            blur(self.winId())
            self.bg_manager.hide()

        elif mode == "solid":
            set_card_selected(self.blur_card, False)
            if hasattr(self, 'solid_card'):
                set_card_selected(self.solid_card, True)
            set_card_selected(self.image_card, False)
            if hasattr(self, 'solid_card'):
                self.path_widget.setVisible(False)
            self.opacity_widget.setVisible(False)
            self.color_widget.setVisible(True)
            color = self.config.get("background_color", "#00000000")
            self.bg_manager.set_solid_color(color)

        elif mode == "image":
            set_card_selected(self.blur_card, False)
            if hasattr(self, 'solid_card'):
                set_card_selected(self.solid_card, False)
                self.color_widget.setVisible(False)
            set_card_selected(self.image_card, True)
            if hasattr(self, 'solid_card'):
                self.path_widget.setVisible(True)
            self.opacity_widget.setVisible(False)
            if hasattr(self, 'solid_card'):
                self.color_widget.setVisible(False)
            if self.config.get("background_image_path") and os.path.exists(self.config.get("background_image_path")):
                self.set_background_image(self.config.get("background_image_path"))

    def set_background_image(self, path):
        self.bg_manager.set_background_image(path)
        self.current_bg_path = path

    def on_path_changed(self):
        path = self.path_input.text().strip()
        if path and os.path.exists(path):
            self.config["background_image_path"] = path
            self.config_manager.save_config()
            self.set_background_image(path)
        elif not path:
            self.config["background_image_path"] = ""
            self.config_manager.save_config()

    def on_opacity_changed(self, value):
        self.config["blur_opacity"] = value
        self.config_manager.save_config()
        opacity_percent = int((value - 10) / (255 - 10) * 100)
        self.opacity_value_label.setText(str(opacity_percent) + "%")
        self.apply_opacity()

    def apply_opacity(self):
        opacity_value = self.config.get("blur_opacity", 150)
        self.right_panel.setStyleSheet(f"background:rgba(0,0,0,{opacity_value});")
        self.sidebar.setStyleSheet(f"background:rgba(0,0,0,{opacity_value});")
        # 更新下拉框的透明度（主页透明度 + 20）
        # dropdown_opacity_value = min(255, opacity_value + 20)
        # dropdown_opacity_rgba = dropdown_opacity_value / 255.0
        # self.ui_builder.update_combobox_opacity(dropdown_opacity_rgba)

    def choose_background_image(self):
        """选择背景图像"""
        file, _ = QFileDialog.getOpenFileName(
            self, "选择背景", "",
            "媒体文件 (*.png *.jpg *.jpeg *.bmp *.mp4 *.avi *.mov *.mkv *.webm);;所有文件 (*.*)"
        )
        if file:
            self.config["background_image_path"] = file
            self.config_manager.save_config()
            self.path_input.setText(file)
            self.set_background_image(file)

    def choose_background_color(self):
        color_str = self.config.get("background_color", "#00000000")
        try:
            current_color = QColor(color_str)
            if not current_color.isValid():
                current_color = QColor(0, 0, 0, 0)
        except:
            current_color = QColor(0, 0, 0, 0)

        color = QColorDialog.getColor(
            current_color,
            self,
            "选择背景颜色",
            QColorDialog.ColorDialogOption.ShowAlphaChannel
        )

        if color.isValid():
            color_str = color.name(QColor.NameFormat.HexArgb)
            self.color_input.setText(color_str)
            self.on_color_changed()

    def on_color_changed(self):
        color_str = self.color_input.text().strip()
        try:
            color = QColor(color_str)
            if color.isValid():
                self.config["background_color"] = color_str
                self.config_manager.save_config()

                if hasattr(self, 'color_btn'):
                    self.color_btn.setStyleSheet(
                        f"QPushButton{{background:{color_str};border:1px solid rgba(255,255,255,0.3);border-radius:4px;}}QPushButton:hover{{background:{color_str};border:1px solid rgba(255,255,255,0.5);}}"
                    )

                if self.config.get("background_mode") == "solid":
                    self.bg_manager.set_solid_color(color_str)
        except:
            pass

    def get_edge(self, pos):
        x, y, w, h, e = pos.x(), pos.y(), self.width(), self.height(), self.edge_size
        edge = ""
        if y < e:
            edge += "t"
        elif y > h - e:
            edge += "b"
        if x < e:
            edge += "l"
        elif x > w - e:
            edge += "r"
        return edge

    def update_cursor(self, global_pos):
        local_pos = self.mapFromGlobal(global_pos)
        edge = self.get_edge(local_pos)
        cursors = {
            "t": Qt.CursorShape.SizeVerCursor,
            "b": Qt.CursorShape.SizeVerCursor,
            "l": Qt.CursorShape.SizeHorCursor,
            "r": Qt.CursorShape.SizeHorCursor,
            "tl": Qt.CursorShape.SizeFDiagCursor,
            "br": Qt.CursorShape.SizeFDiagCursor,
            "tr": Qt.CursorShape.SizeBDiagCursor,
            "bl": Qt.CursorShape.SizeBDiagCursor
        }
        self.setCursor(cursors.get(edge, Qt.CursorShape.ArrowCursor))

    def mousePressEvent(self, ev):
        if ev.button() == Qt.MouseButton.LeftButton:
            edge = self.get_edge(ev.position().toPoint())
            if edge:
                self.resize_edge = edge
                self.resize_start = ev.globalPosition().toPoint()
                self.resize_geo = self.geometry()
            elif ev.position().y() < 40 and ev.position().x() > self.sidebar.width():
                self.drag_pos = ev.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, ev):
        if self.resize_edge:
            diff = ev.globalPosition().toPoint() - self.resize_start
            geo = QRect(self.resize_geo)
            if 't' in self.resize_edge:
                geo.setTop(geo.top() + diff.y())
            if 'b' in self.resize_edge:
                geo.setBottom(geo.bottom() + diff.y())
            if 'l' in self.resize_edge:
                geo.setLeft(geo.left() + diff.x())
            if 'r' in self.resize_edge:
                geo.setRight(geo.right() + diff.x())
            if geo.width() >= self.minimumWidth() and geo.height() >= self.minimumHeight():
                self.setGeometry(geo)
        elif self.drag_pos:
            self.move(ev.globalPosition().toPoint() - self.drag_pos)
        else:
            self.update_cursor(ev.globalPosition().toPoint())

    def mouseReleaseEvent(self, ev):
        self.drag_pos = None
        self.resize_edge = None

    def resizeEvent(self, ev):
        super().resizeEvent(ev)
        if hasattr(self, 'current_bg_path') and self.current_bg_path:
            self.set_background_image(self.current_bg_path)

        if not hasattr(self, '_resize_timer'):
            self._resize_timer = QTimer()
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._save_window_size)

        self._resize_timer.start(300)

    def _save_window_size(self):
        self.config["window_width"] = self.width()
        self.config["window_height"] = self.height()
        self.config_manager.save_config()

    def toggle_font_menu(self):
        """切换字体设置菜单"""
        content = self.font_container.layout().itemAt(1).widget()
        is_visible = content.isVisible()

        if is_visible:
            content.setVisible(False)
        else:
            content.setVisible(True)

    def set_font_mode(self, mode):
        """设置字体模式: 0=选择字体, 1=自定义字体"""
        self.config["font_mode"] = mode
        self.config_manager.save_config()

        # 更新卡片选中状态
        self._update_font_card_selection(mode)

        # 显示/隐藏对应的控件
        self.font_select_widget.setVisible(mode == 0)
        self.font_path_widget.setVisible(mode == 1)

        # 应用字体
        self.apply_font()

    def _update_font_card_selection(self, mode):
        """更新字体卡片选中状态"""
        cards = [
            (self.font_select_card, 0),
            (self.font_custom_card, 1)
        ]

        for card, card_mode in cards:
            if card_mode == mode:
                card.setStyleSheet(
                    "QPushButton{background:rgba(255,255,255,0.15);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.05);}")
                check_pixmap = load_svg_icon("svg/check-lg.svg", self.dpi_scale)
                if check_pixmap:
                    card.check_label.setPixmap(scale_icon_for_display(check_pixmap, 20, self.dpi_scale))
            else:
                card.setStyleSheet(
                    "QPushButton{background:rgba(255,255,255,0.05);border:none;border-radius:0px;}QPushButton:hover{background:rgba(255,255,255,0.1);}QPushButton:pressed{background:rgba(255,255,255,0.03);}")
                card.check_label.clear()

    def on_font_family_changed(self, font_family):
        """字体选择变化"""
        self.config["custom_font_family"] = font_family
        self.config_manager.save_config()
        self.apply_font()

    def on_font_path_changed(self):
        """字体路径变化"""
        path = self.font_path_input.text().strip()
        if path and os.path.exists(path):
            self.config["custom_font_path"] = path
            self.config_manager.save_config()
            self.apply_font()
        elif not path:
            self.config["custom_font_path"] = ""
            self.config_manager.save_config()

    def choose_font_file(self):
        """选择字体文件"""
        file, _ = QFileDialog.getOpenFileName(
            self, self.language_manager.translate("font_custom_label"), "",
            "字体文件 (*.ttf *.otf *.ttc *.woff *.woff2);;所有文件 (*.*)"
        )
        if file:
            self.config["custom_font_path"] = file
            self.config_manager.save_config()
            self.font_path_input.setText(file)
            self.apply_font()

    def apply_font(self):
        """应用字体设置"""
        from PyQt6.QtGui import QFont, QFontDatabase
        font_mode = self.config.get("font_mode", 0)
        font_family = "Microsoft YaHei UI"
        font_path = self.config.get("custom_font_path", "")

        if font_mode == 0:
            # 选择字体
            font_family = self.config.get("custom_font_family", "Microsoft YaHei UI")
        elif font_mode == 1 and font_path and os.path.exists(font_path):
            # 自定义字体：从字体文件加载
            font_id = QFontDatabase.addApplicationFont(font_path)
            if font_id != -1:
                font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        # 应用到整个应用
        self._apply_font_to_app(font_family)

    def _apply_font_to_app(self, font_family):
        """应用字体到应用的所有控件"""
        from PyQt6.QtGui import QFont

        # 设置全局字体
        set_current_font(font_family)

        app = QApplication.instance()
        if app:
            font = QFont(font_family)
            app.setFont(font)

            # 强制更新所有控件以应用新字体
            # 注意：样式表中的字体设置优先级高于 setFont，所以需要手动更新
            self._update_all_fonts(font_family)

    def _update_all_fonts(self, font_family):
        """更新所有控件的字体样式"""
        # 转义字体名称中的特殊字符
        escaped_font = font_family.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"')
        # 使用双引号包裹字体名称，避免单引号问题
        font_family_quoted = f'"{escaped_font}"'

        # 更新窗口中的导航文本和标题
        for text_widget in self.nav_texts:
            font_size = int(14 * self.dpi_scale)
            text_widget.setStyleSheet(f"color:white;background:transparent;font-size:{font_size}px;font-family:{font_family_quoted};")

        # 更新标题标签
        if hasattr(self, 'title_lbl'):
            font_size = int(14 * self.dpi_scale)
            self.title_lbl.setStyleSheet(f"color:white;background:transparent;font-size:{font_size}px;font-family:{font_family_quoted};")

        # 更新所有新闻卡片的字体
        home_page = self.stack.widget(0)
        if home_page:
            # 获取主页的滚动区域（通过遍历布局查找）
            from PyQt6.QtWidgets import QScrollArea
            scroll_area = home_page.findChild(QScrollArea)
            if scroll_area:
                # 获取 scroll_content
                scroll_content = scroll_area.widget()
                if scroll_content and hasattr(scroll_content, 'news_cards'):
                    for card in scroll_content.news_cards:
                        card.update_font(font_family)

        # 更新实例页面文件浏览器的字体
        instance_page = self.stack.widget(1)
        if instance_page and hasattr(self, 'file_explorer'):
            self.file_explorer.update_font(font_family)

        # 触发 UI 更新以刷新设置页面的字体
        try:
            self.ui_builder._update_settings_font(font_family)
        except Exception as e:
            # 静默处理字体更新错误，避免崩溃
            pass


