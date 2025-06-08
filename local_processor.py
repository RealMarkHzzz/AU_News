import logging
import time
from sqlalchemy.orm import Session
from typing import Dict, List

from content_analysis.analyzer import ContentAnalyzer
from data_ingestion.database import SessionLocal
from data_ingestion.models import Article, Keyword

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("local_processor")

class LocalProcessor:
    """本地处理器，直接处理数据库中的文章，不通过HTTP请求"""
    
    def __init__(self):
        self.analyzer = None  # 延迟初始化
    
    def get_analyzer(self, db: Session) -> ContentAnalyzer:
        """获取或创建内容分析器，使用数据库中的关键词"""
        if not self.analyzer:
            # 从数据库获取活跃的关键词
            keywords = db.query(Keyword).filter(Keyword.is_active == True).all()
            
            # 创建关键词权重字典
            keyword_weights = {}
            for kw in keywords:
                keyword_weights[kw.word] = kw.weight
            
            # 如果没有关键词，添加一些默认关键词
            if not keyword_weights:
                keyword_weights = {
                    "chinese students": 3.0,
                    "international students": 2.5,
                    "adelaide": 2.0,
                    "安全": 2.0,
                    "留学生": 3.0
                }
            
            # 创建分析器
            self.analyzer = ContentAnalyzer(keyword_weights=keyword_weights)
            logger.info(f"初始化分析器，使用{len(keyword_weights)}个关键词")
        
        return self.analyzer
    
    def process_pending_articles(self, limit: int = 10) -> Dict:
        """处理待分析的文章"""
        try:
            db = SessionLocal()
            
            try:
                # 获取最新的待处理文章
                pending_articles = db.query(Article).filter(Article.status == "pending").limit(limit).all()
                
                if not pending_articles:
                    logger.info("没有发现待处理的文章")
                    return {"status": "success", "processed": 0}
                    
                logger.info(f"发现{len(pending_articles)}篇待处理文章")
                
                # 获取分析器(使用数据库中的关键词)
                analyzer = self.get_analyzer(db)
                
                # 处理文章
                processed_count = 0
                for article in pending_articles:
                    # 分析文章
                    result = analyzer.analyze_article(article.title, article.content or "")
                    
                    # 更新文章信息
                    article.relevance_score = result["relevance_score"]
                    article.sentiment = result["sentiment"]
                    article.status = "processed"
                    
                    processed_count += 1
                
                # 提交所有更改
                db.commit()
                    
                logger.info(f"成功处理了{processed_count}篇文章")
                return {"status": "success", "processed": processed_count}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"处理文章时出错: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def reevaluate_articles(self, limit: int = 500) -> Dict:
        """根据最新关键词重新评估已处理的文章"""
        try:
            db = SessionLocal()
            
            try:
                # 强制初始化一个新的分析器，使用最新的关键词
                self.analyzer = None
                analyzer = self.get_analyzer(db)
                
                # 获取已处理的文章
                processed_articles = db.query(Article).filter(Article.status == "processed").limit(limit).all()
                
                if not processed_articles:
                    logger.info("没有发现已处理的文章")
                    return {"status": "success", "reevaluated": 0}
                    
                logger.info(f"重新评估{len(processed_articles)}篇已处理文章")
                
                # 重新评估文章
                reevaluated_count = 0
                for article in processed_articles:
                    # 分析文章
                    result = analyzer.analyze_article(article.title, article.content or "")
                    
                    # 更新文章信息
                    old_relevance = article.relevance_score
                    old_sentiment = article.sentiment
                    article.relevance_score = result["relevance_score"]
                    article.sentiment = result["sentiment"]
                    
                    # 记录变化
                    if old_relevance != article.relevance_score or old_sentiment != article.sentiment:
                        logger.debug(f"文章#{article.id} 评分变化: 相关性 {old_relevance:.2f} -> {article.relevance_score:.2f}, 情感 {old_sentiment:.2f} -> {article.sentiment:.2f}")
                    
                    reevaluated_count += 1
                
                # 提交所有更改
                db.commit()
                    
                logger.info(f"成功重新评估了{reevaluated_count}篇文章")
                return {"status": "success", "reevaluated": reevaluated_count}
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"重新评估文章时出错: {str(e)}")
            return {"status": "error", "message": str(e)}