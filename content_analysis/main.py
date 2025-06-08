from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
from .analyzer import ContentAnalyzer

app = FastAPI(title="内容分析服务")
analyzer = ContentAnalyzer()

class ArticleAnalysisRequest(BaseModel):
    article_id: Optional[int] = None
    title: str
    content: str

class AnalysisResult(BaseModel):
    relevance_score: float
    sentiment: float
    matched_keywords: List[str]

@app.get("/")
def read_root():
    return {"message": "澳大利亚新闻内容分析服务"}

@app.post("/analyze", response_model=AnalysisResult)
def analyze_article(request: ArticleAnalysisRequest):
    """分析单篇文章"""
    try:
        result = analyzer.analyze_article(request.title, request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch-analyze", response_model=List[AnalysisResult])
def batch_analyze(articles: List[ArticleAnalysisRequest]):
    """批量分析文章"""
    try:
        results = []
        for article in articles:
            result = analyzer.analyze_article(article.title, article.content)
            results.append(result)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))