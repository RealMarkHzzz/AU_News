import logging
import time
from typing import List, Dict
from .service_client import ContentAnalysisClient, DataIngestionClient

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("integration_processor")

class IntegrationProcessor:
    """集成处理器，用于协调不同服务之间的工作流"""
    
    def __init__(self):
        self.content_client = ContentAnalysisClient()
        self.data_client = DataIngestionClient()
    
    def process_pending_articles(self, limit: int = 10) -> Dict:
        """处理待分析的文章"""
        try:
            # 获取最新的待处理文章
            articles = self.data_client.get_articles(limit=limit)
            
            if not articles:
                logger.info("没有发现待处理的文章")
                return {"status": "success", "processed": 0}
            
            # 只处理状态为pending的文章
            pending_articles = [a for a in articles if a.get('status') == 'pending']
            
            if not pending_articles:
                logger.info(f"没有发现状态为'pending'的文章")
                return {"status": "success", "processed": 0}
                
            logger.info(f"发现{len(pending_articles)}篇待处理文章")
            
            # 准备批量分析请求
            analysis_requests = []
            for article in pending_articles:
                analysis_requests.append({
                    "article_id": article["id"],
                    "title": article["title"],
                    "content": article.get("content", "")
                })
            
            # 批量分析文章
            analysis_results = self.content_client.batch_analyze(analysis_requests)
            
            # 处理结果
            processed_count = 0
            for i, result in enumerate(analysis_results):
                article_id = pending_articles[i]["id"]
                
                # 准备更新数据
                update_data = {
                    "relevance_score": result["relevance_score"],
                    "sentiment": result["sentiment"],
                    "status": "processed"
                }
                
                # 更新文章信息
                self.data_client.update_article(article_id, update_data)
                processed_count += 1
                
            logger.info(f"成功处理了{processed_count}篇文章")
            return {"status": "success", "processed": processed_count}
            
        except Exception as e:
            logger.error(f"处理文章时出错: {str(e)}")
            return {"status": "error", "message": str(e)}