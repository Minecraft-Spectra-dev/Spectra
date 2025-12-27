"""管理器模块"""

from .config import ConfigManager
from .language import LanguageManager
from .background import BackgroundManager
from .log_manager import LogManager, get_logger, setup_logging

__all__ = [
    'ConfigManager',
    'LanguageManager',
    'BackgroundManager',
    'LogManager',
    'get_logger',
    'setup_logging'
]
