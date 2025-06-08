from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class RSSSource(Base):
    """RSS数据源模型"""
    __tablename__ = "rss_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    last_fetched = Column(DateTime, nullable=True)
    fetch_interval = Column(Integer, default=3600)  # 默认1小时
    is_active = Column(Boolean, default=True)
    error_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.now)


class Article(Base):
    """新闻文章模型"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    guid = Column(String(255), unique=True, nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text)
    summary = Column(Text)
    source = Column(String(100), nullable=False)
    url = Column(Text, nullable=False)
    published_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    sentiment = Column(Float, nullable=True)  # -1.0 to 1.0
    relevance_score = Column(Float, nullable=True)  # 0.0 to 1.0
    language = Column(String(10), default='en')
    status = Column(String(20), default='pending')  # pending, processed, published


class Keyword(Base):
    """关键词模型"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), default="general")
    weight = Column(Float, default=1.0)  # 关键词权重
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)