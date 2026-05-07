import logging
import sys
from typing import Optional
from pathlib import Path
from app.config.server import server_config


class Logger:
    """日志管理类"""
    
    def __init__(self, name: str = "DSMS"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加 handler
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """设置日志处理器"""
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if server_config.settings.debug else logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(console_handler)
        
        # File Handler (optional)
        log_file = Path("logs/app.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
    
    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)
    
    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)
    
    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)
    
    def error(self, message: str, exc_info: bool = False):
        """错误日志"""
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message: str, exc_info: bool = False):
        """严重错误日志"""
        self.logger.critical(message, exc_info=exc_info)


_loggers: dict = {}


def get_logger(name: str = "DSMS") -> Logger:
    """获取日志实例

    Args:
        name: 日志名称

    Returns:
        Logger 实例
    """
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]
