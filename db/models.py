import enum
from datetime import datetime
from typing import Optional, List

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship

from db.database import Base


class ArticleStatus(enum.Enum):
    """文章状态枚举"""
    NEW = "new"              # 新采集
    PROCESSED = "processed"  # 已处理
    RELEVANT = "relevant"    # 相关
    IRRELEVANT = "irrelevant"  # 不相关


class RssSource(Base):
    """RSS源表"""
    __tablename__ = "rss_sources"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    last_fetch_at = Column(DateTime, nullable=True)
    
    # 关系
    articles = relationship("Article", back_populates="source")
    
    def __repr__(self):
        return f"<RssSource {self.name}>"


class Article(Base):
    """文章表"""
    __tablename__ = "articles"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False, unique=True)
    content = Column(Text, nullable=True)
    published_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.now)
    processed_at = Column(DateTime, nullable=True)
    status = Column(Enum(ArticleStatus), default=ArticleStatus.NEW)
    relevance_score = Column(Float, default=0.0)
    sentiment_score = Column(Float, nullable=True)
    source_id = Column(Integer, ForeignKey("rss_sources.id"))
    
    # 关系
    source = relationship("RssSource", back_populates="articles")
    keywords = relationship("ArticleKeyword", back_populates="article")
    
    def __repr__(self):
        return f"<Article {self.title[:30]}...>"


class Keyword(Base):
    """关键词表"""
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String(100), nullable=False, unique=True)
    category = Column(String(50), nullable=True)
    weight = Column(Float, default=1.0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    # 关系
    articles = relationship("ArticleKeyword", back_populates="keyword")
    
    def __repr__(self):
        return f"<Keyword {self.word}>"


class ArticleKeyword(Base):
    """文章-关键词关联表"""
    __tablename__ = "article_keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"))
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    count = Column(Integer, default=1)  # 关键词在文章中出现次数
    
    # 关系
    article = relationship("Article", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="articles")
    
    def __repr__(self):
        return f"<ArticleKeyword article_id={self.article_id} keyword_id={self.keyword_id}>"


class User(Base):
    """用户表"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    last_login = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<User {self.username}>" 