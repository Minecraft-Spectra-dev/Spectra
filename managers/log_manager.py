"""日志管理器 - 统一的日志系统管理"""

import gzip
import logging
import os
import shutil
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


class LogManager:
    """日志管理器，提供统一的日志记录功能"""
    
    _instance: Optional['LogManager'] = None
    _initialized = False
    
    # 日志级别映射
    LOG_LEVELS = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, log_dir: str = "logs", level: str = "INFO"):
        """初始化日志管理器
        
        Args:
            log_dir: 日志文件目录
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        # 如果已经初始化，每次启动时也要执行存档操作
        if self._initialized:
            # 只在初始化完成后才执行，以避免清空新创建的日志文件
            self._archive_old_logs(skip_if_empty=True)
            return
            
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)  # 自动创建目录
        self.level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self.max_backups = 5  # 最多保留5份存档
        self.loggers = {}
        
        # 创建日志格式
        self._setup_formats()
        
        # 存档旧日志文件（首次初始化时）
        self._archive_old_logs(skip_if_empty=True)
        
        # 配置根日志记录器
        self._setup_root_logger()
        
        # 设置类变量
        LogManager._initialized = True
        
    def _setup_formats(self):
        """设置日志格式"""
        # 详细格式（用于文件）
        self.detailed_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 简洁格式（用于控制台）
        self.simple_format = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # 调试格式（用于开发调试）
        self.debug_format = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    def _archive_old_logs(self, skip_if_empty: bool = False):
        """将现有的日志文件压缩存档
        
        Args:
            skip_if_empty: 如果为 True，当日志文件为空时跳过存档
        """
        for log_name in ['info.log', 'debug.log']:
            log_file = self.log_dir / log_name
            
            # 如果日志文件存在
            if log_file.exists():
                file_size = log_file.stat().st_size
                # 如果设置了 skip_if_empty 且文件为空或非常小，跳过
                if skip_if_empty and file_size < 100:  # 小于 100 字节认为是空的
                    continue
                # 如果文件有内容，先压缩存档
                if file_size > 0:
                    # 生成存档文件名: info.log.1.gz, info.log.2.gz, ...
                    self._rotate_and_compress(log_file)
    
    def _rotate_and_compress(self, log_file: Path):
        """轮转并压缩日志文件
        
        Args:
            log_file: 日志文件路径
        """
        if not log_file.exists():
            return
        
        base_name = log_file.name  # info.log 或 debug.log
        
        # 获取现有的所有压缩存档编号
        archive_numbers = sorted([
            int(f.stem.split('.')[-1])
            for f in self.log_dir.glob(f"{base_name}.[0-9].gz")
        ])
        
        # 从大到小依次递增编号
        for num in sorted(archive_numbers, reverse=True):
            old_file = self.log_dir / f"{base_name}.{num}.gz"
            if old_file.exists():
                new_num = num + 1
                new_file = self.log_dir / f"{base_name}.{new_num}.gz"
                old_file.rename(new_file)
        
        # 重新获取存档编号（已经递增）
        new_archive_numbers = sorted([
            int(f.stem.split('.')[-1])
            for f in self.log_dir.glob(f"{base_name}.[0-9].gz")
        ])
        
        # 删除超过上限的存档（编号最大的）
        while len(new_archive_numbers) >= self.max_backups:
            largest_num = max(new_archive_numbers)
            file_to_delete = self.log_dir / f"{base_name}.{largest_num}.gz"
            if file_to_delete.exists():
                file_to_delete.unlink()
                new_archive_numbers.remove(largest_num)
        
        # 压缩当前日志文件为 .1.gz
        archive_file = self.log_dir / f"{base_name}.1.gz"
        self._compress_file(log_file, archive_file)
        
        # 清空原日志文件
        try:
            with open(log_file, 'w', encoding='utf-8') as f:
                f.truncate(0)
        except Exception as e:
            logging.getLogger(__name__).error(f"清空日志文件失败: {e}")
    
    def _compress_file(self, source: Path, target: Path):
        """压缩文件
        
        Args:
            source: 源文件路径
            target: 目标压缩文件路径
        """
        try:
            with open(source, 'rb') as f_in:
                with gzip.open(target, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            logging.getLogger(__name__).info(f"日志已压缩存档: {source.name} -> {target.name}")
        except Exception as e:
            logging.getLogger(__name__).error(f"压缩日志文件失败: {e}")
    
    def _setup_root_logger(self):
        """配置根日志记录器"""
        root_logger = logging.getLogger()
        root_logger.setLevel(self.level)
        
        # 清除现有的处理器
        root_logger.handlers.clear()
        
        # 添加文件处理器
        self._add_file_handlers(root_logger)
        
        # 添加控制台处理器
        self._add_console_handler(root_logger)
        
        # 设置异常处理
        self._setup_exception_handler()
    
    def _add_file_handlers(self, logger: logging.Logger):
        """添加文件处理器
        
        Args:
            logger: 要添加处理器的日志记录器
        """
        # 1. info.log - INFO 级别及以上
        info_log_file = self.log_dir / "info.log"
        info_handler = RotatingFileHandler(
            info_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=0,  # 不使用 RotatingFileHandler 的备份，我们自己管理
            encoding='utf-8'
        )
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(self.detailed_format)
        logger.addHandler(info_handler)
        
        # 2. debug.log - DEBUG 级别及以上（与info.log格式完全一致）
        debug_log_file = self.log_dir / "debug.log"
        debug_handler = RotatingFileHandler(
            debug_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=0,  # 不使用 RotatingFileHandler 的备份，我们自己管理
            encoding='utf-8'
        )
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(self.detailed_format)
        logger.addHandler(debug_handler)
    
    def _add_console_handler(self, logger: logging.Logger):
        """添加控制台处理器
        
        Args:
            logger: 要添加处理器的日志记录器
        """
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(self.level)
        console_handler.setFormatter(self.simple_format)
        logger.addHandler(console_handler)
    
    def _setup_exception_handler(self):
        """设置全局异常处理器"""
        def handle_exception(exc_type, exc_value, exc_traceback):
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_traceback)
                return
            
            # 使用error日志记录器记录异常
            logger = self.get_logger('exception')
            logger.critical(
                "Uncaught exception",
                exc_info=(exc_type, exc_value, exc_traceback)
            )
        
        sys.excepthook = handle_exception
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称，通常使用 __name__
            
        Returns:
            logging.Logger: 配置好的日志记录器
        """
        if name in self.loggers:
            return self.loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(self.level)
        self.loggers[name] = logger
        return logger
    
    def set_level(self, level: str):
        """设置日志级别
        
        Args:
            level: 日志级别字符串 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        new_level = self.LOG_LEVELS.get(level.upper(), logging.INFO)
        self.level = new_level
        
        # 更新所有日志记录器的级别
        for logger in self.loggers.values():
            logger.setLevel(new_level)
        
        # 更新根日志记录器的级别
        root_logger = logging.getLogger()
        root_logger.setLevel(new_level)
        
        # 更新控制台处理器的级别
        for handler in root_logger.handlers:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, RotatingFileHandler):
                handler.setLevel(new_level)
    
    def get_log_files(self) -> list[Path]:
        """获取所有日志文件列表
        
        Returns:
            list[Path]: 日志文件路径列表
        """
        return sorted(self.log_dir.glob("*.log*"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    def get_log_stats(self) -> dict:
        """获取日志统计信息
        
        Returns:
            dict: 包含日志统计信息的字典
        """
        log_files = self.get_log_files()
        total_size = sum(f.stat().st_size for f in log_files)
        
        # 统计存档文件数量
        archive_count = len([f for f in log_files if f.suffix == '.gz'])
        
        return {
            'total_files': len(log_files),
            'total_size': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'log_directory': str(self.log_dir),
            'log_files': [str(f) for f in log_files],
            'archive_count': archive_count
        }


# 便捷函数
def get_logger(name: str) -> logging.Logger:
    """获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称
        
    Returns:
        logging.Logger: 日志记录器
    """
    return LogManager().get_logger(name)


def setup_logging(log_dir: str = "logs", level: str = "INFO") -> LogManager:
    """设置日志系统的便捷函数
    
    Args:
        log_dir: 日志目录
        level: 日志级别
        
    Returns:
        LogManager: 日志管理器实例
    """
    return LogManager(log_dir=log_dir, level=level)
