import requests
import logging
from typing import Dict, List, Any, Optional

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("service_client")

class ServiceClient:
    """服务间通信客户端"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """发送HTTP请求"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        try:
            if method.lower() == 'get':
                response = requests.get(url, params=data)
            elif method.lower() == 'post':
                response = requests.post(url, json=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
                
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"请求失败 ({url}): {str(e)}")
            raise

class ContentAnalysisClient(ServiceClient):
    """内容分析服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        super().__init__(base_url)
    
    def analyze_article(self, article_id: int, title: str, content: str) -> Dict:
        """分析单篇文章"""
        data = {
            "article_id": article_id,
            "title": title,
            "content": content
        }
        return self._make_request('post', '/analyze', data)
    
    def batch_analyze(self, articles: List[Dict]) -> List[Dict]:
        """批量分析文章"""
        return self._make_request('post', '/batch-analyze', articles)

class DataIngestionClient(ServiceClient):
    """数据采集服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        super().__init__(base_url)
    
    def get_articles(self, limit: int = 10) -> List[Dict]:
        """获取最新文章"""
        return self._make_request('get', f'/articles/?limit={limit}')
    
    def update_article(self, article_id: int, data: Dict) -> Dict:
        """更新文章信息"""
        return self._make_request('post', f'/articles/{article_id}/update', data)