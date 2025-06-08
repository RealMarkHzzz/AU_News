import logging
import os
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

from .config import settings

# 确保日志目录存在
log_dir = Path(settings.LOG_FILE).parent
log_dir.mkdir(exist_ok=True, parents=True)

# 配置根日志记录器
def setup_logger():
    log_level = getattr(logging, settings.LOG_LEVEL)
    
    # 创建日志格式
    log_format = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # 创建根日志记录器
    logger = logging.getLogger("au_news")
    logger.setLevel(log_level)
    
    # 清除现有的处理器
    if logger.handlers:
        logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = RotatingFileHandler(
        settings.LOG_FILE, 
        maxBytes=10485760,  # 10MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(log_format)
    logger.addHandler(file_handler)
    
    return logger

# 创建默认日志记录器
logger = setup_logger()

def get_logger(name):
    """获取指定名称的日志记录器"""
    return logging.getLogger(f"au_news.{name}") 