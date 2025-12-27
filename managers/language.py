"""语言管理器"""

import json
import os
import locale
import logging
import sys

logger = logging.getLogger(__name__)


class LanguageManager:
    def __init__(self, config_manager=None, lang_dir="lang"):
        self.config_manager = config_manager
        # lang 目录优先从 _MEIPASS 读取（打包后），其次从当前工作目录读取
        if hasattr(sys, '_MEIPASS'):
            # 打包后环境，优先从 _internal 读取
            internal_lang = os.path.join(sys._MEIPASS, lang_dir)
            if os.path.exists(internal_lang):
                self.lang_dir = internal_lang
            else:
                self.lang_dir = os.path.join(os.getcwd(), lang_dir)
        else:
            # 开发环境
            self.lang_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', lang_dir)
            self.lang_dir = os.path.abspath(self.lang_dir)
        self.languages = self._load_languages()
        self.current_language = self._get_current_language()
        logger.info(f"语言管理器初始化完成，当前语言: {self.current_language}")

    def _get_system_language(self):
        """获取系统默认语言"""
        try:
            # 获取系统语言环境
            system_locale = locale.getdefaultlocale()[0]

            if system_locale:
                # 处理中文变体
                if system_locale.startswith('zh'):
                    # 繁体中文（台湾、香港、澳门）
                    if system_locale in ['zh_TW', 'zh_HK', 'zh_MO']:
                        return 'zh_CN'
                    # 简体中文（中国、新加坡）
                    elif system_locale in ['zh_CN', 'zh_SG']:
                        return 'zh_CN'
                    # 其他中文变体
                    else:
                        return 'zh_CN'
                # 其他语言
                else:
                    return 'en_US'
        except:
            pass

        return 'en_US'

    def _load_languages(self):
        """从lang目录加载所有语言文件"""
        languages = {}
        
        if not os.path.exists(self.lang_dir):
            logger.warning(f"语言目录不存在: {self.lang_dir}")
            return languages
        
        try:
            for filename in os.listdir(self.lang_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.lang_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            lang_data = json.load(f)
                            
                            # 验证语言文件格式
                            if 'metadata' in lang_data and 'translations' in lang_data:
                                metadata = lang_data['metadata']
                                lang_code = metadata.get('code', filename[:-5])
                                languages[lang_code] = {
                                    'name': metadata.get('name', lang_code),
                                    'code': lang_code,
                                    'author': metadata.get('author', 'Unknown'),
                                    'translations': lang_data['translations'],
                                    'filename': filename
                                }
                                logger.debug(f"加载语言文件: {filename} ({lang_code})")
                    except json.JSONDecodeError:
                        logger.error(f"语言文件格式错误: {filename}")
                        continue
        except Exception as e:
            logger.error(f"加载语言文件失败: {e}")
        
        logger.info(f"成功加载 {len(languages)} 种语言")
        return languages
    
    def _get_current_language(self):
        """获取当前语言"""
        saved_lang = None
        if self.config_manager:
            saved_lang = self.config_manager.get("language")

        # 如果保存的语言存在，使用它
        if saved_lang and saved_lang in self.languages:
            return saved_lang

        # 否则使用系统默认语言
        system_lang = self._get_system_language()
        if system_lang and system_lang in self.languages:
            return system_lang

        # 如果系统语言不存在，使用第一个可用的语言
        if self.languages:
            return list(self.languages.keys())[0]

        # 如果没有语言文件，使用默认语言
        return "zh_CN"

    def reload_languages(self):
        """重新加载语言文件（用于用户添加新语言后刷新）"""
        old_current = self.current_language
        self.languages = self._load_languages()

        # 如果当前语言不在新加载的语言列表中，切换到第一个可用语言
        if self.current_language not in self.languages:
            if self.languages:
                self.current_language = list(self.languages.keys())[0]
            else:
                self.current_language = "zh_CN"

        # 保存新语言设置
        self._save_language_config()

        return old_current != self.current_language

    def set_language(self, language_code):
        """设置当前语言"""
        if language_code in self.languages:
            self.current_language = language_code
            self._save_language_config()
            return True
        return False

    def _save_language_config(self):
        """保存语言配置"""
        if self.config_manager:
            self.config_manager.set("language", self.current_language)
    
    def get_language(self):
        """获取当前语言代码"""
        return self.current_language
    
    def get_display_name(self, language_code):
        """获取语言显示名称"""
        if language_code in self.languages:
            return self.languages[language_code]['name']
        return language_code
    
    def get_all_languages(self):
        """获取所有支持的语言列表 (language_code, display_name)"""
        return [(code, data['name']) for code, data in self.languages.items()]
    
    def get_language_info(self, language_code):
        """获取语言完整信息"""
        if language_code in self.languages:
            return self.languages[language_code]
        return None
    
    def translate(self, key, default=None):
        """获取翻译文本
        
        优先级：
        1. 当前语言中的翻译
        2. 英语(en_US)中的翻译（如果存在）
        3. 默认值
        4. 翻译键本身
        """
        if default is None:
            default = key
        
        # 首先尝试从当前语言获取翻译
        if self.current_language in self.languages:
            translations = self.languages[self.current_language]['translations']
            if key in translations:
                return translations[key]
        
        # 如果当前语言中没有找到，尝试从英语(en_US)获取翻译
        if 'en_US' in self.languages and self.current_language != 'en_US':
            translations = self.languages['en_US']['translations']
            if key in translations:
                return translations[key]
        
        # 都没有找到，返回默认值
        return default
    
    def tr(self, key, default=None):
        """translate的简写"""
        return self.translate(key, default)
    
    def get_translations(self, language_code):
        """获取指定语言的所有翻译"""
        if language_code in self.languages:
            return self.languages[language_code]['translations']
        return {}
    
    def get_available_languages(self):
        """获取所有可用语言的代码列表"""
        return list(self.languages.keys())
