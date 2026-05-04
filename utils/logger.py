import logging
import sys
from datetime import datetime


class VoxisLogger:
    """Centralized logging for VOXIS"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if VoxisLogger._initialized:
            return
        
        self.logger = logging.getLogger("VOXIS")
        self.logger.setLevel(logging.DEBUG)
        
        # Console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        
        # Formatter
        formatter = logging.Formatter(
            fmt='[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        
        self.logger.addHandler(handler)
        VoxisLogger._initialized = True
    
    def debug(self, msg: str, **kwargs):
        self.logger.debug(msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        self.logger.info(msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.logger.warning(msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self.logger.error(msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.logger.critical(msg, **kwargs)


def get_logger():
    """Get the VOXIS logger instance"""
    return VoxisLogger()
