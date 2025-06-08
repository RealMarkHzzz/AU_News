import re
from typing import List, Tuple, Dict
from textblob import TextBlob
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("content_analyzer")

# 默认关键词权重
DEFAULT_KEYWORD_WEIGHTS = {
    "chinese students": 3.0,
    "international students": 2.5,
    "adelaide": 2.0,
    "china": 1.5,
    "chinese": 1.5,
    "safety": 2.0,
    "accommodation": 1.5,
    "visa": 2.0,
    "part-time job": 1.5,
    "university": 1.0,
    "education": 1.0,
    "study": 1.0,
    "australia": 0.5,
    "tuition fee": 1.8,
    "immigration": 1.7,
    "discrimination": 2.2,
    "covid": 1.0,
    "mandarin": 1.2,
    "cultural": 1.0,
    "housing": 1.5
}

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self, keyword_weights: Dict[str, float] = None):
        """初始化分析器
        
        Args:
            keyword_weights: 关键词权重字典，如果为None则使用默认值
        """
        self.keyword_weights = keyword_weights or DEFAULT_KEYWORD_WEIGHTS
    
    def calculate_relevance(self, text: str) -> Tuple[float, List[str]]:
        """计算文章相关性得分"""
        text_lower = text.lower()
        matched_keywords = []
        total_score = 0.0
        
        for keyword, weight in self.keyword_weights.items():
            # 使用正则表达式匹配关键词
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = len(re.findall(pattern, text_lower))
            
            if matches > 0:
                matched_keywords.append(keyword)
                total_score += weight * matches
                logger.debug(f"匹配关键词: {keyword}, 出现次数: {matches}, 权重: {weight}")
        
        # 归一化得分 (0-1)
        max_possible_score = sum(self.keyword_weights.values()) * 3  # 假设最多出现3次
        relevance_score = min(total_score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
        
        logger.info(f"相关性得分: {relevance_score:.2f}, 匹配关键词: {', '.join(matched_keywords)}")
        return relevance_score, matched_keywords
    
    def analyze_sentiment(self, text: str) -> float:
        """分析情感倾向"""
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity  # -1 to 1
        
        sentiment_desc = "中性"
        if sentiment > 0.25:
            sentiment_desc = "积极"
        elif sentiment < -0.25:
            sentiment_desc = "消极"
            
        logger.info(f"情感分析: {sentiment:.2f} ({sentiment_desc})")
        return sentiment
    
    def analyze_article(self, title: str, content: str) -> Dict:
        """分析文章内容"""
        full_text = f"{title} {content}"
        
        # 计算相关性
        relevance_score, matched_keywords = self.calculate_relevance(full_text)
        
        # 情感分析
        sentiment = self.analyze_sentiment(full_text)
        
        return {
            "relevance_score": relevance_score,
            "sentiment": sentiment,
            "matched_keywords": matched_keywords
        }