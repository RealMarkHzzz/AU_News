import feedparser
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
import logging
from . import models, database

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("rss_collector")

class RSSCollector:
    """RSS源数据采集器"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def fetch_rss_feed(self, source_id: int):
        """获取单个RSS源的数据"""
        # 获取数据源信息
        source = self.db.query(models.RSSSource).filter(models.RSSSource.id == source_id).first()
        
        if not source or not source.is_active:
            logger.warning(f"RSS源 {source_id} 不存在或未激活")
            return {"status": "skipped", "source_id": source_id}
        
        try:
            # 解析RSS feed
            logger.info(f"开始获取RSS源: {source.name} ({source.url})")
            feed = feedparser.parse(source.url)
            new_articles = 0
            
            for entry in feed.entries[:10]:  # 限制为最新的10条
                # 生成唯一标识
                guid = entry.get('id') or entry.get('link')
                guid_hash = hashlib.md5(guid.encode()).hexdigest()
                
                # 检查是否已存在
                existing = self.db.query(models.Article).filter_by(guid=guid).first()
                if existing:
                    continue
                
                # 提取发布日期
                if hasattr(entry, 'published_parsed') and entry.published_parsed:
                    published_date = datetime(*entry.published_parsed[:6])
                else:
                    published_date = datetime.now()
                
                # 提取描述/内容
                content = entry.get('description', '')
                if hasattr(entry, 'content') and entry.content:
                    content = entry.content[0].value
                
                # 创建新文章记录
                article = models.Article(
                    guid=guid,
                    title=entry.title,
                    content=content,
                    source=source.name,
                    url=entry.link,
                    published_at=published_date,
                    language='en',
                    status='pending'
                )
                self.db.add(article)
                logger.info(f"发现新文章: {entry.title}")
                new_articles += 1
            
            # 更新源的最后获取时间
            source.last_fetched = datetime.now()
            source.error_count = 0
            self.db.commit()
            
            return {"status": "success", "source_id": source_id, "new_articles": new_articles}
            
        except Exception as e:
            logger.error(f"获取RSS源 {source.name} 失败: {str(e)}")
            source.error_count += 1
            self.db.commit()
            return {"status": "error", "source_id": source_id, "message": str(e)}
    
    def fetch_all_active_sources(self):
        """获取所有激活的RSS源"""
        sources = self.db.query(models.RSSSource).filter_by(is_active=True).all()
        results = []
        
        for source in sources:
            result = self.fetch_rss_feed(source.id)
            results.append(result)
        
        return results