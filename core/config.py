import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME: str = "澳大利亚新闻简报系统"
    PROJECT_VERSION: str = "1.0.0"
    
    # 数据库配置
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/au_news.db")
    
    # 应用配置
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "t")
    API_PREFIX: str = "/api"
    
    # RSS采集配置
    RSS_COLLECTION_INTERVAL: int = int(os.getenv("RSS_COLLECTION_INTERVAL", "86400"))  # 默认为1天
    
    # 文章处理配置
    ARTICLE_RELEVANCE_THRESHOLD: float = float(os.getenv("ARTICLE_RELEVANCE_THRESHOLD", "0.1"))
    
    # 日志配置
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", f"{BASE_DIR}/logs/au_news.log")

# 创建全局配置对象
settings = Settings() 