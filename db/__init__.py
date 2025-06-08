"""
数据库模块：提供数据库访问和模型定义

此模块包含：
- 数据库连接管理
- 数据模型定义
- 数据访问接口
"""

# 导入所有模型，确保它们被SQLAlchemy发现
from db.database import Base, engine, SessionLocal, get_db, init_db
from db.models import (
    ArticleStatus,
    RssSource,
    Article,
    Keyword,
    ArticleKeyword,
    User
) 